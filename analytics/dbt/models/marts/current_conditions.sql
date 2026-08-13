WITH observations AS (
    SELECT
        station_id,
        source_id,
        observed_at,
        variable,
        value
    FROM {{ ref('stg_weather_observation') }}
),
latest AS (
    SELECT
        station_id,
        source_id,
        MAX(observed_at) AS observed_at
    FROM observations
    GROUP BY station_id, source_id
),
pivoted AS (
    SELECT
        o.station_id,
        o.source_id,
        o.observed_at,
        {{ fetch_value('air_temperature_2m') }},
        {{ fetch_value('dew_point_2m') }},
        {{ fetch_value('wind_speed_10m') }},
        {{ fetch_value('wind_direction_10m') }},
        {{ fetch_value('wind_gust_10m') }},
        {{ fetch_value('surface_pressure') }},
        {{ fetch_value('visibility') }},
        {{ fetch_value('cloud_cover') }}
    FROM observations AS o
    INNER JOIN latest USING (station_id, source_id, observed_at)
    GROUP BY o.station_id, o.source_id, o.observed_at
)
SELECT
    p.station_id,
    st.icao_code,
    l.slug AS location_slug,
    l.name AS location_name,
    l.latitude,
    l.longitude,
    s.code AS source_code,
    p.observed_at,
    p.air_temperature_2m,
    p.dew_point_2m,
    p.wind_speed_10m,
    p.wind_direction_10m,
    p.wind_gust_10m,
    p.surface_pressure,
    p.visibility,
    p.cloud_cover
FROM pivoted AS p
INNER JOIN {{ ref('stg_station') }} AS st USING (station_id)
INNER JOIN {{ ref('stg_location') }} AS l USING (location_id)
INNER JOIN {{ ref('stg_source') }} AS s ON s.source_id = p.source_id
