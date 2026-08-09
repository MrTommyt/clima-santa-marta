"""Open-Meteo modelled-history bronze -> silver transform.

Mapping doc: docs/data_dictionary/openmeteo-history-field-mapping.md.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from clima_db.models import weather_model_history
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from clima_transforms.assess import assess
from clima_transforms.openmeteo_forecast import FORECAST_MODEL, VARIABLES
from clima_transforms.runs import start_run, update_run
from clima_transforms.utils import (
    build_bronze,
    build_engine,
    location_id_by_slug,
    source_id_by_code,
)

PIPELINE_VERSION = "openmeteo-history-0.1.0"

BRONZE_PREFIX = "source=open_meteo/dataset=historical_forecast/"

SLUG_PATTERN = re.compile(r"location=(?P<slug>[^/]+)/")


def slug_from_key(object_key: str) -> str:
    match = SLUG_PATTERN.search(object_key)

    if match is None:
        raise ValueError(f"No location in bronze key: {object_key}")

    return match["slug"]


def parse_payload(
    payload: dict[str, Any],
    *,
    location_id: int,
    source_id: int,
    raw_record_id: str,
) -> list[dict[str, Any]]:
    hourly = payload["hourly"]
    offset = timezone(timedelta(seconds=payload["utc_offset_seconds"]))

    rows: list[dict[str, Any]] = []

    for index, local_time in enumerate(hourly["time"]):
        valid_at = datetime.fromisoformat(local_time).replace(tzinfo=offset)

        for source_field, (variable, unit, factor) in VARIABLES.items():
            values = hourly.get(source_field)

            if values is None or values[index] is None:
                continue

            value = float(values[index]) * factor

            rows.append(
                {
                    "location_id": location_id,
                    "source_id": source_id,
                    "forecast_model": FORECAST_MODEL,
                    "valid_at": valid_at,
                    "variable": variable,
                    "value": value,
                    "unit": unit,
                    "quality_status": assess(variable, value),
                    "raw_record_id": raw_record_id,
                    "pipeline_version": PIPELINE_VERSION,
                }
            )

    return rows


def upsert_rows(engine: Engine, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    chunk_size = 5000
    if len(rows) > chunk_size:
        return sum(
            upsert_rows(engine, rows[i : i + chunk_size])
            for i in range(0, len(rows), chunk_size)
        )

    statement = (
        insert(weather_model_history)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=[
                "location_id",
                "variable",
                "valid_at",
                "source_id",
                "forecast_model",
            ],
        )
        .returning(weather_model_history.c.id)
    )

    with engine.begin() as conn:
        return len(conn.execute(statement).fetchall())


def transform_objects(
    engine: Engine,
    objects: list[tuple[str, dict[str, Any]]],
    *,
    source_id: int,
    location_ids: dict[str, int],
) -> int:
    rows: list[dict[str, Any]] = []

    for object_key, payload in objects:
        rows.extend(
            parse_payload(
                payload,
                location_id=location_ids[slug_from_key(object_key)],
                source_id=source_id,
                raw_record_id=object_key,
            )
        )

    return upsert_rows(engine, rows)


def run(window_hours: int | None = 48) -> int:
    """window_hours=None reprocesses all of history (initial load, rebuilds)."""
    engine = build_engine()
    bronze = build_bronze()

    end = datetime.now(UTC)
    since = None if window_hours is None else end - timedelta(hours=window_hours)

    source_id = source_id_by_code(engine, "open_meteo")
    run_id = start_run(
        engine,
        dataset="historical_forecast",
        source_id=source_id,
        window_start=since,
        window_end=end,
    )

    inserted = 0
    status = "failed"
    keys: list[str] = []
    try:
        keys = bronze.list_keys(BRONZE_PREFIX, modified_since=since)

        objects = [(key, bronze.read_json(key)) for key in keys]

        slugs = {slug_from_key(key) for key in keys}
        location_ids = {slug: location_id_by_slug(engine, slug) for slug in slugs}

        inserted = transform_objects(
            engine,
            objects,
            source_id=source_id,
            location_ids=location_ids,
        )
        status = "finished"
    finally:
        update_run(engine, run_id, status=status, records_upserted=inserted)

    print(f"Snapshots read: {len(keys)}; new rows inserted: {inserted}")
    return inserted
