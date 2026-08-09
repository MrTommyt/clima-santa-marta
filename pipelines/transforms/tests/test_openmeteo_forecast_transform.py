"""Exit-gate test for the Open-Meteo forecast transform.

Proves idempotency (run twice, second inserts nothing), lineage, the
generated_at handoff from the object key, and the km/h -> m/s conversion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

pytestmark = pytest.mark.integration

FIXTURE = Path(__file__).parent / "fixtures/openmeteo-forecast-sample.json"


@pytest.fixture(scope="module")
def engine():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgis/postgis:17-3.5") as pg:
        engine = create_engine(pg.get_connection_url(driver="psycopg"))

        from clima_db.models import metadata as schema

        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS metadata")
            conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS silver")
        schema.create_all(engine)

        from clima_db.models import location, source

        with engine.begin() as conn:
            conn.execute(source.insert().values(id=1, code="open_meteo", name="OM"))
            conn.execute(
                location.insert().values(
                    id=3,
                    slug="minca",
                    name="Minca",
                    latitude=11.1436,
                    longitude=-74.1178,
                    elevation_m=650,
                )
            )

        yield engine


def load_fixture():
    data = json.loads(FIXTURE.read_text())
    return data["object_key"], data["payload"]


def test_idempotent_with_issuance_and_lineage(engine):
    from clima_db.models import weather_forecast
    from clima_transforms.openmeteo_forecast import transform_objects

    object_key, payload = load_fixture()
    objects = [(object_key, payload)]

    first = transform_objects(engine, objects, source_id=1, location_ids={"minca": 3})
    second = transform_objects(engine, objects, source_id=1, location_ids={"minca": 3})

    assert first > 0
    assert second == 0

    with engine.connect() as conn:
        total = conn.execute(
            select(func.count()).select_from(weather_forecast)
        ).scalar()
        generated = (
            conn.execute(select(weather_forecast.c.forecast_generated_at).distinct())
            .scalars()
            .all()
        )
        missing_lineage = conn.execute(
            select(func.count())
            .select_from(weather_forecast)
            .where(weather_forecast.c.raw_record_id.is_(None))
        ).scalar()

    assert total == first
    assert missing_lineage == 0
    # The 0400Z bucket in the fixture key must be every row's issuance time.
    assert generated == [datetime(2026, 8, 7, 4, 0, tzinfo=UTC)]


def test_wind_speed_lands_in_ms(engine):
    from clima_db.models import weather_forecast
    from clima_transforms.openmeteo_forecast import transform_objects

    object_key, payload = load_fixture()
    transform_objects(
        engine, [(object_key, payload)], source_id=1, location_ids={"minca": 3}
    )

    raw_kmh = payload["hourly"]["wind_speed_10m"][0]
    first_valid = payload["hourly"]["time"][0]

    with engine.connect() as conn:
        row = conn.execute(
            select(weather_forecast.c.value, weather_forecast.c.unit)
            .where(weather_forecast.c.variable == "wind_speed_10m")
            .order_by(weather_forecast.c.forecast_valid_at)
            .limit(1)
        ).first()

    assert row is not None, f"no wind row for first hour {first_valid}"
    assert row.unit == "m/s"
    assert row.value == pytest.approx(raw_kmh / 3.6)
