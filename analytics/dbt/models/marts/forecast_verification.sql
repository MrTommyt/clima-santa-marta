WITH observations AS (
    SELECT
        st.location_id,
        o.variable,
        DATE_TRUNC('hour', o.observed_at) AS valid_hour,
        AVG(o.value) AS observed_value
    FROM {{ ref('stg_weather_observation') }} AS o
    INNER JOIN {{ ref('stg_station') }} AS st USING (station_id)
    GROUP BY st.location_id, o.variable, DATE_TRUNC('hour', o.observed_at)

),
forecasts AS (
    SELECT
        location_id,
        source_id,
        forecast_model,
        variable,
        forecast_generated_at,
        forecast_valid_at,
        forecast_horizon_hours,
        value AS forecast_value
    FROM {{ ref('stg_weather_forecast') }}
    WHERE forecast_horizon_hours >= 0
)
SELECT
    f.location_id,
    l.slug AS location_slug,
    s.code AS source_code,
    f.forecast_model,
    f.variable,
    f.forecast_generated_at,
    f.forecast_valid_at,
    f.forecast_horizon_hours,
    f.forecast_value,
    o.observed_value,
    f.forecast_value - o.observed_value AS forecast_error,
    ABS(f.forecast_value - o.observed_value) AS forecast_absolute_error
FROM forecasts AS f
INNER JOIN observations AS o
    ON o.location_id = f.location_id
    AND o.variable = f.variable
    AND o.valid_hour = f.forecast_valid_at
INNER JOIN {{ ref('stg_location') }} AS l ON l.location_id = f.location_id
INNER JOIN {{ ref('stg_source') }} AS s ON s.source_id = f.source_id
