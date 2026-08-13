from airflow.sdk import dag, task


@dag(schedule="0 2 * * *", catchup=False, max_active_runs=1, tags=["transformation"])
def dbt_build():
    @task(retries=1)
    def build() -> None:
        import subprocess

        dirs = ["--project-dir", "/opt/clima/dbt", "--profiles-dir", "/opt/clima/dbt"]
        subprocess.run(["dbt", "run", *dirs], check=True)
        subprocess.run(["dbt", "test", *dirs], check=True)

    build()


dbt_build()
