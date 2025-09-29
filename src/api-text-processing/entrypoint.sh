#!/bin/bash
# Check if MLFlow service is up
echo "Checking if MLFlow service is up..."
HEALTH_URL=$MLFLOW_ADDR/health
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for MLFlow service to be healthy."
    sleep 1
done
echo "MLFlow service is up"

# Keep it here not to have any issue with the Python package installation
export AWS_ACCESS_KEY_ID=${MINIO_API_TEXT_PROCESSING_USER}
export AWS_SECRET_ACCESS_KEY=${MINIO_API_TEXT_PROCESSING_PASSWORD}
export AWS_CA_BUNDLE=${MINIO_API_TEXT_PROCESSING_CA_PATH}
# export REQUESTS_CA_BUNDLE=${API_IMAGE_TEXT_PROCESSING_PEM_PATH}
export MLFLOW_S3_ENDPOINT_URL=https://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}

echo "ENVIRONMENT: $ENVIRONMENT"
if [[ "$ENVIRONMENT" == "test" ]]; then
    echo "Staring tests..."
    pip install --break-system-packages -r requirements/dev.txt
    exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT &

    test.sh
else
    echo "Staring production application..."
    vault.sh

    set -m

    exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT --ssl-keyfile $API_TEXT_PROCESSING_KEY_PATH --ssl-certfile $API_TEXT_PROCESSING_CERT_PATH  --ssl-ca-certs $API_TEXT_PROCESSING_CA_PATH --ssl-cert-reqs 2 &


    jobs

    nginx-fcgiwrap.sh

    nginx-conf.sh

    fg %1

fi

