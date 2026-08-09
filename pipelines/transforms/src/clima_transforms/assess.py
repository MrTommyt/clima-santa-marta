"""Per-value quality assessment.

The verdict vocabulary matches the CHECK constraint on
silver.weather_observation: valid | suspicious | invalid.

The BOUNDS table is the data-science content of this module and it is YOURS:
the example row shows the shape, not the answer. For each canonical variable
decide two ranges from Santa Marta's actual climate:
- hard: outside this, the value is physically implausible -> invalid
- soft: inside hard but outside this, keep an eyebrow raised -> suspicious
Document your reasoning per variable in the mapping doc or a short note;
"why is 12 the lower bound" must be answerable later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bounds:
    hard_min: float
    hard_max: float
    soft_min: float
    soft_max: float


BOUNDS: dict[str, Bounds] = {
    # EXAMPLE ROW: the numbers are placeholders demonstrating the shape.
    # Replace with your own reasoned values, then add every variable the
    # mapping produces. A variable missing from this table gets 'valid'
    # by default (see assess), so absence here is a decision too.
    "air_temperature_2m": Bounds(
        hard_min=0.0,
        hard_max=70.0,
        soft_min=18.0,
        soft_max=50.0,
    ),
    # TODO: dew_point_2m, wind_speed_10m, wind_direction_10m, wind_gust_10m,
    #       surface_pressure, visibility, ...
}


def assess(variable: str, value: float) -> str:
    bounds = BOUNDS.get(variable)

    if bounds is None:
        return "valid"

    if value < bounds.hard_min or value > bounds.hard_max:
        return "invalid"

    if value < bounds.soft_min or value > bounds.soft_max:
        return "suspicious"

    return "valid"
