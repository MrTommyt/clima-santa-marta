SELECT
    location_id,
    source_id,
    forecast_model,
    forecast_generated_at,
    forecast_valid_at,
    (EXTRACT(EPOCH FROM forecast_valid_at - forecast_generated_at) / 3600)::int
        AS forecast_horizon_hours,
    variable,
    value,
    unit
FROM {{ source('silver', 'weather_forecast') }}
WHERE quality_status = 'valid'
