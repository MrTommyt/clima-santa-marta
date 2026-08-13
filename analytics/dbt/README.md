# dbt

Silver-to-gold SQL models. dbt owns the `staging` and `gold` schemas; it never
writes silver (transforms do) or reads bronze.

Layout:

- `models/staging/`: one view per source table. Column selection and the
  `quality_status = 'valid'` filter, nothing else. Lands in the `staging`
  schema. `stg_weather_observation` is the worked example; the other source
  tables follow the same pattern as needed.
- `models/marts/`: the business-facing gold models the API and site read
  (current conditions, daily summaries, forecast verification). Built from
  staging via `{{ ref('...') }}`, land in `gold`.

Workflow:

```bash
make dbt-run      # build all models
make dbt-test     # run schema tests
make dbt-docs     # generate docs + lineage graph (target/index.html)
```
