from airflow.sdk import dag, task


@dag(schedule="*/10 * * * *", catchup=False, max_active_runs=1, tags=["ingestion"])
def metar_fetch():
    @task(retries=2)
    def capture() -> None:
        # Imported inside the task so a stale container image breaks the run
        # (visibly, with retries) instead of breaking DAG parsing.
        from clima_shared.runtime import load_source_config, run_prefetch
        from ingestion_metar.adapter import MetarObservationsAdapter

        adapter = MetarObservationsAdapter(load_source_config("metar_observations"))
        run_prefetch(adapter)

    capture()


metar_fetch()
