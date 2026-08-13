SELECT
    id AS station_id,
    location_id,
    icao_code,
    wigos_id,
    ideam_code
FROM {{ source('metadata', 'station') }}
