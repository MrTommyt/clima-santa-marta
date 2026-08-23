# Airflow on Railway: one container running scheduler, api-server, triggerer
# and dag-processor (airflow standalone). DAGs and source config are baked in;
# a push to main rebuilds the image. Build context is the repo root.
FROM apache/airflow:3.3.0-python3.12

COPY --chown=airflow:0 analytics/dbt /opt/clima/dbt
COPY --chown=airflow:0 pipelines/shared /opt/clima/shared
COPY --chown=airflow:0 pipelines/transforms /opt/clima/transforms
COPY --chown=airflow:0 db /opt/clima/db
COPY --chown=airflow:0 services/ingestion-metar /opt/clima/ingestion-metar
COPY --chown=airflow:0 services/ingestion-openmeteo /opt/clima/ingestion-openmeteo
COPY --chown=airflow:0 pipelines/airflow/dags /opt/airflow/dags
COPY --chown=airflow:0 config /opt/airflow/config

RUN chmod -R g+w /opt/clima/dbt && \
    pip install --no-cache-dir \
    dbt-postgres~=1.11 \
    /opt/clima/shared \
    /opt/clima/transforms \
    /opt/clima/db \
    /opt/clima/ingestion-metar \
    /opt/clima/ingestion-openmeteo

ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor \
    AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__API__PORT=8080 \
    SOURCE_CONFIG_PATH=/opt/airflow/config/sources.yaml

COPY --chown=airflow:0 infrastructure/railway/airflow/entrypoint.sh /opt/clima/entrypoint.sh

CMD ["bash", "/opt/clima/entrypoint.sh"]
