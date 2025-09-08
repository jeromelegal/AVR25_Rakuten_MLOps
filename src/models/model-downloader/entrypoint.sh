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

echo "Setting up vault..."
vault.sh
echo "Vault is setup!"

set -m

echo "Downloading model files from GDrive to '$LOCAL_MODEL_DIRECTORY_PATH'..."
mkdir -p $LOCAL_MODEL_DIRECTORY_PATH
gdown https://drive.google.com/drive/folders/1Z-v77XxjHGYbpxcAUmza3LyCjt9bLf_J -O $LOCAL_MODEL_DIRECTORY_PATH --folder
echo "File downloaded successfully!"

echo "Storing files in Minio $MINIO_MODEL_BUCKET_NAME bucket..."
exec python3 src/store_files_to_bucket.py $LOCAL_MODEL_DIRECTORY_PATH
echo "File stored to Minio!"

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
