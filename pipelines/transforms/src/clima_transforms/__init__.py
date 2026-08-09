"""Bronze-to-silver transforms. Each source gets one module; Airflow DAG
tasks call the module's run() with a reprocessing window."""
