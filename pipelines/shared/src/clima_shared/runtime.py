from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from clima_shared.bootstrap import BootstrapService
from clima_shared.bronze import MinioBronzeStore
from clima_shared.events import KafkaEventPublisher
from clima_shared.http_adapter import HttpSourceAdapter


def load_source_config(key: str) -> dict[str, Any]:
    config_path = Path(os.getenv("SOURCE_CONFIG_PATH", "/app/config/sources.yaml"))

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config[key]


def build_service(adapter: HttpSourceAdapter) -> BootstrapService:
    bronze = MinioBronzeStore(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        bucket=os.getenv("MINIO_BRONZE_BUCKET", "bronze"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )
    bronze.ensure_bucket()

    events = KafkaEventPublisher(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"],
    )

    return BootstrapService(
        adapter=adapter,
        bronze=bronze,
        events=events,
    )


def optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def run_cli(adapter: HttpSourceAdapter) -> None:
    """Standard prefetch CLI shared by all sources: plan the desired
    partitions, list what is missing from bronze, and fetch it unless --plan."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Show missing objects without fetching them",
    )

    args = parser.parse_args()

    service = build_service(adapter)

    try:
        desired = adapter.plan(
            requested_from=optional_date(args.from_date),
            requested_to=optional_date(args.to_date),
        )

        missing = service.find_missing(desired)

        print(f"Desired partitions: {len(desired)}")
        print(f"Missing partitions: {len(missing)}")

        for request in missing:
            print(request.object_key)

        if args.plan:
            return

        for request in missing:
            result = service.run_one(request)
            print(f"{result.status}: {result.object_key}")
    finally:
        adapter.close()
