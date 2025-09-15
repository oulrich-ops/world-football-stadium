#!/bin/bash
set -e

# Installer les dépendances
if [ -e "/opt/airflow/requirements.txt" ]; then
    pip install --no-cache-dir -r /opt/airflow/requirements.txt
fi

exec airflow standalone