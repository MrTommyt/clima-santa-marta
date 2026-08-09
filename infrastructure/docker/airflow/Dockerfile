# Airflow with the project's ingestion packages installed, so DAG tasks can
# import clima_shared and the source adapters. Rebuild after changing any of
# the copied packages: docker compose build airflow
FROM apache/airflow:3.3.0-python3.12

COPY --chown=airflow:0 pipelines/shared /opt/clima/shared
COPY --chown=airflow:0 pipelines/transforms /opt/clima/transforms
COPY --chown=airflow:0 db /opt/clima/db
COPY --chown=airflow:0 services/ingestion-metar /opt/clima/ingestion-metar
COPY --chown=airflow:0 services/ingestion-openmeteo /opt/clima/ingestion-openmeteo

# One command so pip satisfies the packages' clima-* dependencies from the
# local paths instead of looking for them on PyPI.
RUN pip install --no-cache-dir \
    /opt/clima/shared \
    /opt/clima/transforms \
    /opt/clima/db \
    /opt/clima/ingestion-metar \
    /opt/clima/ingestion-openmeteo
