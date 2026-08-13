SELECT
    id AS run_id,
    source_id,
    dataset,
    window_start,
    window_end,
    started_at,
    finished_at,
    status,
    records_upserted
FROM {{ source('metadata', 'ingestion_run') }}
