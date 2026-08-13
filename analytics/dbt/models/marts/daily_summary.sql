WITH observed AS (

    SELECT
        st.location_id,
        o.variable,
        o.value,
        o.observed_at AS valid_at,
        'observed' AS data_kind
    FROM {{ ref('stg_weather_observation') }} AS o
    INNER JOIN {{ ref('stg_station') }} AS st USING (station_id)
),
modelled AS (

    SELECT
        location_id,
        variable,
        value,
        valid_at,
        'modelled' AS data_kind
    FROM {{ ref('stg_weather_model_history') }}
),
unioned AS (

    SELECT * FROM observed
    UNION ALL
    SELECT * FROM modelled
),
daily AS (

    SELECT
        location_id,
        data_kind,
        (valid_at AT TIME ZONE 'America/Bogota')::date AS day,
        MIN(value) FILTER (WHERE variable = 'air_temperature_2m') AS temperature_min,
        MAX(value) FILTER (WHERE variable = 'air_temperature_2m') AS temperature_max,
        AVG(value) FILTER (WHERE variable = 'air_temperature_2m') AS temperature_mean,
        SUM(value) FILTER (WHERE variable = 'precipitation') AS precipitation_total,
        AVG(value) FILTER (WHERE variable = 'relative_humidity_2m') AS humidity_mean,
        AVG(value) FILTER (WHERE variable = 'wind_speed_10m') AS wind_speed_mean,
        MAX(value) FILTER (WHERE variable = 'wind_gust_10m') AS wind_gust_max,
        COUNT(*) AS sample_count
    FROM unioned
    GROUP BY location_id, data_kind, (valid_at AT TIME ZONE 'America/Bogota')::date
)
SELECT
    d.location_id,
    l.slug AS location_slug,
    l.name AS location_name,
    d.day,
    d.data_kind,
    d.temperature_min,
    d.temperature_max,
    d.temperature_mean,
    d.precipitation_total,
    d.humidity_mean,
    d.wind_speed_mean,
    d.wind_gust_max,
    d.sample_count
FROM daily AS d
INNER JOIN {{ ref('stg_location') }} AS l USING (location_id)
