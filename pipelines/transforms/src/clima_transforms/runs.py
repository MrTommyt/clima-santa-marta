from datetime import datetime

from clima_db.models import ingestion_run
from sqlalchemy import func, insert, update


def start_run(
    engine,
    *,
    source_id: int,
    dataset: str,
    window_start: datetime | None,
    window_end: datetime,
):
    statement = (
        insert(ingestion_run)
        .values(
            source_id=source_id,
            dataset=dataset,
            window_start=window_start,
            window_end=window_end,
            started_at=func.now(),
            status="running",
        )
        .returning(ingestion_run.c.id)
    )
    with engine.begin() as conn:
        return conn.execute(statement).scalar_one()


def update_run(engine, run_id: int, *, status: str, records_upserted: int):
    statement = (
        update(ingestion_run)
        .where(ingestion_run.c.id == run_id)
        .values(
            finished_at=func.now(), status=status, records_upserted=records_upserted
        )
    )
    with engine.begin() as conn:
        return conn.execute(statement)
