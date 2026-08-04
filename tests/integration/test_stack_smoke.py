"""Smoke tests for the local compose stack.

Require `make dev` to be running; excluded from `make test` via the marker.
Connection settings mirror .env.example defaults and can be overridden with the
same environment variables compose uses.
"""

import os

import pytest

pytestmark = pytest.mark.integration


def test_postgres_reachable() -> None:
    import psycopg

    conn = psycopg.connect(
        host="localhost",
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "clima"),
        password=os.environ.get("POSTGRES_PASSWORD", "clima-local-dev"),
        dbname=os.environ.get("POSTGRES_DB", "clima"),
    )
    with conn, conn.cursor() as cur:
        cur.execute("SELECT postgis_version()")
        row = cur.fetchone()
    assert row is not None


def test_redis_reachable() -> None:
    import redis

    client = redis.Redis(host="localhost", port=int(os.environ.get("REDIS_PORT", "6379")))
    assert client.ping()


def test_minio_buckets_exist() -> None:
    import boto3

    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://localhost:{os.environ.get('MINIO_PORT', '9000')}",
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "minio"),
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", "minio-local-dev"),
    )
    buckets = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    assert {"raw", "bronze", "silver", "gold", "mlflow-artifacts"} <= buckets
