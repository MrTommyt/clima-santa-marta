# The stock mlflow image ships neither a Postgres driver nor S3 support, so this
# thin layer is required for the postgres backend store + MinIO artifact store.
FROM ghcr.io/mlflow/mlflow:v3.17.1

RUN pip install --no-cache-dir psycopg2-binary~=2.9 boto3~=1.40
