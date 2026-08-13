from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine


def engine() -> Engine:
    user = os.getenv("POSTGRES_USER", "clima")
    password = os.getenv("POSTGRES_PASSWORD", "clima-local-dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "clima")
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}")
