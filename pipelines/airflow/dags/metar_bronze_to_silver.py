from airflow.sdk import dag, task


@dag(schedule="@daily", catchup=False, max_active_runs=1, tags=["transformation"])
def metar_bronze_to_silver_mapping():
    @task(retries=2)
    def transform():
        from clima_transforms.metar import run

        run(window_hours=48)

    transform()


metar_bronze_to_silver_mapping()
