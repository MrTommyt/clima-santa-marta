"""METAR bronze -> silver transform.

Structure (written): windowing, station lookup, upsert, orchestration.
Content (YOURS, marked TODO): parse_report(), following the mapping doc at
docs/data_dictionary/metar-field-mapping.md. Keep code and doc in agreement.

Bump PIPELINE_VERSION whenever mapping or assessment logic changes: it is
part of every row's lineage.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from clima_db.models import source, station, weather_observation
from clima_shared.bronze import MinioBronzeStore
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.dialects.postgresql import insert

from clima_transforms.assess import assess
from clima_transforms.runs import start_run, update_run

PIPELINE_VERSION = "metar-0.1.0"

BRONZE_PREFIX = "source=metar/dataset=observations/"


def build_engine() -> Engine:
    user = os.getenv("POSTGRES_USER", "clima")
    password = os.getenv("POSTGRES_PASSWORD", "clima-local-dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "clima")
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}")


def build_bronze() -> MinioBronzeStore:
    return MinioBronzeStore(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        bucket=os.getenv("MINIO_BRONZE_BUCKET", "bronze"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


def station_id_by_icao(engine: Engine, icao: str) -> int:
    with engine.connect() as conn:
        row = conn.execute(
            select(station.c.id).where(station.c.icao_code == icao)
        ).first()

    if row is None:
        raise ValueError(f"No station with icao_code={icao}; seed it first")

    return row.id


def source_id_by_code(engine: Engine, code: str) -> int:
    with engine.connect() as conn:
        row = conn.execute(select(source.c.id).where(source.c.code == code)).first()

    if row is None:
        raise ValueError(f"No source with code={code}; seed it first")

    return row.id


def parse_report(
    report: dict[str, Any],
    *,
    station_id: int,
    source_id: int,
    raw_record_id: str,
) -> list[dict[str, Any]]:
    """Turn ONE report from the payload into silver rows (one per variable).

    TODO(you): implement per the mapping doc. The temperature example below
    shows the complete pattern for one variable: extraction, absence
    handling, conversion (none here), assessment, and row shape. Every other
    mapped field follows it.
    """
    rows: list[dict[str, Any]] = []
    observed_at = datetime.fromisoformat(report["reportTime"])

    def knot_to_ms(x):
        return x * 0.514444

    def conv_visib(x: str):
        if x.endswith("+"):
            return 10000.0
        return float(x) * 1609.34

    cover_mapping = {"CLR": 0.0, "FEW": 18.75, "SCT": 43.75, "BKN": 75.0, "OVC": 100.0}

    def parse_cover(x: str):
        return cover_mapping.get(x)

    def parse_direction(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    def append_row(canonical_var, source_field, unit, conv=lambda x: x):
        value = report.get(source_field)
        if value is None:
            return

        value = conv(value)
        if value is None:
            return

        rows.append(
            {
                "station_id": station_id,
                "source_id": source_id,
                "variable": canonical_var,
                "value": float(value),
                "unit": unit,
                "observed_at": observed_at,
                "quality_status": assess(canonical_var, float(value)),
                "raw_record_id": raw_record_id,
                "pipeline_version": PIPELINE_VERSION,
            }
        )

    append_row("air_temperature_2m", "temp", "degC")
    append_row("dew_point_2m", "dewp", "degC")
    append_row("wind_speed_10m", "wspd", "m/s", knot_to_ms)
    append_row("wind_direction_10m", "wdir", "deg", parse_direction)
    append_row("wind_gust_10m", "wgst", "m/s", knot_to_ms)
    append_row("surface_pressure", "altim", "hPa")
    append_row("visibility", "visib", "m", conv_visib)
    append_row("cloud_cover", "cover", "%", parse_cover)

    return rows


def upsert_rows(engine: Engine, rows: list[dict[str, Any]]) -> int:
    """Idempotent insert: the ADR-0006 unique constraint absorbs replays.
    Returns how many rows were actually new."""
    if not rows:
        return 0

    # Postgres caps one statement at 65535 bind parameters; chunk well below.
    chunk_size = 5000
    if len(rows) > chunk_size:
        return sum(
            upsert_rows(engine, rows[i : i + chunk_size])
            for i in range(0, len(rows), chunk_size)
        )

    statement = (
        insert(weather_observation)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=["station_id", "variable", "observed_at", "source_id"],
        )
        # DO NOTHING + RETURNING yields only the rows actually inserted, which
        # sidesteps the driver's undetermined (-1) rowcount on multi-VALUES.
        .returning(weather_observation.c.id)
    )

    with engine.begin() as conn:
        inserted = len(conn.execute(statement).fetchall())

    return inserted


def transform_payloads(
    engine: Engine,
    payloads: list[tuple[str, Any]],
    *,
    station_id: int,
    source_id: int,
) -> int:
    """Pure-ish core, separated from MinIO so tests can feed fixtures."""
    # Overlapping snapshots repeat the same reports; dedup on the silver
    # grain before inserting. Dict keeps the FIRST occurrence, which matches
    # the first-seen lineage decision (keys arrive in sorted capture order).
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}

    for object_key, payload in payloads:
        for report in payload:
            for row in parse_report(
                report,
                station_id=station_id,
                source_id=source_id,
                raw_record_id=object_key,
            ):
                key = (
                    row["station_id"],
                    row["variable"],
                    row["observed_at"],
                    row["source_id"],
                )
                unique.setdefault(key, row)

    return upsert_rows(engine, list(unique.values()))


def run(window_hours: int = 24) -> int:
    """Entry point for the Airflow task: reprocess every snapshot stored in
    the window. Overlap is free: the constraint deduplicates."""
    engine = build_engine()
    bronze = build_bronze()

    end = datetime.now(UTC)
    since = end - timedelta(hours=window_hours)

    source_id = source_id_by_code(engine, "metar")
    run_id = start_run(
        engine,
        dataset="observations",
        source_id=source_id,
        window_start=since,
        window_end=end,
    )

    inserted = 0
    status = "failed"
    try:
        keys = bronze.list_keys(BRONZE_PREFIX, modified_since=since)

        payloads = [(key, bronze.read_json(key)) for key in keys]

        sksm_station_id = station_id_by_icao(engine, "SKSM")
        inserted = transform_payloads(
            engine,
            payloads,
            station_id=sksm_station_id,
            source_id=source_id,
        )
        status = "finished"
    finally:
        update_run(engine, run_id, status=status, records_upserted=inserted)

    print(f"Snapshots read: {len(keys)}; new rows inserted: {inserted}")
    return inserted
