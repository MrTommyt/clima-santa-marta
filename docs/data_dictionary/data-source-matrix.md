# Data-source matrix

One row represents one endpoint or dataset integrated into the platform. The cadence column describes how often the project plans to fetch the source, not necessarily how often the provider produces new data.

| Source     | Endpoint / dataset                     | Variables                                                                                                                         | Cadence                  | License / terms                                                                                            | Rate limits                                                                  | Milestone |
| ---------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------- |
| Open-Meteo | `/v1/forecast`                         | Temperature, apparent temperature, humidity, precipitation, rain probability, wind, gusts, pressure, cloud cover and weather code | Hourly                   | Free API for non-commercial use under CC BY 4.0; attribution required                                      | 10,000 calls/day, 5,000/hour and 600/minute on the free API                  | 2         |
| Open-Meteo | `/v1/marine`                           | Wave height, wave direction, wave period, swell and sea-surface temperature                                                       | Every 3 hours            | Same Open-Meteo free API terms; marine values are modelled and must not replace official maritime warnings | Same Open-Meteo free API limits                                              | 6         |
| Open-Meteo | `/v1/air-quality`                      | PM2.5, PM10, ozone, nitrogen dioxide, dust and UV index                                                                           | Every 3 hours            | Same Open-Meteo free API terms; values are regional model estimates, not local sensor readings             | Same Open-Meteo free API limits                                              | 6         |
| SKSM METAR | `/api/data/metar?ids=SKSM&format=json` | Temperature, dew point, wind, visibility, pressure, clouds and reported weather                                                   | Every 10 minutes         | Public Aviation Weather API; follow its usage rules and identify the client with a custom user agent       | 100 requests/minute; no more than one request/minute per thread              | 2         |
| IDEAM      | Station catalogue `hp9r-jxuu`          | Station code, name, status, location, altitude and sensor type                                                                    | Daily                    | Colombian open data; reuse is allowed, but IDEAM warns that records may contain delays or errors           | Use a Socrata app token; abusive traffic may be throttled                    | 6         |
| IDEAM      | Air temperature `sbwg-7ju4`            | Station, timestamp, observed temperature, unit and location                                                                       | Daily incremental import | Colombian open data; additional validation is required before technical or sensitive use                   | Use filtered and paginated Socrata queries with an app token                 | 6         |
| IDEAM      | Precipitation `s54a-sgyg`              | Station, timestamp, precipitation, unit and location                                                                              | Daily incremental import | Colombian open data; measurements have basic quality control but may still require validation              | Use filtered and paginated Socrata queries with an app token                 | 6         |
| NASA POWER | `/api/temporal/daily/point`            | Temperature, humidity, precipitation, wind and solar radiation                                                                    | Monthly backfill         | Free global data; cite NASA POWER and record the API version and access date                               | No fixed public request quota; excessive synchronous requests may be blocked | 6         |

Open-Meteo’s forecast API supports hourly forecasts for coordinates, while its free non-commercial tier currently uses CC BY 4.0 and the limits listed above.

The Aviation Weather API provides worldwide METAR data and currently limits clients to 100 requests per minute, with each endpoint used no more than once per minute per thread.

IDEAM’s catalogue is updated daily. Its temperature dataset contains hourly station readings, while its precipitation dataset contains measurements recorded every ten minutes. IDEAM also warns that records may arrive late, contain sensor errors or require additional validation.

NASA POWER provides daily point data from 1981 to near real time. Recent meteorological values can later be replaced by improved climate-quality products, so backfills should support updates rather than treating every downloaded value as permanent.

## Evaluation notes

### Open-Meteo

Open-Meteo is the initial forecast provider because it offers weather, marine and air-quality data through similar JSON APIs. It is easy to query for several Santa Marta locations and does not require an API key for the free non-commercial service.

The data is modelled rather than directly observed. Every stored forecast must therefore include:

* The requested location
* The time the forecast was collected
* The time the forecast applies to
* The timezone
* The selected model, when available

Forecasts must never be stored only as “the latest forecast,” because that would prevent later accuracy analysis.

**Evaluation status:** Approved for initial integration.

### SKSM METAR

The SKSM METAR feed provides observed conditions from Simón Bolívar International Airport. It gives the project a local observation source for comparing forecasts against real measurements.

METAR reports use UTC and may contain missing fields when a condition was not measured or reported. The API only exposes a limited recent history, so the platform must retain every collected report in raw storage. The service may also return a valid response with no data, which should not be treated as a pipeline failure.

**Evaluation status:** Approved as the main observation source for Milestone 2.

### IDEAM

IDEAM provides the most relevant official Colombian station data. The station catalogue will first be used to identify active stations in Santa Marta and nearby parts of Magdalena. Temperature and precipitation will then be requested only for the selected station codes and for records newer than the last successful import.

The datasets are large, so full downloads should be avoided. Queries must use:

* Station filters
* Timestamp filters
* Pagination
* Stable ordering
* A Socrata application token

Socrata recommends application tokens because anonymous requests share lower throttling limits. Requests using a token receive a separate request pool, although abusive usage may still be limited.

IDEAM explicitly warns about delayed transmissions, station outages, unusual values and raw sensor errors. The ingestion pipeline must preserve these records, while the silver layer applies quality flags rather than silently deleting inconvenient measurements.

San Lorenzo (WIGOS `0-170-0-15015060`): OSCAR/Surface lists the station as silent/non-reporting as of August 2026, and the PRD and OSCAR coordinates disagree by roughly 5 km. Verify against the IDEAM catalogue before integrating it or seeding its location and station rows.

**Evaluation status:** Approved, pending confirmation of which nearby stations provide consistent recent data.

### NASA POWER

NASA POWER will provide long-term regional climate and solar data. It is useful for monthly summaries, historical comparisons and broad climate patterns.

It is not suitable for neighborhood-level current conditions. Meteorological data has coarse spatial resolution, and recent values usually arrive with a delay of several days. Recent provisional records may also be replaced after improved products become available.

The pipeline should therefore store the retrieval date and allow previously loaded periods to be refreshed. Published results must credit NASA POWER and record the service version used.

**Evaluation status:** Approved for historical and regional analysis, not real-time conditions.

## Review process

After each source has run for at least seven days, update its evaluation notes with:

* Successful request rate
* Average update delay
* Missing-data frequency
* Unexpected schema changes
* Station or variable availability
* Final polling cadence
* Decision to retain, replace or remove the source

This matrix should describe the sources the project actually uses. An endpoint that was considered but never integrated belongs in an architecture decision record, not in this table pretending it has a job.
