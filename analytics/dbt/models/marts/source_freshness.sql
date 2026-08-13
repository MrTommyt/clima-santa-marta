WITH runs AS (
    SELECT
        source_id,
        dataset,
        MAX(finished_at) AS last_run_at,
        MAX(finished_at) FILTER (WHERE status = 'finished') AS last_success_at
    FROM {{ ref('stg_ingestion_run') }}
    GROUP BY source_id, dataset
),
data_recency AS (
    SELECT source_id, 'observations' AS dataset, MAX(observed_at) AS latest_data_at
    FROM {{ ref('stg_weather_observation') }}
    GROUP BY source_id

    UNION ALL

    SELECT source_id, 'forecast', MAX(forecast_generated_at)
    FROM {{ ref('stg_weather_forecast') }}
    GROUP BY source_id

    UNION ALL

    SELECT source_id, 'historical_forecast', MAX(valid_at)
    FROM {{ ref('stg_weather_model_history') }}
    GROUP BY source_id
)
SELECT
    s.code AS source_code,
    r.dataset,
    r.last_run_at,
    r.last_success_at,
    r.last_run_at = r.last_success_at AS last_run_succeeded,
    d.latest_data_at,
    ROUND(EXTRACT(EPOCH FROM NOW() - r.last_success_at) / 60) AS minutes_since_success,
    ROUND(EXTRACT(EPOCH FROM NOW() - d.latest_data_at) / 60) AS minutes_since_data
FROM runs AS r
INNER JOIN {{ ref('stg_source') }} AS s USING (source_id)
LEFT JOIN data_recency AS d USING (source_id, dataset)
