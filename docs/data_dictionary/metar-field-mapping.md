# METAR field mapping (bronze to silver)

One row per source field the transform consumes. This document is the design
record for `clima_transforms.metar`; the code must match it. Findings verified
against a real SKSM report on 2026-08-07 (rawOb: `METAR SKSM 071800Z 21007KT
9999 NSC 30/25 Q1009`). Cells marked **decision** are choices, not source
facts; change them only together with the code and a PIPELINE_VERSION bump.

| Source field | Canonical variable | Source unit | Canonical unit | Conversion | When absent | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `temp` | `air_temperature_2m` | °C | °C | none | skip (no row) | verified: `30` matched `30/25` in rawOb |
| `dewp` | `dew_point_2m` | °C | °C | none | skip | verified against `30/25` |
| `wspd` | `wind_speed_10m` | knots | m/s | × 0.514444 | skip | verified: `7` matched `21007KT` |
| `wdir` | `wind_direction_10m` | degrees | degrees | none | skip | **decision**: value `"VRB"` (variable wind) → skip the direction row, keep the speed row |
| `wgst` | `wind_gust_10m` | knots | m/s | × 0.514444 | skip | absent means "no gusts reported" (calm), not sensor failure |
| `altim` | `surface_pressure` | hPa | hPa | none | skip | verified: `1009` matched `Q1009` (QNH, sea-level-referenced). **decision**: used as surface pressure knowingly; at SKSM's 5 m elevation the QNH-vs-station difference (~0.6 hPa) is negligible. Revisit if a station with real elevation ever reports via METAR |
| `slp` | (not consumed) | | | | | field does not appear in this feed's reports |
| `visib` | `visibility` | statute miles | m | × 1609.34 | skip | **decision**: `"N+"` capped values (e.g. `"6+"`, matching international code 9999) → store canonical 10000.0 m ("10 km or more") |
| `cover` | `cloud_cover` | CLR/FEW/SCT/BKN/OVC | % | okta midpoints | skip | **decision**: CLR=0, FEW=18.75, SCT=43.75, BKN=75, OVC=100 (standard okta band midpoints) |
| `clouds` | (not consumed in v1) | | | | | per-layer detail; `cover` summary suffices for now |
| `wxString` | (not consumed in v1) | | | | | maps to `weather_condition`, which needs a standardization vocabulary; deferred until that design exists |
| `qcField`, `fltCat`, `lat`, `lon`, `elev`, `name` | (not consumed) | | | | | station metadata / aviation categories; station facts already live in `metadata.station` |

## Timestamps

- `observed_at` = `reportTime` (ISO 8601 UTC with `Z`, e.g.
  `2026-08-07T18:00:00.000Z`; `datetime.fromisoformat` parses it on
  Python 3.11+). `obsTime` is the same instant as epoch seconds: ignored.
- `receiptTime` is when Aviation Weather received the report;
  `receiptTime - reportTime` is a per-report source-delay measurement.
  Not stored in v1, but it is the natural input for the freshness metric
  (issue #15) when that lands.
- The capture bucket in the object key is NOT the observation time: one
  snapshot contains many reports with their own times.

## Report types

**Decision**: SPECI reports (off-schedule special observations during rapidly
changing weather) are consumed like METARs: they are real observations, and
the unique constraint absorbs any timing overlap.

## Duplicates across snapshots

Consecutive snapshots overlap by design (24 h lookback). The same report
appears in many objects. **Decision**: first-seen snapshot wins lineage: the
upsert uses ON CONFLICT DO NOTHING, so `raw_record_id` points at the earliest
capture containing the report.

## Quality bounds calibration

Bounds in `clima_transforms/assess.py` are currently calibrated for coastal
SKSM only (e.g. `soft_min=18` °C). Mountain stations (Minca at 650 m, San
Lorenzo at 2,200 m) would trip `suspicious` on normal readings: revisit
per-station or per-elevation bounds when IDEAM stations arrive (Milestone 6).
Variables without bounds default to `valid`: triage, not oversight.
