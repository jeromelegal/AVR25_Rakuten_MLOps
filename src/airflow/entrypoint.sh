#!/bin/bash
set -e

echo "Starting entrypoint script..."

export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow_user:airflow_user_password@postgresql:5432/airflow?sslmode=verify-full&sslcert=/etc/ssl/airflow/postgresql_airflow.crt&sslkey=/etc/ssl/airflow/postgresql_airflow.key&sslrootcert=/etc/ssl/airflow/postgresql_airflow_ca.crt"
export AIRFLOW__DATABASE__SQL_ALCHEMY_SCHEMA="$POSTGRESQL_AIRFLOW_SCHEMA"

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
tail -f /dev/null
echo "EXEC AIRFLOW db migrate..."
airflow db migrate
echo "EXEC AIRFLOW db check..."
airflow db check
echo "EXEC AIRFLOW scheduler..."
airflow scheduler &
jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
