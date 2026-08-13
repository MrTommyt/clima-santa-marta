"""Loaders for the warehouse, one per table worth exploring.

All loaders return long-format DataFrames with timezone-aware timestamps;
`wide()` pivots to one column per variable when a chart wants that shape.
Filters accept None to mean "everything".
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import Engine, text

from clima_ml.db import engine as default_engine

Filter = Sequence[str] | None
Moment = datetime | str | None


def _read(
    base_sql: str,
    clauses: list[str],
    params: dict[str, Any],
    order_by: str,
    db: Engine | None,
    parse_dates: Sequence[str] = (),
) -> pd.DataFrame:
    sql = base_sql
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY {order_by}"

    frame = pd.read_sql(text(sql), db or default_engine(), params=params)
    for column in parse_dates:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


def observations(
    variables: Filter = None,
    stations: Filter = None,
    start: Moment = None,
    end: Moment = None,
    quality: Sequence[str] = ("valid",),
    db: Engine | None = None,
) -> pd.DataFrame:
    base = """
        SELECT
            st.icao_code AS station,
            l.slug AS location,
            o.variable,
            o.value,
            o.unit,
            o.observed_at,
            o.quality_status
        FROM silver.weather_observation AS o
        JOIN metadata.station AS st ON st.id = o.station_id
        JOIN metadata.location AS l ON l.id = st.location_id
    """
    clauses = ["o.quality_status = ANY(:quality)"]
    params: dict[str, Any] = {"quality": list(quality)}
    if variables:
        clauses.append("o.variable = ANY(:variables)")
        params["variables"] = list(variables)
    if stations:
        clauses.append("st.icao_code = ANY(:stations)")
        params["stations"] = list(stations)
    if start:
        clauses.append("o.observed_at >= :start")
        params["start"] = start
    if end:
        clauses.append("o.observed_at < :end")
        params["end"] = end

    return _read(base, clauses, params, "o.observed_at", db, ["observed_at"])


def model_history(
    variables: Filter = None,
    locations: Filter = None,
    start: Moment = None,
    end: Moment = None,
    db: Engine | None = None,
) -> pd.DataFrame:
    base = """
        SELECT
            l.slug AS location,
            h.variable,
            h.value,
            h.unit,
            h.valid_at
        FROM silver.weather_model_history AS h
        JOIN metadata.location AS l ON l.id = h.location_id
    """
    clauses = ["h.quality_status = 'valid'"]
    params: dict[str, Any] = {}
    if variables:
        clauses.append("h.variable = ANY(:variables)")
        params["variables"] = list(variables)
    if locations:
        clauses.append("l.slug = ANY(:locations)")
        params["locations"] = list(locations)
    if start:
        clauses.append("h.valid_at >= :start")
        params["start"] = start
    if end:
        clauses.append("h.valid_at < :end")
        params["end"] = end

    return _read(base, clauses, params, "h.valid_at", db, ["valid_at"])


def forecasts(
    variables: Filter = None,
    locations: Filter = None,
    min_horizon: int | None = None,
    max_horizon: int | None = None,
    db: Engine | None = None,
) -> pd.DataFrame:
    base = """
        SELECT
            l.slug AS location,
            f.forecast_model,
            f.forecast_generated_at,
            f.forecast_valid_at,
            f.variable,
            f.value,
            f.unit
        FROM silver.weather_forecast AS f
        JOIN metadata.location AS l ON l.id = f.location_id
    """
    clauses = ["f.quality_status = 'valid'"]
    params: dict[str, Any] = {}
    if variables:
        clauses.append("f.variable = ANY(:variables)")
        params["variables"] = list(variables)
    if locations:
        clauses.append("l.slug = ANY(:locations)")
        params["locations"] = list(locations)

    frame = _read(
        base,
        clauses,
        params,
        "f.forecast_generated_at, f.forecast_valid_at",
        db,
        ["forecast_generated_at", "forecast_valid_at"],
    )
    horizon = frame["forecast_valid_at"] - frame["forecast_generated_at"]
    frame["horizon_hours"] = (horizon.dt.total_seconds() / 3600).astype(int)
    if min_horizon is not None:
        frame = frame[frame["horizon_hours"] >= min_horizon]
    if max_horizon is not None:
        frame = frame[frame["horizon_hours"] <= max_horizon]
    return frame.reset_index(drop=True)


def verification(
    variables: Filter = None,
    db: Engine | None = None,
) -> pd.DataFrame:
    base = "SELECT * FROM gold.forecast_verification"
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if variables:
        clauses.append("variable = ANY(:variables)")
        params["variables"] = list(variables)

    return _read(
        base,
        clauses,
        params,
        "forecast_valid_at",
        db,
        ["forecast_generated_at", "forecast_valid_at"],
    )


def daily_summary(db: Engine | None = None) -> pd.DataFrame:
    frame = pd.read_sql(
        text("SELECT * FROM gold.daily_summary ORDER BY day"),
        db or default_engine(),
    )
    frame["day"] = pd.to_datetime(frame["day"])
    return frame


def wide(frame: pd.DataFrame, time_column: str = "observed_at") -> pd.DataFrame:
    """Pivot a long loader result to one column per variable."""
    index = [c for c in ("station", "location", time_column) if c in frame.columns]
    return (
        frame.pivot_table(index=index, columns="variable", values="value")
        .reset_index()
        .rename_axis(columns=None)
    )
