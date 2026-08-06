from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class FetchRequest:
    source: str
    dataset: str
    location_id: str
    start_date: date
    end_date: date
    parameters: dict[str, Any]
    time_label: str | None = None

    @property
    def request_id(self) -> str:
        """Create a deterministic identifier from the request contents."""
        canonical = json.dumps(
            {
                "source": self.source,
                "dataset": self.dataset,
                "location_id": self.location_id,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "parameters": self.parameters,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def object_key(self) -> str:
        """Return the deterministic MinIO path for this request."""
        return (
            f"source={self.source}/"
            f"dataset={self.dataset}/"
            f"location={self.location_id}/"
            f"year={self.start_date.year:04d}/"
            f"month={self.start_date.month:02d}/"
            f"day={self.start_date.day:02d}/"
            + (f"{self.time_label}-" if self.time_label else "")
            + f"{self.request_id[:16]}.json.gz"
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["start_date"] = self.start_date.isoformat()
        result["end_date"] = self.end_date.isoformat()
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FetchRequest:
        return cls(
            source=value["source"],
            dataset=value["dataset"],
            location_id=value["location_id"],
            start_date=date.fromisoformat(value["start_date"]),
            end_date=date.fromisoformat(value["end_date"]),
            parameters=value["parameters"],
            time_label=value.get("time_label"),
        )
