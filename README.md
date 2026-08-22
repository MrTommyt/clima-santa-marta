# Clima Santa Marta

<!-- TODO: one-paragraph pitch — what this platform does and for whom. -->

A production-style climate data and ML platform for Santa Marta, Colombia. Ingests
weather, marine, and air-quality data from Open-Meteo, IDEAM, SKSM airport METAR, and
NASA POWER; processes it through a bronze/silver/gold lakehouse; and serves it via a
public API and website.

## Quickstart

Requires: [uv](https://docs.astral.sh/uv/), Docker with Compose, GNU Make.

```bash
git clone <repo-url> && cd clima-santa-marta
make setup   # .env, Python workspace, pre-commit hooks
make dev     # start the local platform (Postgres/PostGIS, MinIO, Kafka, Airflow, MLflow, Redis)
make test    # run the unit test suite
```

Run `make help` for all targets. Local UIs once `make dev` is up:

| Service | URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8081 |
| MinIO console | http://localhost:9001 |
| API (run `make api`) | http://localhost:8000/docs |

## Repository layout

| Path | Purpose |
| --- | --- |
| `apps/api` | FastAPI backend |
| `apps/web` | Next.js public site (Milestone 9) |
| `services/ingestion-*` | One isolated ingestion service per data source |
| `pipelines/` | Airflow DAGs, Spark jobs, shared Python library |
| `analytics/dbt` | dbt Core analytical models |
| `ml/` | Notebooks, features, training, evaluation, serving |
| `contracts/` | JSON Schema event and data contracts |
| `infrastructure/` | Terraform, Railway config, local Dockerfiles |
| `observability/` | Grafana, Prometheus, OpenTelemetry config |
| `tests/` | Integration, data-quality, and end-to-end tests |
| `docs/` | Architecture, ADRs, data dictionary, methodology |

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Product requirements](docs/architecture/prd.md)
- [Architecture decision records](docs/adr/)
- [Data-source matrix](docs/data_dictionary/data-source-matrix.md)
- [AI usage policy](docs/ai-usage-policy.md)

## Deployment

The collection pipeline runs on Railway (project `clima-santa-marta`, environment
`production`): PostGIS, an S3-compatible bucket for bronze, and one Airflow service
built from `infrastructure/railway/airflow/Dockerfile`. Pushes to `main` that touch
pipelines, services, db, dbt or config rebuild it (see `railway.json`). The local
compose stack remains the development environment; its DAGs are paused so only
Railway collects. To analyze production data from this machine:

```bash
make explore ENV_FILE=.env.railway   # .env.railway is gitignored; see docs/architecture/overview.md
```

## Status

Milestone 4: matplotlib dashboards on the data. Collection runs unattended on Railway.
