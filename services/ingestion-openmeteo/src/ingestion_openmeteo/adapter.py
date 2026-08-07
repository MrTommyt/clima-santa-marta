from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from clima_shared.http_adapter import HttpSourceAdapter
from clima_shared.models import FetchRequest


class OpenMeteoHistoricalAdapter(HttpSourceAdapter):
    source = "open_meteo"
    dataset = "historical_forecast"

    def __init__(self, config):
        super().__init__(config)
        src = self.config.get("source")
        dts = self.config.get("dataset")

        if src is not None:
            self.source = src
        if dts is not None:
            self.dataset = dts

    def plan(
        self,
        *,
        requested_from: date | None = None,
        requested_to: date | None = None,
    ) -> list[FetchRequest]:
        window = self.availability_window(requested_from, requested_to)

        if window is None:
            return []

        start, end = window

        requests: list[FetchRequest] = []

        bucket = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        bucket = bucket.replace(hour=bucket.hour - bucket.hour % 4)

        is_forecast = self.config.get("forecast")
        for location_id, location in self.config["locations"].items():

            def append_request(start, end, location_id, location):
                parameters = {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "hourly": ",".join(self.config["hourly"]),
                    "timezone": self.config.get("timezone", "UTC"),
                }

                if is_forecast:
                    parameters["interval_start"] = bucket.isoformat()

                requests.append(
                    FetchRequest(
                        source=self.source,
                        dataset=self.dataset,
                        location_id=location_id,
                        start_date=start,
                        end_date=end,
                        parameters=parameters,
                        time_label=f"{bucket:%H%M}Z" if is_forecast else None,
                    )
                )

            if is_forecast:
                append_request(start, end, location_id, location)
                continue

            for day in self.daterange(start, end):
                append_request(day, day, location_id, location)

        return requests

    def request_params(self, request):
        return {k: v for k, v in request.parameters.items() if k != "interval_start"}

    def validate(self, parsed: Any, request: FetchRequest) -> None:
        if "hourly" not in parsed:
            raise ValueError(
                "Open-Meteo response does not contain hourly data. "
                f"Request ID: {request.request_id}"
            )
