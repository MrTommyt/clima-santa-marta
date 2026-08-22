from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from clima_shared.bronze import MinioBronzeStore
from clima_shared.events import KafkaEventPublisher
from clima_shared.models import FetchRequest


class SourceAdapter(Protocol):
    def fetch(self, request: FetchRequest) -> bytes:
        """Fetch one source partition and return the original response bytes."""


@dataclass(frozen=True)
class BootstrapResult:
    request_id: str
    object_key: str
    status: str


class BootstrapService:
    def __init__(
        self,
        *,
        adapter: SourceAdapter,
        bronze: MinioBronzeStore,
        events: KafkaEventPublisher | None,
    ) -> None:
        self.adapter = adapter
        self.bronze = bronze
        self.events = events

    def find_missing(
        self,
        requests: Sequence[FetchRequest],
    ) -> list[FetchRequest]:
        return [
            request
            for request in requests
            if not self.bronze.exists(request.object_key)
        ]

    def run_one(self, request: FetchRequest) -> BootstrapResult:
        # Airflow may retry a task, so check again immediately before fetching.
        if self.bronze.exists(request.object_key):
            return BootstrapResult(
                request_id=request.request_id,
                object_key=request.object_key,
                status="skipped",
            )

        payload = self.adapter.fetch(request)

        stored = self.bronze.put_json(
            object_key=request.object_key,
            payload=payload,
        )

        if self.events is not None:
            self.events.publish_created(request, stored)

        return BootstrapResult(
            request_id=request.request_id,
            object_key=stored.object_key,
            status="created",
        )
