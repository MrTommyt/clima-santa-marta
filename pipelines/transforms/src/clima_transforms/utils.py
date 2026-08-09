import os

from clima_db.models import location, source
from clima_shared.bronze import MinioBronzeStore
from sqlalchemy import Engine, create_engine, select


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


def source_id_by_code(engine: Engine, code: str) -> int:
    with engine.connect() as conn:
        row = conn.execute(select(source.c.id).where(source.c.code == code)).first()

    if row is None:
        raise ValueError(f"No source with code={code}; seed it first")

    return row.id


def location_id_by_slug(engine: Engine, slug: str) -> int:
    with engine.connect() as conn:
        row = conn.execute(select(location.c.id).where(location.c.slug == slug)).first()

    if row is None:
        raise ValueError(f"No location with slug={slug}; seed it first")

    return row.id
