#!/bin/bash
# Runs only on first boot of an EMPTY pgdata volume (docker-entrypoint-initdb.d
# contract). If the database layout changes, run `make clean` to drop volumes.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE DATABASE airflow OWNER "$POSTGRES_USER";
    CREATE DATABASE mlflow OWNER "$POSTGRES_USER";
EOSQL
