from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from clima_db.models import metadata as target_metadata
from sqlalchemy import create_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic manages only these schemas. Everything else (PostGIS's tiger and
# topology schemas, spatial_ref_sys, dbt-owned gold) is invisible to
# autogenerate, so it never proposes dropping what it doesn't own.
MANAGED_SCHEMAS = {"metadata", "silver"}


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def database_url() -> str:
    override = os.getenv("DATABASE_URL")
    if override:
        return override

    user = os.getenv("POSTGRES_USER", "clima")
    password = os.getenv("POSTGRES_PASSWORD", "clima-local-dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "clima")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of executing (alembic upgrade --sql)."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_name=include_name,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url())

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
