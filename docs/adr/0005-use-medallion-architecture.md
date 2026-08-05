# ADR-0005: Use a medallion architecture

- **Status**: Accepted
- **Date**: 2026-07-05

## Context

The platform ingest from 4 different sources (Open-Meteo, SKSM, IDEAM, NASA POWER), and probably more in the coming future but they all have different formats in the way they send the data, units, timestamp conversions and also they're different in terms of reliabilty.

Sources deliver heterogeneous, sometimes late or corrected data (IDEAM warns of this). Forecast verification needs immutable history, and reprocessing must not depend on re-calling external APIs. Cleaned data needs database behavior (constraints, upserts, spatial queries); analytics and ML favor columnar files. Medallion organizes data by quality.

## Decision

Keep the medallion architecture as the logical model. Postgres will store living data, while Historical analytical data will be stored inside Parquet objects

|Layer|Storage|
|---|---|
|Raw/Bronze| Object storage; Compressed JSON. Never deleted |
|Silver| Postgres/PostGIS |
|Gold serving| Postgres tables & Materialized Views |
|Gold analytics| Dated, versioned Parquet snapshots |

## Consequences

- Later corrections in this model would need to become upserts to keep the historical data consistent.
- Idempotency and forecast immutability are constrained by schema.
- dbt will run in its native in-warehouse pattern.

## Alternatives considered

- **All-parquet medallion**; no constraints but correction would need complete partition rewrites. Rejected.
- **Everything in postgres**; would turn the database into the data lake. Rejected.
- **Iceberg / TimescaleDB**; too complex for this initial stage. Could be considered later.
