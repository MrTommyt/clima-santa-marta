SELECT
    id AS source_id,
    code,
    name
FROM {{ source('metadata', 'source') }}
