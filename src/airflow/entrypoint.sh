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

if [ -n "$AIRFLOW__API__SECRET_KEY" ]; then
    echo "Using Airflow API secret key from environment variable."
else
    echo "Using Vault key to retrieve Airflow API secret key."
    export AIRFLOW__API__SECRET_KEY=$(cat $AIRFLOW_INTERNAL_SECRET_KEY_PATH)
fi

echo "------------ $AIRFLOW__API__SECRET_KEY ---------------"

echo "$POSTGRESQL_AIRFLOW_SCHEMA"
echo "EXEC AIRFLOW db migrate..."
airflow db migrate

echo "EXEC AIRFLOW API server..."
airflow api-server -p 8795 > api-server.log &

tail -f /dev/null 

echo "EXEC AIRFLOW scheduler..."
airflow scheduler > scheduler.log & 

echo "EXEC AIRFLOW dag-processor..."
airflow dag-processor > dag-processor.log &


echo "EXEC AIRFLOW triggerer..."
airflow triggerer > triggerer.log &


jobs

#nginx-fcgiwrap.sh

#nginx-conf.sh

fg %1
