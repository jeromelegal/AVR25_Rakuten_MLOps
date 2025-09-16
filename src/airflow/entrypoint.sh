#!/bin/bash
set -e

echo "Starting entrypoint script..."
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow_user:airflow_user_password@postgresql:5432/airflow_db"

#HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$AIRFLOW_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
# until [ $HTTP_CODE -eq 200 ]; do
#     HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$AIRFLOW_SERVICE_NAME/health)
#     echo "Waiting for Airflow service to be healthy."
#     sleep 1
# done

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

echo "EXEC AIRFLOW db migrate..."
exec airflow db migrate
echo "EXEC AIRFLOW db init..."
exec airflow db init
echo "EXEC AIRFLOW scheduler..."
exec airflow scheduler
jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1