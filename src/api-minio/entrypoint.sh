#!/bin/bash
# Check if Minio service is up
echo "Checking if Minio service is up..."
HEALTH_URL=http://$MINIO_SERVICE_NAME:$MINIO_SERVICE_PORT/minio/health/live
echo "HEALTH_URL: $HEALTH_URL"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done
echo "Minio service is up"

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

    exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT --ssl-keyfile $API_MINIO_KEY_PATH --ssl-certfile $API_MINIO_CERT_PATH  --ssl-ca-certs $API_MINIO_CA_PATH --ssl-cert-reqs 2 &


    jobs

    nginx-fcgiwrap.sh

    nginx-conf.sh

    fg %1

fi

