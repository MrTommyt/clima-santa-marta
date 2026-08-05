# Product requirements

## Problem

Merge multiple meteorological stations into one clear signal and a better, more
tailored forecast for Santa Marta than generic weather services provide.

## Target users

Anyone currently in the city (residents, tourists, boaters and divers, researchers)
who wants a forecast they can trust for Santa Marta specifically. And, candidly: hiring
managers reviewing this project as a portfolio.

## Geographic zones

The vertical slice uses physical stations whose observations can be retrieved
programmatically. Coordinates are station locations (not administrative zones); model
forecasts are requested for the same coordinates so forecasts can be compared against
observations.

| Location | Lat | Lon | Source | Station ID | Why included |
| --- | ---: | ---: | --- | --- | --- |
| Aeropuerto Internacional Simón Bolívar | 11.1147 | -74.2310 | IDEAM WIS2 and AviationWeather METAR | IDEAM `15015050`; WIGOS `0-20000-0-80009`; ICAO `SKSM` | Reliable low-elevation coastal reference with operational aviation observations (temperature, dew point, wind, pressure, visibility, clouds). Main forecast-validation station. |
| Minca Automatic Station | 11.14028 | -74.11972 | IDEAM WIS2 | WIGOS `0-170-0-15017030` | Humid foothill environment (~650 m); enables coast-vs-lower-Sierra comparison. |
| San Lorenzo Automatic Station | 11.06667 | -74.03333 | IDEAM WIS2 | WIGOS `0-170-0-15015060` | High-elevation Sierra Nevada (~2,200 m); strongest climatic contrast with the coast. |

## Supported variables

Priority goes to variables available from **both** physical observations and numerical
forecasts, so predictions can be compared against real measurements instead of merely
republishing an external forecast. Not every station reports every variable;
per-station availability is checked during source validation, and source quality
(IDEAM explicitly warns of delays, gaps, and sensor failures) is measured, not assumed.

### Core variables for the vertical slice

| Canonical variable          | Unit                  | Data type                        | Initial sources                                                                | Purpose                                                                 |
| --------------------------- | --------------------- | -------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `air_temperature_2m`        | °C                    | Observed and forecast            | IDEAM, SKSM METAR, Open-Meteo                                                  | Current conditions, daily cycles, forecast evaluation and ML correction |
| `dew_point_2m`              | °C                    | Observed and forecast            | SKSM METAR, Open-Meteo                                                         | Atmospheric moisture, discomfort analysis and humidity validation       |
| `relative_humidity_2m`      | %                     | Observed, forecast or derived    | IDEAM, Open-Meteo; derived from METAR temperature and dew point when necessary | Moisture conditions, heat discomfort and rainfall analysis              |
| `precipitation`             | mm per interval       | Observed and forecast            | IDEAM, Open-Meteo                                                              | Rainfall totals, event detection and forecast verification              |
| `precipitation_probability` | %                     | Forecast                         | Open-Meteo                                                                     | Rain-risk communication and probability calibration                     |
| `wind_speed_10m`            | m/s                   | Observed and forecast            | IDEAM, SKSM METAR, Open-Meteo                                                  | Coastal wind analysis, event detection and forecast accuracy            |
| `wind_direction_10m`        | degrees               | Observed and forecast            | SKSM METAR, Open-Meteo                                                         | Sea-breeze patterns, wind roses and directional forecast evaluation     |
| `wind_gust_10m`             | m/s                   | Observed when reported; forecast | SKSM METAR, Open-Meteo                                                         | Strong-wind events and forecast verification                            |
| `surface_pressure`          | hPa                   | Observed and forecast            | SKSM METAR, Open-Meteo                                                         | Weather-pattern analysis and source comparison                          |
| `visibility`                | m                     | Observed and forecast            | SKSM METAR, Open-Meteo                                                         | Heavy-rain, haze and aviation-condition analysis                        |
| `cloud_cover`               | % or coded layers     | Observed and forecast            | SKSM METAR, Open-Meteo                                                         | Cloud-cycle analysis, radiation context and forecast verification       |
| `weather_condition`         | Standardized category | Observed and forecast            | SKSM METAR, Open-Meteo WMO weather code                                        | Human-readable conditions and categorical verification                  |

