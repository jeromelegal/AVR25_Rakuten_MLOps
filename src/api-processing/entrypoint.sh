#!/bin/bash
# Check if text API service is up
echo "Checking if text API service is up..."
HEALTH_URL=http://$API_TEXT_PROCESSING_SERVICE_NAME:$API_TEXT_PROCESSING_SERVICE_PORT/
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for text API service to be healthy."
    sleep 1
done
echo "Text API service is up"

# Check if image API service is up
echo "Checking if image API service is up..."
HEALTH_URL=http://$API_IMAGE_PROCESSING_SERVICE_NAME:$API_IMAGE_PROCESSING_SERVICE_PORT/
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for image API service to be healthy."
    sleep 1
done
echo "Image API service is up"

echo "Setting up vault..."
vault.sh
echo "Vault is setup!"

echo "Staring production application..."
set -m
exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT --ssl-keyfile $API_PROCESSING_KEY_PATH --ssl-certfile $API_PROCESSING_CERT_PATH  --ssl-ca-certs $API_PROCESSING_CA_PATH --ssl-cert-reqs 2 &

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
