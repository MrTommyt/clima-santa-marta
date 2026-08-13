# Airflow with the project's ingestion packages installed, so DAG tasks can
# import clima_shared and the source adapters. Rebuild after changing any of
# the copied packages: docker compose build airflow
FROM apache/airflow:3.3.0-python3.12

COPY --chown=airflow:0 analytics/dbt /opt/clima/dbt
COPY --chown=airflow:0 pipelines/shared /opt/clima/shared
COPY --chown=airflow:0 pipelines/transforms /opt/clima/transforms
COPY --chown=airflow:0 db /opt/clima/db
COPY --chown=airflow:0 services/ingestion-metar /opt/clima/ingestion-metar
COPY --chown=airflow:0 services/ingestion-openmeteo /opt/clima/ingestion-openmeteo

# One command so pip satisfies the packages' clima-* dependencies from the
# local paths instead of looking for them on PyPI.
# The container runs as ${AIRFLOW_UID}:0, not the airflow user, so dbt's
# writable dirs (logs, target) need group-0 write access.
RUN chmod -R g+w /opt/clima/dbt && \
    pip install --no-cache-dir \
    dbt-postgres~=1.11 \
    /opt/clima/shared \
    /opt/clima/transforms \
    /opt/clima/db \
    /opt/clima/ingestion-metar \
    /opt/clima/ingestion-openmeteo
