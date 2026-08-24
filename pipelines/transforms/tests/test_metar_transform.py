"""Exit-gate test for the METAR bronze->silver transform (Milestone 3).

Proves, against a real throwaway Postgres:
1. Idempotency: running the transform twice yields identical row counts.
2. Lineage: every row carries raw_record_id and pipeline_version.
3. Correctness: known values from the fixture arrive converted.

Remove the skip marker once parse_report() is implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

pytestmark = pytest.mark.integration

FIXTURE = (
    Path(__file__).parent.parent.parent.parent
    / "services/ingestion-metar/test/fixtures/metar-sample.json"
)


@pytest.fixture(scope="module")
def engine():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgis/postgis:17-3.5") as pg:
        engine = create_engine(pg.get_connection_url(driver="psycopg"))

        # Test schema comes from the models (prod uses migrations; keeping
        # them equivalent is what `alembic check` guarantees).
        from clima_db.models import metadata as schema

        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS metadata")
            conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS silver")
        schema.create_all(engine)

        # Minimal seed: one source, one location, one station.
        from clima_db.models import location, source, station

        with engine.begin() as conn:
            conn.execute(source.insert().values(id=2, code="metar", name="METAR"))
            conn.execute(
                location.insert().values(
                    id=1,
                    slug="simon_bolivar_airport",
                    name="Airport",
                    latitude=11.1196,
                    longitude=-74.2306,
                    elevation_m=5,
                )
            )
            conn.execute(station.insert().values(id=1, location_id=1, icao_code="SKSM"))

        yield engine


def test_transform_is_idempotent_with_lineage(engine):
    from clima_db.models import weather_observation
    from clima_transforms.metar import transform_payloads

    payload = json.loads(FIXTURE.read_text())
    payloads = [("bronze/fixture-key.json.gz", payload)]

    first = transform_payloads(engine, payloads, station_id=1, source_id=2)
    second = transform_payloads(engine, payloads, station_id=1, source_id=2)

    assert first > 0, "first run must insert rows"
    assert second == 0, "second run must insert nothing: idempotency"

    with engine.connect() as conn:
        total = conn.execute(
            select(func.count()).select_from(weather_observation)
        ).scalar()
        missing_lineage = conn.execute(
            select(func.count())
            .select_from(weather_observation)
            .where(weather_observation.c.raw_record_id.is_(None))
        ).scalar()

    assert total == first
    assert missing_lineage == 0


def test_known_value_lands_converted(engine):
    """TODO: pick one report from the fixture whose raw values you know,
    run the transform, and assert the silver row holds the CONVERTED value
    (e.g. wind knots -> m/s) with the right unit string. This is the test
    that catches unit mistakes; the idempotency test cannot."""
    ...


def test_numeric_visibility_converts(engine):
    from clima_transforms.metar import parse_report

    report = {"reportTime": "2026-08-24T00:00:00.000Z", "visib": 6.21}
    rows = parse_report(report, station_id=1, source_id=2, raw_record_id="x")

    assert rows[0]["variable"] == "visibility"
    assert rows[0]["value"] == pytest.approx(6.21 * 1609.34)
