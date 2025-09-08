#!/bin/bash
# Check if API Minio service is up
echo "Checking if API Minio service is up..."
HEALTH_URL=http://$API_TEXT_PROCESSING_API_IMAGE_PROCESSING_SERVICE_NAME:$API_TEXT_PROCESSING_API_IMAGE_PROCESSING_SERVICE_PORT/
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done
echo "API Minio service is up"

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

    exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT --ssl-keyfile $API_IMAGE_PROCESSING_KEY_PATH --ssl-certfile $API_IMAGE_PROCESSING_CERT_PATH  --ssl-ca-certs $API_IMAGE_PROCESSING_CA_PATH --ssl-cert-reqs 2 &


    jobs

    nginx-fcgiwrap.sh

    nginx-conf.sh

    fg %1

fi

