from __future__ import annotations

from datetime import date
from typing import Any

from clima_shared.http_adapter import HttpSourceAdapter
from clima_shared.models import FetchRequest


class OpenMeteoHistoricalAdapter(HttpSourceAdapter):
    source = "open_meteo"
    dataset = "historical_forecast"

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

        for location_id, location in self.config["locations"].items():
            for day in self.daterange(start, end):
                parameters = {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "start_date": day.isoformat(),
                    "end_date": day.isoformat(),
                    "hourly": ",".join(self.config["hourly"]),
                    "timezone": self.config.get("timezone", "UTC"),
                }

                requests.append(
                    FetchRequest(
                        source=self.source,
                        dataset=self.dataset,
                        location_id=location_id,
                        start_date=day,
                        end_date=day,
                        parameters=parameters,
                    )
                )

        return requests

    def validate(self, parsed: Any, request: FetchRequest) -> None:
        if "hourly" not in parsed:
            raise ValueError(
                "Open-Meteo response does not contain hourly data. "
                f"Request ID: {request.request_id}"
            )
