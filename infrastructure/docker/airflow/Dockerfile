# Airflow with the project's ingestion packages installed, so DAG tasks can
# import clima_shared and the source adapters. Rebuild after changing any of
# the copied packages: docker compose build airflow
FROM apache/airflow:3.3.0-python3.12

COPY --chown=airflow:0 pipelines/shared /opt/clima/shared
COPY --chown=airflow:0 services/ingestion-metar /opt/clima/ingestion-metar
COPY --chown=airflow:0 services/ingestion-openmeteo /opt/clima/ingestion-openmeteo

# One command so pip satisfies the services' clima-shared dependency from the
# local path instead of looking for it on PyPI.
RUN pip install --no-cache-dir \
    /opt/clima/shared \
    /opt/clima/ingestion-metar \
    /opt/clima/ingestion-openmeteo
