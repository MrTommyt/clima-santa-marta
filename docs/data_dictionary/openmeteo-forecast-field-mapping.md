# Open-Meteo forecast field mapping (bronze to silver)

Design record for `clima_transforms.openmeteo_forecast`; the code must match.
Verified against a real capture on 2026-08-09. The payload is parallel arrays:
`hourly.time[i]` pairs with `hourly.<field>[i]`.

| Source field | Canonical variable | Source unit | Canonical unit | Conversion | Notes |
| --- | --- | --- | --- | --- | --- |
| `temperature_2m` | `air_temperature_2m` | °C | °C | none | |
| `dew_point_2m` | `dew_point_2m` | °C | °C | none | |
| `relative_humidity_2m` | `relative_humidity_2m` | % | % | none | |
| `apparent_temperature` | `apparent_temperature` | °C | °C | none | |
| `precipitation` | `precipitation` | mm | mm | none | |
| `precipitation_probability` | `precipitation_probability` | % | % | none | forecast-only; fuels rain calibration (M7) |
| `surface_pressure` | `surface_pressure` | hPa | hPa | none | true surface pressure (unlike METAR's QNH; note kept for source comparison) |
| `cloud_cover` | `cloud_cover` | % | % | none | already a percentage (unlike METAR's coded cover) |
| `wind_speed_10m` | `wind_speed_10m` | km/h | m/s | ÷ 3.6 | |
| `wind_direction_10m` | `wind_direction_10m` | degrees | degrees | none | |
| `wind_gusts_10m` | `wind_gust_10m` | km/h | m/s | ÷ 3.6 | source name is plural, canonical singular |
| `rain` | (not consumed) | | | | subset of `precipitation`; storing both would double-count |

Absent or null array entries: skip (no row).

## Timestamps

- `forecast_generated_at` = the capture bucket, parsed from the object key
  (`.../day=DD/HHMMZ-<hash>`). It is NOT in the payload; it is the identity
  the capture design created, handed from bronze to silver.
- `forecast_valid_at` = each `hourly.time[i]`: naive local time; attach the
  payload's own `utc_offset_seconds` and convert to UTC.
- `forecast_model` = `"best_match"` (constant until model selection is
  requested explicitly in the source config).

## Idempotency

Append-only insert on the six-column grain (location, variable, valid_at,
generated_at, source, model): replaying a window can only skip, never
overwrite. Forecast runs never supersede each other by design (ADR-0005).