### Derived variables

Calculated from standardized silver-layer data; formulas and inputs are documented and
versioned. Derived heat indicators are analytical information, **not** official
public-health warnings.

| Derived variable              | Inputs                                                      | Purpose                                       |
| ----------------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| `apparent_temperature`        | Temperature, humidity, wind and possibly radiation          | Estimate perceived outdoor heat               |
| `heat_index`                  | Temperature and relative humidity                           | Identify hot and humid periods                |
| `wet_bulb_temperature_approx` | Temperature, relative humidity and pressure where available | Explore combined heat and moisture            |
| `daily_temperature_min`       | Hourly temperature                                          | Daily summaries                               |
| `daily_temperature_max`       | Hourly temperature                                          | Daily summaries and hot-day detection         |
| `daily_temperature_mean`      | Hourly temperature                                          | Climate summaries                             |
| `daily_precipitation_total`   | Interval precipitation                                      | Daily rainfall analysis                       |
| `precipitation_24h`           | Rolling precipitation                                       | Short-term rainfall accumulation              |
| `precipitation_72h`           | Rolling precipitation                                       | Antecedent rainfall context                   |
| `wind_u_component`            | Wind speed and direction                                    | Statistical and ML modelling                  |
| `wind_v_component`            | Wind speed and direction                                    | Statistical and ML modelling                  |
| `temperature_forecast_error`  | Forecast and observed temperature                           | Forecast evaluation                           |
| `forecast_absolute_error`     | Forecast and observed value                                 | MAE calculation                               |
| `forecast_bias`               | Forecast minus observed value                               | Systematic-error analysis                     |
| `source_delay_minutes`        | Observation time and ingestion time                         | Data-freshness monitoring                     |
| `missing_interval_flag`       | Expected and received timestamps                            | Data completeness                             |
| `quality_status`              | Validation rules                                            | Identify valid, suspicious and invalid values |

### Required metadata

Every record carries enough metadata to interpret, trace, and reproduce it.

| Field                    | Description                                              |
| ------------------------ | -------------------------------------------------------- |
| `source_id`              | Originating provider                                     |
| `station_id`             | Physical observation-station identifier, when applicable |
| `location_id`            | Internal project location identifier                     |
| `latitude`               | Source or requested latitude                             |
| `longitude`              | Source or requested longitude                            |
| `elevation_m`            | Station or model-point elevation                         |
| `observed_at`            | Time at which an observation was measured                |
| `forecast_generated_at`  | Time at which a forecast run was generated               |
| `forecast_valid_at`      | Time for which the forecast applies                      |
| `forecast_horizon_hours` | Difference between generation and valid time             |
| `ingested_at`            | Time at which the platform received the record           |
| `original_unit`          | Unit supplied by the source                              |
| `canonical_unit`         | Standardized project unit                                |
| `quality_status`         | Valid, suspicious, invalid or missing                    |
| `raw_record_id`          | Link to the original Bronze-layer payload                |
| `pipeline_version`       | Transformation version used to produce the record        |

Forecasts are never overwritten by newer forecasts: keeping both
`forecast_generated_at` and `forecast_valid_at` is what makes accuracy-by-horizon
measurable.

## Definitions

Every number on the site is exactly one of:

- **Observed**: measured by a physical station.
- **Forecast**: predicted by a weather model.
- **Modelled**: estimated by a regional environmental model.
- **Derived**: calculated by our pipeline.

## Initial analytical questions

1. How complete, timely, and valid is the collected data?
2. What is the daily temperature and humidity cycle at SKSM?
3. How do temperature, humidity, and wind combine to affect perceived heat?
4. How accurate are Open-Meteo temperature forecasts at 6–72 hour horizons?
5. Are forecast rainfall probabilities calibrated against observed rain?
6. How does the model interpret the city's data?
7. How does our forecast error compare to external weather services' errors?

