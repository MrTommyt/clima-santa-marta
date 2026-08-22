# ADR-0003: Use railway as host

- **Status**: Accepted
- **Date**: 2026-08-05

## Context

This decision is mostly shaped by cost, given that this project is designed to be minimal, though with lots of moving parts, I believe that railway and their flexible resource management would allow me to keep costs to a minimal while keeping flexibility of a managed space.

## Decision

Use railway as principal host of the entire project.

## Consequences

- Host would be initially cheaper.
- It would be easier to manage short term.
- If the project grows, moving it to another CSP could be reconsidered. Depending on the money I have available.
- Observed at first deployment (2026-08-21): Railway's Postgres template has no PostGIS, so the PostGIS template (Postgres 16) is used instead of the local Postgres 17; Railway's own S3-compatible bucket serves as production object storage, as the spec prescribes over container volumes; and only the collection slice (PostGIS, bucket, Airflow) is deployed, with Kafka, Redis, MLflow, API and website deferred to their milestones.

## Alternatives considered

- AWS
- GCP
- Hetzner (problem with hetzner is the locations tend to be Europe-based)
