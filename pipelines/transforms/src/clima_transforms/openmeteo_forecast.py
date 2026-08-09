"""Open-Meteo forecast-run bronze -> silver transform.

Mapping doc: docs/data_dictionary/openmeteo-forecast-field-mapping.md.
Bump PIPELINE_VERSION whenever mapping or assessment logic changes.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from clima_db.models import weather_forecast
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from clima_transforms.assess import assess
from clima_transforms.runs import start_run, update_run
from clima_transforms.utils import (
    build_bronze,
    build_engine,
    location_id_by_slug,
    source_id_by_code,
)

PIPELINE_VERSION = "openmeteo-forecast-0.1.0"

BRONZE_PREFIX = "source=open_meteo/dataset=forecast/"

FORECAST_MODEL = "best_match"

KMH_TO_MS = 1 / 3.6

# source hourly field -> (canonical variable, canonical unit, factor)
VARIABLES = {
    "temperature_2m": ("air_temperature_2m", "degC", 1.0),
    "dew_point_2m": ("dew_point_2m", "degC", 1.0),
    "relative_humidity_2m": ("relative_humidity_2m", "%", 1.0),
    "apparent_temperature": ("apparent_temperature", "degC", 1.0),
    "precipitation": ("precipitation", "mm", 1.0),
    "precipitation_probability": ("precipitation_probability", "%", 1.0),
    "surface_pressure": ("surface_pressure", "hPa", 1.0),
    "cloud_cover": ("cloud_cover", "%", 1.0),
    "wind_speed_10m": ("wind_speed_10m", "m/s", KMH_TO_MS),
    "wind_direction_10m": ("wind_direction_10m", "deg", 1.0),
    "wind_gusts_10m": ("wind_gust_10m", "m/s", KMH_TO_MS),
}

# .../location=<slug>/year=YYYY/month=MM/day=DD/HHMMZ-<hash>.json.gz
KEY_PATTERN = re.compile(
    r"location=(?P<slug>[^/]+)/year=(?P<y>\d{4})/month=(?P<m>\d{2})/day=(?P<d>\d{2})/"
    r"(?P<hh>\d{2})(?P<min>\d{2})Z-"
)


def issuance_from_key(object_key: str) -> tuple[str, datetime]:
    """The capture bucket in the object key is the forecast issuance time."""
    match = KEY_PATTERN.search(object_key)

    if match is None:
        raise ValueError(f"Not a forecast capture key: {object_key}")

    generated_at = datetime(
        int(match["y"]),
        int(match["m"]),
        int(match["d"]),
        int(match["hh"]),
        int(match["min"]),
        tzinfo=UTC,
    )

    return match["slug"], generated_at


def parse_payload(
    payload: dict[str, Any],
    *,
    location_id: int,
    source_id: int,
    generated_at: datetime,
    raw_record_id: str,
) -> list[dict[str, Any]]:
    hourly = payload["hourly"]

    # Times in the payload are local and naive; the payload says its offset.
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
                    "forecast_generated_at": generated_at,
                    "forecast_valid_at": valid_at,
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
    """Append-only: the six-column grain makes replays skip, never overwrite."""
    if not rows:
        return 0

    chunk_size = 5000
    if len(rows) > chunk_size:
        return sum(
            upsert_rows(engine, rows[i : i + chunk_size])
            for i in range(0, len(rows), chunk_size)
        )

    statement = (
        insert(weather_forecast)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=[
                "location_id",
                "variable",
                "forecast_valid_at",
                "forecast_generated_at",
                "source_id",
                "forecast_model",
            ],
        )
        .returning(weather_forecast.c.id)
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
    """Pure-ish core, separated from MinIO so tests can feed fixtures."""
    rows: list[dict[str, Any]] = []

    for object_key, payload in objects:
        slug, generated_at = issuance_from_key(object_key)
        rows.extend(
            parse_payload(
                payload,
                location_id=location_ids[slug],
                source_id=source_id,
                generated_at=generated_at,
                raw_record_id=object_key,
            )
        )

    return upsert_rows(engine, rows)


def run(window_hours: int = 48) -> int:
    engine = build_engine()
    bronze = build_bronze()

    end = datetime.now(UTC)
    since = end - timedelta(hours=window_hours)

    source_id = source_id_by_code(engine, "open_meteo")
    run_id = start_run(
        engine,
        dataset="forecast",
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

        slugs = {issuance_from_key(key)[0] for key in keys}
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
