from fastapi import FastAPI

app = FastAPI(title="Clima Santa Marta API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up and serving requests."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness: dependencies are reachable.

    TODO: check PostgreSQL and Redis connectivity once the API uses them
    (Milestone 8); until then readiness equals liveness.
    """
    return {"status": "ready"}