## Goals

- Fetch meteorological data from multiple stations.
- Present it interactively, in a friendly and appealing way.
- Produce forecasts continuously, logging every forecast run historically so model
  accuracy, including revisions and fine-tunings, can be checked over time.
- Compare our accuracy against other weather services that expose an API
  (Weather.com, AccuWeather, ...).

## Non-goals

- Replacing existing weather sources (a welcome surprise, not a goal).
- Building or operating our own weather stations.
- Turning a profit (also a welcome surprise).

## Success metrics

The project succeeds when it reliably collects, processes, analyzes, and serves climate
information for the selected Santa Marta locations. Metrics span platform reliability,
data quality, forecast verification, ML performance, product usability, and
reproducibility.

### Initial vertical-slice metrics

| Area                 | Metric                                                   |                                     Initial target | Measurement                                                   |
| -------------------- | -------------------------------------------------------- | -------------------------------------------------: | ------------------------------------------------------------- |
| Data ingestion       | Successful scheduled ingestion runs                      |                                 ≥ 95% over 30 days | Successful runs divided by expected runs                      |
| Data freshness       | Observation ingestion delay                              | ≤ 15 minutes for METAR; source-dependent for IDEAM | Difference between source observation time and ingestion time |
| Availability         | Continuous collection period                             |                              ≥ 30 consecutive days | Days with at least one valid observation                      |
| Completeness         | Expected observations received                           |                      ≥ 90% for the primary station | Received reporting intervals divided by expected intervals    |
| Validity             | Records passing schema and range validation              |                                              ≥ 98% | Valid records divided by all ingested records                 |
| Duplication          | Duplicate logical observations                           |    < 0.5% before deduplication; 0% in curated data | Duplicate station-variable-timestamp records                  |
| Traceability         | Curated records linked to raw source data                |                                               100% | Records containing source, ingestion and lineage identifiers  |
| Pipeline reliability | Successful ETL executions                                |                                 ≥ 95% over 30 days | Successful ETL runs divided by scheduled runs                 |
| API reliability      | Successful API responses                                 |                      ≥ 99% during normal operation | Non-5xx responses divided by total requests                   |
| API performance      | Cached endpoint response time                            |                                   p95 below 500 ms | Application monitoring                                        |
| Reproducibility      | Environment can be started from repository documentation |                      Successful on a clean machine | Fresh-clone deployment test                                   |
| Visualization        | Reproducible analytical figures                          |                 At least 10 for the vertical slice | Figures regenerated from scripts or notebooks                 |
| Documentation        | Core datasets and transformations documented             |                          100% of production tables | Data dictionary and transformation documentation              |

### Data-quality metrics

Monitored independently for every station, variable, and source.

| Dimension        | Definition                                                                 |                         Target |
| ---------------- | -------------------------------------------------------------------------- | -----------------------------: |
| Completeness     | Percentage of expected values that are available                           | ≥ 90% for primary observations |
| Timeliness       | Percentage of records received within the expected delay                   |                          ≥ 90% |
| Validity         | Percentage of values within defined physical and schema constraints        |                          ≥ 98% |
| Uniqueness       | Percentage of records without duplicate logical keys                       | 100% in silver and gold layers |
| Consistency      | Percentage of records using standardized timestamps, units and identifiers | 100% in silver and gold layers |
| Lineage coverage | Percentage of transformed records traceable to an original payload         |                           100% |

A source that misses a quality target may stay available, but the application must show
its freshness and quality status, and never silently present stale data as current.

### Forecast-verification metrics

Forecasts are evaluated against observations at station coordinates. The initial goal
is a trustworthy baseline, not an immediate claim of superior forecasting.

