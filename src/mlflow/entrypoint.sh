#!/bin/bash

# Check if PostGreSQL API service is up
echo "Checking if PostGreSQL API service is up..."
HEALTH_URL=https://$POSTGRESQL_SERVICE_NAME/health
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for PostGreSQL API service to be healthy."
    sleep 1
done
echo "PostGreSQL API service is up"

# Check if Minio API service is up
echo "Checking if Minio API service is up..."
HEALTH_URL=https://$MINIO_SERVICE_NAME/health
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for Minio API service to be healthy."
    sleep 1
done
echo "Minio API service is up"

vault.sh

set -m

export MLFLOW_TRACKING_URI=postgresql+psycopg://$POSTGRESQL_MLFLOW_USER:$POSTGRESQL_MLFLOW_PASSWORD@$POSTGRESQL_SERVICE_NAME:$POSTGRESQL_SERVICE_PORT/$POSTGRESQL_MLFLOW_DATABASE
export MLFLOW_S3_ENDPOINT_URL=https://$MINIO_SERVICE_NAME:$MINIO_SERVICE_PORT
export AWS_ACCESS_KEY_ID=$MINIO_MLFLOW_USER
export AWS_SECRET_ACCESS_KEY=$MINIO_MLFLOW_PASSWORD

mlflow server \
    --host 0.0.0.0 \
    --port $SERVICE_PORT \
    --default-artifact-root ./artifacts \
    --backend-store-uri $MLFLOW_TRACKING_URI \
    --serve-artifacts \
    --gunicorn-opts "--keyfile $MLFLOW_KEY_PATH --certfile $MLFLOW_CERT_PATH"

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1