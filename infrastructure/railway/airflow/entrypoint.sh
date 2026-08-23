#!/usr/bin/env bash
# The simple auth manager regenerates the admin password on every start unless
# the passwords file already exists. Write it from AIRFLOW_ADMIN_PASSWORD so
# the login stays stable across redeploys.
set -euo pipefail

if [[ -n "${AIRFLOW_ADMIN_PASSWORD:-}" ]]; then
    printf '{"admin": "%s"}\n' "${AIRFLOW_ADMIN_PASSWORD}" \
        > "${AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE:-/opt/airflow/passwords.json}"
fi

exec airflow standalone
