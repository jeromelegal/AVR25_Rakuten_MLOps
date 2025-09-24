#!/bin/bash

# Minio requires certificates to be in the form public.crt / private.key in the folder specified through the --certs-dir
# option and the CAs in a 'CAs' folder
mkdir -p /etc/ssl/minio/CAs
ln -s /etc/ssl/minio/*.ca /etc/ssl/minio/CAs/
ln -s /etc/ssl/minio/minio.crt /etc/ssl/minio/public.crt
ln -s /etc/ssl/minio/minio.key /etc/ssl/minio/private.key

# Lauch Minio server
echo "Starting Minio server..."
minio server /data --address ":$PORT" \
                   --console-address ":$GUI_PORT" \
                   --certs-dir /etc/ssl/minio &
HEALTH_URL=https://127.0.0.1:$PORT/minio/health/live
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" $HEALTH_URL)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done
echo "Minio server started"

# Define alias for the following commands
ALIAS="myminio"
HOSTNAME="https://127.0.0.1:$PORT"

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
declare -a arr=("raw-images" "processed-images" "raw-models" "models" "ci-results" "results" "train-images" "test-images" "airflow" "airflow-logs")
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
echo "Minio buckets OK!"

# Setting up scrape metrics for Prometheus (see https://docs.min.io/community/minio-object-store/operations/monitoring/collect-minio-metrics-using-prometheus.html)
echo "Setting up Prometheus metrics..."
metrics=("" "node" "bucket" "resource")
for metric in "${metrics[@]}"; do
    result=$(mc admin prometheus generate "$ALIAS" "$metric")
    echo "\tconfiguration for metric '$metric':\n$result"
    token=$(echo "$result" | grep -Po '(?<=bearer_token:\s).*')
    echo "Token for metric '$metric' is: $token. Storing token in vault..."
    vault kv put secret/minio/prometheus/token_${metric} token="$token"
done

