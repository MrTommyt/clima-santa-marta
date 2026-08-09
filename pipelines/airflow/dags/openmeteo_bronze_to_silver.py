from airflow.sdk import dag, task


@dag(schedule="@daily", catchup=False, max_active_runs=1, tags=["transformation"])
def openmeteo_bronze_to_silver_mapping():
    @task(retries=2)
    def transform():
        from clima_transforms.openmeteo_forecast import run

        run(window_hours=48)

    transform()


openmeteo_bronze_to_silver_mapping()


@dag(schedule="@daily", catchup=False, max_active_runs=1, tags=["transformation"])
def openmeteo_history_to_silver_mapping():
    @task(retries=2)
    def transform():
        from clima_transforms.openmeteo_history import run

        run(window_hours=48)

    transform()


openmeteo_history_to_silver_mapping()
