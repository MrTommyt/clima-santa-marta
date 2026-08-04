# Airflow

DAGs live in `dags/`, which compose mounts read-only into the Airflow container at
`/opt/airflow/dags`. Real DAGs arrive with the ETL milestones; local Airflow runs as a
single `airflow standalone` container (see `compose.yaml`).