| Forecast variable        | Primary metrics                                                   |
| ------------------------ | ----------------------------------------------------------------- |
| Temperature              | MAE, RMSE and mean bias                                           |
| Relative humidity        | MAE and mean bias                                                 |
| Wind speed               | MAE and RMSE                                                      |
| Rain occurrence          | Precision, recall, F1 score and Brier score                       |
| Rain probability         | Reliability curve and calibration error                           |
| General forecast quality | Performance by forecast horizon, month, location and source model |

First-release success: forecast errors computed automatically once observations arrive,
metrics segmented by horizon, baseline performance stored and versioned, and forecast
quality trackable over time.

### Machine-learning metrics

Every model is compared with a non-ML baseline. For temperature correction the
baselines are: the original numerical forecast, historical mean forecast bias, and a
simple linear correction.

A model may be promoted only if it:

1. Improves validation MAE over the uncorrected forecast.
2. Does not introduce substantially worse errors for any geographic location.
3. Is evaluated on a time-based test period not used during training.
4. Has its dataset version, features, parameters, and Git commit recorded in MLflow.
5. Can be reproduced from stored code and configuration.

Initial (exploratory, not guaranteed) target: **5–10% reduction in temperature MAE**
versus the original forecast. For rain-probability calibration: improve Brier score or
calibration error without unacceptable loss of event recall.

### Product metrics

The public service must make provenance and uncertainty understandable.

| Metric                                                     |                                                     Target |
| ---------------------------------------------------------- | ---------------------------------------------------------: |
| Values displaying source and timestamp                     |                                                       100% |
| Values labelled as observed, forecast, modelled or derived |                                                       100% |
| Core pages usable on mobile and desktop                    |                                                       100% |
| Core page load time                                        |                    Below 3 seconds under normal conditions |
| Accessibility audit                                        |             No critical automated accessibility violations |
| Source outage handling                                     | Site remains usable with a visible degraded-status message |
| Public methodology coverage                                |                  Every major variable and model documented |

Core user tasks, achievable without external documentation: view current conditions;
see when data was last updated; tell observed from modelled values; view the next 24 h
of forecast; compare forecast against observations; inspect historical trends.

### Engineering and reproducibility metrics

The platform can be rebuilt and safely changed:

- All application services are containerized; local development starts through
  documented commands.
- Infrastructure changes go through Terraform or versioned service configuration.
- Pull requests run automated linting, tests, and security checks.
- Database migrations are version controlled.
- Failed ingestion events are preserved for investigation.
- Historical transformations rerun without duplicate output.
- Production deployments map to a Git commit; secrets stay out of the repository.
- At least one complete recovery/replay procedure is documented and tested.

### Portfolio and learning metrics

This project also exists to build practical data and ML skills, so success includes
demonstrable ownership:

- One complete source-to-dashboard pipeline.
- One PySpark historical backfill and one Kafka + Spark Structured Streaming pipeline.
- One documented exploratory analysis with ten or more polished Matplotlib figures.
- One model tracked and registered in MLflow.
- Written explanations of data-cleaning and modelling decisions.
- A public architecture diagram, data dictionary, and project case study covering
  problems, trade-offs, and results.

AI-generated code counts as evidence of learning only if reviewed, tested, and
explainable by the author.

## MVP success definition

The first MVP is successful when:

1. At least one Santa Marta station has been collected continuously for 30 days.
2. At least 90% of expected primary observations were received.
3. Raw, bronze, silver, and gold datasets can be regenerated.
4. Open-Meteo forecasts are archived without overwriting previous runs.
5. Forecast error is calculated automatically when observations arrive.
6. A public API and website show current conditions, forecasts, timestamps, and sources.
7. At least ten reproducible Matplotlib visualizations are published.
8. The application deploys from version-controlled infrastructure and configuration.
9. Data-quality and service-health metrics are visible.
10. The repository documents enough for another developer to run the system locally.

## Known limitations

- No sensors or stations of our own; external stations must be trusted to be accurate.
- Free-tier API limits may constrain collection.
- Single maintainer: responses to incidents and upstream API changes may be slow.
