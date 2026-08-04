# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Santa Marta Climate Intelligence Platform** — a production-style data and ML platform serving current conditions, forecasts, marine conditions, air quality, heat/rain risk indicators, historical climate exploration, and forecast-verification metrics for Santa Marta, Colombia. Data sources: Open-Meteo (forecast, historical, marine, air quality), IDEAM stations (Datos Abiertos Colombia), SKSM airport METAR, NASA POWER.

The repository is currently in early stages; sections below describe the target design that all work must follow.

## The central rule: division of labor

**The user builds the data intelligence. Claude builds/scaffolds delivery machinery.**

Claude is **encouraged** to do: frontend scaffolding and React components, CSS/responsive layouts, Docker/CI boilerplate, Terraform module scaffolding, Makefile commands, documentation formatting, test fixtures, mock API payloads, routine serialization, accessibility review, debugging environment issues, and code review of the user's completed implementations.

Claude may do **with verification** (must pass format → validation → plan → security scan → staging → smoke tests for infra changes): Terraform changes, DB migrations, security/Kafka configuration, performance optimization, unit tests, dependency upgrades.

Claude must **not** do the core data-science work: choosing analytical questions, defining transformations, data-cleaning decisions, exploratory analysis, interpreting visualizations, choosing statistical tests, designing target variables, feature engineering, leakage prevention, validation-strategy selection, model selection, or writing final analytical conclusions. Claude may critique that work after the user completes it, but should not silently become the data scientist. When a task falls in this category, scaffold the mechanics and stop — leave the decisions to the user.

## Commands

The local environment is driven by `make` (targets exist once Milestone 1 lands):

```bash
make setup     # bootstrap Python workspace (uv) and local env
make dev       # start full local stack via Docker Compose
make test      # run the test suite
```

Python tooling: `uv` with `pyproject.toml`, Ruff + mypy + pre-commit, pytest (with testcontainers for integration tests). Tests live in `tests/{integration,data_quality,end_to_end}` plus per-package unit tests; run a single test with `uv run pytest path/to/test_file.py::test_name`.

## Architecture

Flow: ingestion services → (raw object storage in MinIO/S3 **and** Kafka) → Spark Structured Streaming → bronze → Airflow + PySpark → silver → dbt Core → gold (PostgreSQL/PostGIS + Parquet) → ML training/MLflow → FastAPI (+ Redis cache) → Next.js public site.

Strict tool responsibilities — do not blur them:
- **Kafka**: events only (observation received, forecast run received, DQ failure, prediction generated). Not a scheduler.
- **Object storage (MinIO/S3)**: every raw API response and all Parquet analytical data. Never use a Railway volume as the data lake.
- **PostgreSQL/PostGIS**: application queries (current conditions, locations, recent observations, metadata).
- **Spark**: expensive processing — backfills, large joins, streaming aggregations.
- **dbt**: documented analytical SQL models consumed by API/analytics.
- **Airflow**: batch orchestration only.

### Build sequence

Do not deploy the whole diagram up front. Build the vertical slice first: Open-Meteo + SKSM METAR → Python ingestion → raw object storage → ETL → PostgreSQL → FastAPI → minimal website. Insert Kafka, Spark, Airflow, dbt, and MLflow one at a time afterward — each addition must fix a real limitation of the previous architecture. Milestones (0–12 in docs) are sequential exit gates, not calendar dates.

## Repository layout (monorepo)

```
apps/{api,web}                      FastAPI backend, Next.js frontend
services/ingestion-{openmeteo,ideam,metar,nasa-power}
pipelines/{airflow/dags,spark/{batch,streaming},shared}
analytics/dbt
ml/{notebooks,features,training,evaluation,serving}
contracts/{events,schemas}          JSON Schema data contracts
infrastructure/{terraform,railway,docker}
observability/{grafana,prometheus,opentelemetry}
tests/{integration,data_quality,end_to_end}
docs/{architecture,adr,data_dictionary,methodology}
```

Source adapters must be isolated behind our own contracts — never leak third-party payload structures across the codebase. Never commit datasets, model artifacts, or notebook outputs to git (object storage and MLflow hold those).

## Data model rules

Warehouse uses explicit dimensional modeling: `dim_location`, `dim_station`, `dim_source`, `dim_variable`, `dim_weather_condition`, `dim_forecast_model`, `dim_date`, `dim_time`; facts include `fact_observation`, `fact_forecast`, `fact_marine_forecast`, `fact_air_quality`, `fact_forecast_verification`, `fact_data_quality_result`, `fact_environmental_alert`, `fact_model_prediction`.

**Never overwrite a forecast with a newer forecast.** Every forecast record stores both `forecast_generated_at` and `forecast_valid_at` so honest forecast verification is possible (what was predicted, what was known when, accuracy by horizon, model comparison).

Other invariants:
- Every record carries event time and ingestion time; failed payloads are preserved.
- Bronze is immutable (original payloads, request metadata, payload hashes); silver normalizes units/timestamps/locations with quality flags and dedup; gold serves current conditions, summaries, climate aggregates, and verification tables.
- ETL must be idempotent; historical partitions rebuildable; every gold record has lineage to source.
- API responses must include source timestamps; the site must distinguish observed vs. modelled data and degrade gracefully when a source is down. No environmental warning may be presented as an official government alert.

## ML conventions

Use cases: temperature forecast correction, rain-probability calibration, sensor/source anomaly detection. Every experiment logs dataset version, git commit, metrics, and artifacts to MLflow; a baseline is always included; model promotion requires an explicit evaluation gate; production models must be rollback-able. Time-aware train/validation/test splits are mandatory.

## Deployment

Three environments: local, staging, production. Railway hosts services (web, api, ingestion-worker, airflow, mlflow, otel-collector, postgres, redis) via `railway.toml` config-as-code; Railway cron has a 5-minute minimum and imprecise timing — use it for batch work only, persistent consumers run as ordinary services. External managed services handle object storage, production Kafka, and Grafana telemetry. Terraform uses the community Railway provider (`terraform-community-providers`, pin the version, currently 0.6.2) with remote state + locking; validate every plan in staging. CI/CD is GitHub Actions: PR pipeline runs Ruff, mypy, pytest, dbt parse/tests, Terraform fmt/validate, Checkov, Trivy, Gitleaks, Docker build, integration tests; main-branch pipeline deploys staging → smoke tests → migrations → manual production approval, with deployment concurrency so releases cannot collide.
