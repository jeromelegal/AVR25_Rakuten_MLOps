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

# \"host=postgresql port=5432 user=$POSTGRESQL_MLFLOW_USER password=$POSTGRESQL_MLFLOW_PASSWORD dbname=$POSTGRESQL_MLFLOW_DATABASE sslmode=verify-full sslcert=$POSTGRESQL_MLFLOW_CERT_PATH sslkey=$POSTGRESQL_MLFLOW_KEY_PATH sslrootcert=$POSTGRESQL_MLFLOW_CA_PATH\""

# Generate backend URI using DSN
qs=$(python3 -c "import urllib.parse; \
params = { \
    \"host\": \"${POSTGRESQL_SERVICE_NAME}\", \
    \"port\": \"${POSTGRESQL_SERVICE_PORT}\", \
    \"user\": \"${POSTGRESQL_MLFLOW_USER}\", \
    \"password\": \"${POSTGRESQL_MLFLOW_PASSWORD}\", \
    \"dbname\": \"${POSTGRESQL_MLFLOW_DATABASE}\", \
    \"sslmode\": \"verify-full\", \
    \"sslcert\": \"${POSTGRESQL_MLFLOW_CERT_PATH}\", \
    \"sslkey\": \"${POSTGRESQL_MLFLOW_KEY_PATH}\", \
    \"sslrootcert\": \"${POSTGRESQL_MLFLOW_CA_PATH}\", \
}; \
print(urllib.parse.urlencode(params))" \
)
BACKEND_DSN="postgresql+psycopg:///?${qs}"

su mlflow -c "mlflow server \
    --host 0.0.0.0 \
    --port $SERVICE_PORT \
    --default-artifact-root \"s3://${MINIO_DEFAULT_MLFLOW_ARTIFACT_BUCKET}/\" \
    --backend-store-uri '${BACKEND_DSN}' \
    --serve-artifacts \
    --uvicorn-opts \"--ssl-keyfile $MLFLOW_KEY_PATH --ssl-certfile $MLFLOW_CERT_PATH\"" &

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1