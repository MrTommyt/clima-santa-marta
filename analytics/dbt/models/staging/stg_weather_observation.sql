SELECT
    station_id,
    source_id,
    observed_at,
    variable,
    value,
    unit
FROM {{ source('silver', 'weather_observation') }}
WHERE quality_status = 'valid'
