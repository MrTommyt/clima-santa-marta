from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from clima_shared.bootstrap import BootstrapResult, BootstrapService
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

    # No broker configured means no events: bronze writes still happen.
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    events = (
        KafkaEventPublisher(bootstrap_servers=bootstrap_servers)
        if bootstrap_servers
        else None
    )

    return BootstrapService(
        adapter=adapter,
        bronze=bronze,
        events=events,
    )


def optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def run_prefetch(
    adapter: HttpSourceAdapter,
    *,
    requested_from: date | None = None,
    requested_to: date | None = None,
    plan_only: bool = False,
) -> list[BootstrapResult]:
    """Shared prefetch flow for CLIs and Airflow tasks: plan the desired
    partitions, list what is missing from bronze, and fetch it unless
    plan_only. Closes the adapter when done."""
    service = build_service(adapter)

    try:
        desired = adapter.plan(
            requested_from=requested_from,
            requested_to=requested_to,
        )

        missing = service.find_missing(desired)

        print(f"Desired partitions: {len(desired)}")
        print(f"Missing partitions: {len(missing)}")

        for request in missing:
            print(request.object_key)

        if plan_only:
            return []

        results: list[BootstrapResult] = []

        for request in missing:
            result = service.run_one(request)
            print(f"{result.status}: {result.object_key}")
            results.append(result)

        return results
    finally:
        adapter.close()


def run_cli(adapter: HttpSourceAdapter) -> None:
    """Standard prefetch CLI shared by all sources."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Show missing objects without fetching them",
    )

    args = parser.parse_args()

    run_prefetch(
        adapter,
        requested_from=optional_date(args.from_date),
        requested_to=optional_date(args.to_date),
        plan_only=args.plan,
    )
