#!/bin/bash

# Lauch Minio server
echo "Starting Minio server..."
minio server /data --address ":$PORT" --console-address ":$GUI_PORT" &
HEALTH_URL=http://127.0.0.1:$PORT/minio/health/live
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done
echo "Minio server started"

# Define alias for the following commands
ALIAS="myminio"
HOSTNAME="http://127.0.0.1:$PORT"

bash +o history
mc alias set $ALIAS $HOSTNAME $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
bash -o history
echo "Minio alias configured"

# Exit if there is an error code when checking connection to the server
echo "Checking Minio connection..."
mc admin info "$ALIAS"
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "Failed to retrieve MinIO admin info for alias '$ALIAS'"
    exit $STATUS
fi
echo "Minio connection OK"

# Generate bucket and exit if not possible
echo "Creating Minio buckets..."
declare -a arr=("raw-images" "processed-images" "models" "ci-results" "results" "train-images" "test-images")
for i in "${arr[@]}"
do
    echo "$i"
    mc mb --ignore-existing --region "eu-central-1" /data/$i
    STATUS=$?
    if [ $STATUS -ne 0 ]; then
        echo "Failed to create Minio bucket '$i'"
        exit $STATUS
    fi
done

echo "Minio bucket OK"
