SELECT
    id AS location_id,
    slug,
    name,
    latitude,
    longitude,
    elevation_m
FROM {{ source('metadata', 'location') }}
