"""Table definitions for the operational schema.

Define tables on this `metadata` object so Alembic autogenerate can diff them
against the live database. Workflow: edit models here, then
`make migration m="describe change"`, review the generated revision by hand,
then `make migrate`.

Notes for authoring:
- Set `schema="metadata"` or `schema="silver"` on each Table/model; Postgres
  schemas themselves are NOT created by autogenerate: the first migration
  touching a schema needs an explicit
  `op.execute('CREATE SCHEMA IF NOT EXISTS ...')`.
- The naming convention below gives every constraint and index a
  deterministic name; never pass explicit names unless overriding on purpose.
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    func,
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Worked example: the simplest table, showing the Core Table syntax the rest
# follow. One row per upstream provider (open_meteo, metar, ideam, nasa_power).
source = Table(
    "source",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", Text, nullable=False, unique=True),
    Column("name", Text, nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    schema="metadata",
)

location = Table(
    "location",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("slug", Text, nullable=False, unique=True),
    Column("name", Text),
    Column("latitude", Double, nullable=False),
    Column("longitude", Double, nullable=False),
    Column("elevation_m", Double, nullable=False),
    schema="metadata",
)

station = Table(
    "station",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("location_id", Integer, ForeignKey("metadata.location.id"), nullable=False),
    Column("wigos_id", Text, nullable=True),
    Column("icao_code", Text, nullable=True),
    Column("ideam_code", Text, nullable=True),
    schema="metadata",
)

ingestion_run = Table(
    "ingestion_run",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", Integer, ForeignKey("metadata.source.id"), nullable=False),
    Column("dataset", Text, nullable=False),
    Column("window_start", DateTime(timezone=True)),
    Column("window_end", DateTime(timezone=True)),
    Column("started_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
    Column("status", Text, nullable=False),
    Column("records_upserted", Integer),
    schema="metadata",
)

# weather_observation = Table("weather_observation", metadata, ...,
#                             schema="silver")
#   The long table from ADR-0006. Columns: id (BigInteger PK), station_id (FK),
#   source_id (FK), variable (Text), value (Float/Numeric: your call),
#   unit (Text, canonical), observed_at (DateTime(timezone=True)),
#   ingested_at (DateTime(timezone=True)), quality_status (Text),
#   raw_record_id (Text: the bronze object key), pipeline_version (Text).
#   Constraints, passed after the columns:
#     sa.UniqueConstraint("station_id", "variable", "observed_at", "source_id")
#       -> the ADR-0006 grain; this is what makes upserts idempotent.
#     sa.CheckConstraint(
#         "quality_status IN ('valid','suspicious','invalid','missing')",
#         name="quality_status_values")
#       -> autogenerate may miss CHECKs: verify it appears in the draft.
#     sa.Index(None, "station_id", "variable", "observed_at")
#       -> query pattern for time-series reads; None lets the naming
#          convention name it.
weather_observation = Table(
    "weather_observation",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("station_id", Integer, ForeignKey("metadata.station.id"), nullable=False),
    Column("source_id", Integer, ForeignKey("metadata.source.id"), nullable=False),
    Column("unit", Text, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("quality_status", Text, nullable=False),
    Column("raw_record_id", Text, nullable=False),
    Column("pipeline_version", Text, nullable=False),
    Column("variable", Text, nullable=False),
    Column("value", Double, nullable=False),
    UniqueConstraint("station_id", "variable", "observed_at", "source_id"),
    CheckConstraint(
        "quality_status IN ('valid', 'suspicious', 'invalid')",
        name="quality_status_values",
    ),
    Index(None, "station_id", "variable", "observed_at"),
    schema="silver",
)
