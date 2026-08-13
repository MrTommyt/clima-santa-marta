WITH forecasts AS (
    SELECT *
    FROM {{ ref('stg_weather_forecast') }}
    WHERE forecast_horizon_hours >= 0
),
latest_run AS (
    SELECT
        location_id,
        source_id,
        forecast_model,
        MAX(forecast_generated_at) AS forecast_generated_at
    FROM forecasts
    GROUP BY location_id, source_id, forecast_model
),
pivoted AS (
    SELECT
        f.location_id,
        f.source_id,
        f.forecast_model,
        f.forecast_generated_at,
        f.forecast_valid_at,
        f.forecast_horizon_hours,
        {{ fetch_value('air_temperature_2m') }},
        {{ fetch_value('apparent_temperature') }},
        {{ fetch_value('dew_point_2m') }},
        {{ fetch_value('relative_humidity_2m') }},
        {{ fetch_value('precipitation') }},
        {{ fetch_value('precipitation_probability') }},
        {{ fetch_value('wind_speed_10m') }},
        {{ fetch_value('wind_direction_10m') }},
        {{ fetch_value('wind_gust_10m') }},
        {{ fetch_value('surface_pressure') }},
        {{ fetch_value('cloud_cover') }}
    FROM forecasts AS f
    INNER JOIN latest_run
        USING (location_id, source_id, forecast_model, forecast_generated_at)
    GROUP BY
        f.location_id,
        f.source_id,
        f.forecast_model,
        f.forecast_generated_at,
        f.forecast_valid_at,
        f.forecast_horizon_hours
)
SELECT
    p.location_id,
    l.slug AS location_slug,
    l.name AS location_name,
    s.code AS source_code,
    p.forecast_model,
    p.forecast_generated_at,
    p.forecast_valid_at,
    p.forecast_horizon_hours,
    p.air_temperature_2m,
    p.apparent_temperature,
    p.dew_point_2m,
    p.relative_humidity_2m,
    p.precipitation,
    p.precipitation_probability,
    p.wind_speed_10m,
    p.wind_direction_10m,
    p.wind_gust_10m,
    p.surface_pressure,
    p.cloud_cover
FROM pivoted AS p
INNER JOIN {{ ref('stg_location') }} AS l USING (location_id)
INNER JOIN {{ ref('stg_source') }} AS s ON s.source_id = p.source_id
