from airflow.sdk import dag, task


@dag(
    schedule="@daily", catchup=False, max_active_runs=1, tags=["ingestion", "prefetch"]
)
def openmeteo_historical_fetch():
    @task(retries=3)
    def capture() -> None:
        from clima_shared.runtime import load_source_config, run_prefetch
        from ingestion_openmeteo.adapter import OpenMeteoHistoricalAdapter

        source_config = load_source_config("openmeteo_historical")
        adapter = OpenMeteoHistoricalAdapter(source_config)
        run_prefetch(adapter)

    capture()


@dag(schedule="0 0/4 * * *", catchup=False, max_active_runs=1, tags=["ingestion"])
def openmeteo_forecast_fetch():
    @task(retries=3)
    def capture() -> None:
        from clima_shared.runtime import load_source_config, run_prefetch
        from ingestion_openmeteo.adapter import OpenMeteoHistoricalAdapter

        source_config = load_source_config("openmeteo_forecast")
        adapter = OpenMeteoHistoricalAdapter(source_config)
        run_prefetch(adapter)

    capture()


openmeteo_historical_fetch()
openmeteo_forecast_fetch()
