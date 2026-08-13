"""Loader integration tests against the local stack (make dev)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_observations_long_and_wide():
    from clima_ml import load

    frame = load.observations(variables=["air_temperature_2m", "dew_point_2m"])

    assert not frame.empty
    assert set(frame.columns) >= {"station", "variable", "value", "observed_at"}
    assert frame["observed_at"].dt.tz is not None

    pivoted = load.wide(frame)
    assert "air_temperature_2m" in pivoted.columns


def test_forecasts_have_horizon():
    from clima_ml import load

    frame = load.forecasts(variables=["air_temperature_2m"], min_horizon=0)

    assert not frame.empty
    assert (frame["horizon_hours"] >= 0).all()


def test_verification_loads():
    from clima_ml import load

    frame = load.verification(variables=["air_temperature_2m"])

    assert not frame.empty
    assert {"forecast_value", "observed_value", "forecast_error"} <= set(frame.columns)
