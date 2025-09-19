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

echo "--- ---- AIRFLOW create user admin:admin ---- ---"
[ ! -f /opt/airflow/simple_auth_manager_passwords.json.generated ] && echo '{"admin": "admin"}' > /opt/airflow/simple_auth_manager_passwords.json.generated

echo " --- ---- AIRFLOW connection MINIO... ---- ---"
# airflow connections add 'minio_s3' \
#     --conn-type 'generic' \
#     --conn-extra '{"host": "http://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}", "aws_access_key_id": "${MINIO_AIRFLOW_USER}", "aws_secret_access_key": "${MINIO_AIRFLOW_PASSWORD}", "verify": "${MINIO_AIRFLOW_CA_PATH}"}'

# if ! airflow connections get 'minio_s3' > /dev/null 2>&1; then
#     airflow connections add 'minio_s3' \
#         --conn-type 'generic' \
#         --conn-extra '{"host": "http://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}", "aws_access_key_id": "${MINIO_AIRFLOW_USER}", "aws_secret_access_key": "${MINIO_AIRFLOW_PASSWORD}", "verify": "${MINIO_AIRFLOW_CA_PATH}"}'
# else
#     echo "Connection minio_s3 already exists, skipping add."
# fi

airflow connections delete minio_s3
airflow connections add 'minio_s3' \
    --conn-type 'aws' \
    --conn-extra '{"host": "http://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}", 
                    "aws_access_key_id": "${MINIO_AIRFLOW_USER}", 
                    "aws_secret_access_key": "${MINIO_AIRFLOW_PASSWORD}", 
                    "verify": "${MINIO_AIRFLOW_CA_PATH}"}'

echo "EXEC AIRFLOW API server..."
airflow api-server -p 8795 &


echo "EXEC AIRFLOW scheduler..."
airflow scheduler &

echo "EXEC AIRFLOW dag-processor..."
airflow dag-processor &

echo "EXEC AIRFLOW triggerer..."
airflow triggerer &
tail -f /dev/null

jobs

#nginx-fcgiwrap.sh

#nginx-conf.sh

fg %1
