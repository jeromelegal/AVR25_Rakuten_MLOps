#!/bin/bash
set -e

echo "Starting entrypoint script..."

HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$POSTGRESQL_SERVICE_NAME/health)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$POSTGRESQL_SERVICE_NAME/health)
    echo "Waiting for PostgreSQL service to be healthy."
    sleep 1
done

echo "Call vault.sh to retrieve certificates and private key..."
# Appeler le script Vault pour récupérer les certificats et la clé privée
vault.sh

set -m
# su - postgresql -c "mlflow server \
#     --backend-store-uri sqlite:///mlflow.db \
#     --default-artifact-root ./artifacts \
#     --host 0.0.0.0 \
#     --port $SERVICE_PORT \
#     --serve-artifacts \
#     --gunicorn-opts "--keyfile /path/to/private.key --certfile /path/to/certificate.crt" &
echo "$POSTGRESQL_AIRFLOW_SCHEMA"
echo "EXEC AIRFLOW db migrate..."
airflow db migrate
echo "EXEC AIRFLOW scheduler..."
airflow scheduler

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
