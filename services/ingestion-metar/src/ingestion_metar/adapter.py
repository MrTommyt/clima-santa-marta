from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from clima_shared.http_adapter import HttpSourceAdapter
from clima_shared.models import FetchRequest


def floor_to_interval(moment: datetime, minutes: int) -> datetime:
    floored_minute = (moment.minute // minutes) * minutes
    return moment.replace(minute=floored_minute, second=0, microsecond=0)


class MetarObservationsAdapter(HttpSourceAdapter):
    """Rolling-window source: the API only serves the recent past, so the
    only capturable partition is the current interval. Each capture stores
    the full lookback window, which lets a later capture recover the
    observations of intervals missed during an outage; gaps longer than the
    lookback are permanently lost by nature of the source."""

    source = "metar"
    dataset = "observations"

    def plan(
        self,
        *,
        requested_from: date | None = None,
        requested_to: date | None = None,
    ) -> list[FetchRequest]:
        # Date ranges are not applicable to a rolling window; only the
        # current capture interval can be planned.
        bucket = floor_to_interval(
            datetime.now(UTC),
            self.config["capture_interval_minutes"],
        )

        requests: list[FetchRequest] = []

        for location_id, location in self.config["locations"].items():
            parameters = {
                "station": location["icao"],
                "interval_start": bucket.isoformat(),
            }

            requests.append(
                FetchRequest(
                    source=self.source,
                    dataset=self.dataset,
                    location_id=location_id,
                    start_date=bucket.date(),
                    end_date=bucket.date(),
                    parameters=parameters,
                    time_label=f"{bucket:%H%M}Z",
                )
            )

        return requests

    def request_params(self, request: FetchRequest) -> dict[str, Any]:
        return {
            "ids": request.parameters["station"],
            "format": "json",
            "hours": self.config["lookback_hours"],
        }

    def validate(self, parsed: Any, request: FetchRequest) -> None:
        if not isinstance(parsed, list):
            raise ValueError(
                "METAR response is not a list of reports. "
                f"Request ID: {request.request_id}"
            )
