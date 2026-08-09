# Open-Meteo modelled history field mapping (bronze to silver)

Design record for `clima_transforms.openmeteo_history`. Target:
`silver.weather_model_history`.

The payload format and units are identical to the forecast captures, so the
variable table is shared: see
[openmeteo-forecast-field-mapping.md](openmeteo-forecast-field-mapping.md).
Fields absent from the historical dataset (`dew_point_2m`,
`precipitation_probability`) simply produce no rows.

## What this data is

The model's after-the-fact estimate of completed days (analysis), fetched one
day behind real time. By the PRD definitions it is **modelled**: not observed
(no instrument), not forecast (no issuance semantics).

- **Never verification ground truth.** Verifying Open-Meteo forecasts against
  Open-Meteo analysis is the model grading its own homework. Ground truth is
  METAR (airport) and, later, IDEAM stations.
- Legitimate uses: climate exploration, clearly-labelled modelled context at
  locations without instruments, ML baseline features.
- Overlaps in content with the negative-horizon rows inside forecast captures
  (`past_days`); different keys, different questions. This table is the
  canonical modelled past; the forecast rows are per-issuance snapshots.

## Bronze-immutability exception (2026-08-09)

21 objects for days 2026-08-08..15 were deleted from bronze along with their
4,536 silver rows: they were fetched before those days completed (development
artifacts), contained forecast data mislabeled as history, and their presence
made the daily prefetch skip fetching the real data. This is the only
sanctioned reason to delete bronze: a partition that never represented what
its key claims. The days were refetched properly afterward.

## Timestamps

`valid_at` = each `hourly.time[i]`, naive local plus the payload's
`utc_offset_seconds`, converted to UTC. There is no issuance column; a
re-fetched revised day would be skipped by the grain (first version wins),
matching bronze's fetch-once policy.
