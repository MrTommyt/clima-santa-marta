"""Exit-gate test for the Open-Meteo modelled-history transform."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

pytestmark = pytest.mark.integration

FIXTURE = Path(__file__).parent / "fixtures/openmeteo-history-sample.json"


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


def test_idempotent_with_lineage_and_utc(engine):
    from clima_db.models import weather_model_history
    from clima_transforms.openmeteo_history import transform_objects

    data = json.loads(FIXTURE.read_text())
    objects = [(data["object_key"], data["payload"])]

    first = transform_objects(engine, objects, source_id=1, location_ids={"minca": 3})
    second = transform_objects(engine, objects, source_id=1, location_ids={"minca": 3})

    assert first > 0
    assert second == 0

    with engine.connect() as conn:
        total = conn.execute(
            select(func.count()).select_from(weather_model_history)
        ).scalar()
        missing_lineage = conn.execute(
            select(func.count())
            .select_from(weather_model_history)
            .where(weather_model_history.c.raw_record_id.is_(None))
        ).scalar()
        first_valid = conn.execute(
            select(func.min(weather_model_history.c.valid_at))
        ).scalar()

    assert total == first
    assert missing_lineage == 0
    # Local midnight June 1 (UTC-5) must land as 05:00 UTC.
    assert first_valid.isoformat() == "2026-06-01T05:00:00+00:00"
