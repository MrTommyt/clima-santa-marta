from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from clima_shared.models import FetchRequest

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


def is_retryable_error(exception: BaseException) -> bool:
    if isinstance(
        exception,
        (
            httpx.ConnectTimeout,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ReadError,
            httpx.RemoteProtocolError,
        ),
    ):
        return True

    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_STATUS_CODES

    return False


def canonical_json_bytes(parsed: Any) -> bytes:
    """Re-encode into stable JSON bytes rather than storing content whose
    formatting is controlled by the provider."""
    return json.dumps(
        parsed,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class HttpSourceAdapter:
    """Shared HTTP machinery for source adapters.

    A concrete source provides only what is specific to it: the `source` and
    `dataset` identifiers, `plan()` (which partitions should exist), and
    `validate()` (what a usable response must contain). The endpoint and an
    optional `user_agent` come from the source config.
    """

    source: str
    dataset: str

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

        timeout = httpx.Timeout(
            connect=30.0,
            read=90.0,
            write=30.0,
            pool=30.0,
        )

        limits = httpx.Limits(
            max_connections=5,
            max_keepalive_connections=5,
            keepalive_expiry=30.0,
        )

        self.client = httpx.Client(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            headers={
                "User-Agent": config.get("user_agent", "clima-santa-marta/0.1"),
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self.client.close()

    def plan(
        self,
        *,
        requested_from: date | None = None,
        requested_to: date | None = None,
    ) -> list[FetchRequest]:
        raise NotImplementedError

    def validate(self, parsed: Any, request: FetchRequest) -> None:
        """Override to reject responses that lack the expected data."""

    def request_params(self, request: FetchRequest) -> dict[str, Any]:
        """Query parameters actually sent to the API.

        Defaults to the request's identity parameters. Override when identity
        and query differ, e.g. a rolling-window source whose identity is the
        capture interval but whose query is a lookback in hours."""
        return request.parameters

    @retry(
        retry=retry_if_exception(is_retryable_error),
        wait=wait_random_exponential(
            multiplier=1,
            min=1,
            max=30,
        ),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(
            logger,
            logging.WARNING,
        ),
        reraise=True,
    )
    def fetch(self, request: FetchRequest) -> bytes:
        response = self.client.get(
            self.config["endpoint"],
            params=self.request_params(request),
        )

        response.raise_for_status()

        parsed = response.json()

        self.validate(parsed, request)

        return canonical_json_bytes(parsed)

    def availability_window(
        self,
        requested_from: date | None,
        requested_to: date | None,
    ) -> tuple[date, date] | None:
        """Clamp a requested range to what the source can safely provide,
        using the `available_from` and `availability_lag_days` config keys.
        Returns None when nothing is available."""
        forecast_days = self.config.get("forecast_days")
        available_from = (
            date.today()
            if forecast_days is not None
            else date.fromisoformat(self.config["available_from"])
        )

        latest_safe_date = (
            date.today() - timedelta(days=self.config["availability_lag_days"])
            if forecast_days is None
            else date.today() + timedelta(days=forecast_days)
        )

        start = max(requested_from or available_from, available_from)
        end = min(requested_to or latest_safe_date, latest_safe_date)

        if start > end:
            return None

        return start, end

    @staticmethod
    def daterange(start: date, end: date) -> Iterator[date]:
        current = start

        while current <= end:
            yield current
            current += timedelta(days=1)
