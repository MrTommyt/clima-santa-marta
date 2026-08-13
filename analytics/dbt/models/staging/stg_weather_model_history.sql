SELECT
    location_id,
    source_id,
    forecast_model,
    valid_at,
    variable,
    value,
    unit
FROM {{ source('silver', 'weather_model_history') }}
WHERE quality_status = 'valid'
