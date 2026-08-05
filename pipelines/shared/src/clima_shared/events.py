from __future__ import annotations

import json
from datetime import UTC, datetime

from confluent_kafka import Producer

from clima_shared.bronze import StoredObject
from clima_shared.models import FetchRequest


class KafkaEventPublisher:
    def __init__(
        self,
        *,
        bootstrap_servers: str,
        topic: str = "bronze.object.created.v1",
    ) -> None:
        self.topic = topic
        self.producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
                "client.id": "climate-ingestion",
            }
        )

    def publish_created(
        self,
        request: FetchRequest,
        stored: StoredObject,
    ) -> None:
        event = {
            "event_id": request.request_id,
            "event_type": "bronze.object.created",
            "event_version": 1,
            "occurred_at": datetime.now(UTC).isoformat(),
            "source": request.source,
            "dataset": request.dataset,
            "location_id": request.location_id,
            "partition_start": request.start_date.isoformat(),
            "partition_end": request.end_date.isoformat(),
            "object_key": stored.object_key,
            "checksum_sha256": stored.checksum_sha256,
            "size_bytes": stored.size_bytes,
        }

        self.producer.produce(
            topic=self.topic,
            key=request.request_id,
            value=json.dumps(event).encode("utf-8"),
        )

        remaining = self.producer.flush(timeout=10)

        if remaining:
            raise RuntimeError(f"{remaining} Kafka message(s) were not delivered")
