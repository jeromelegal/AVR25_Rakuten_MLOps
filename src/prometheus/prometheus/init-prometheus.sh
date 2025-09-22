#!/bin/bash
set -euo pipefail

machine=$(gcc -dumpmachine)
# TODO: Change SIGNATURE values if the Prometheus version is changed
if [ "$machine" = "arm64-apple-darwin24.5.0" ]; then
    echo "Architecture ARM64 sur Darwin détectée."
    ARCH="darwin-arm64"
    SIGNATURE="c17bc2c992f0b5515eebe2b4ccd626214f8e309a0fe6ec40ed13c42ec13d05fb"
elif [ "$machine" = "aarch64-linux-gnu" ]; then
    echo "Architecture ARM64 sur Darwin détectée."
    ARCH="linux-arm64"
    SIGNATURE="173389cc42bf09c4e6e54cb53fa07a5a835d7c261e14775d2183181d6e385d1c"
elif [ "$machine" = "x86_64-linux-gnu" ]; then
    echo "Architecture x86_64 sur Linux détectée."
    ARCH="linux-amd64"
    SIGNATURE="e811827af26d822afb09a4f28314f61b618b12cff5369835a67f674d8b46f39a"
else
    echo "L'architecture: $machine est non gérée"
    exit 1
fi
URL="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.${ARCH}.tar.gz"
ARCHIVE="$(basename "$URL")"

# Download the archive
echo "Downloading $ARCHIVE..."
curl -L -o "$ARCHIVE" "$URL"

# Verify checksum
echo "Verifying checksum..."
DOWNLOADED_CHECKSUM=$(sha256sum "$ARCHIVE" | awk '{print $1}')

if [[ "$DOWNLOADED_CHECKSUM" != "$SIGNATURE" ]]; then
    echo "Checksum verification failed!" >&2
    rm -f "$ARCHIVE"
    exit 1
fi

echo "Checksum verified."

echo "Extracting archive..."
tar -xzf "$ARCHIVE"

echo "Cleaning up archive..."
rm -f "$ARCHIVE"

# echo "Hashing password..."
# echo $PROMETHEUS_ROOT_PASSWORD | mkpasswd -m sha-512 -s > $PROMETHEUS_PASSWORD_HASH_FILE

echo "Generating configuration file to enable mTLS..."
sed \
  -e "s|\bCERT_FILE\b|${PROMETHEUS_CERT_PATH}|g" \
  -e "s|\bKEY_FILE\b|${PROMETHEUS_KEY_PATH}|g" \
  -e "s|\bCA_FILE\b|${PROMETHEUS_CA_PATH}|g" \
  -e "s|\bUSER\b|${PROMETHEUS_ROOT_USER}|g" \
  -e "s|\bPASSWORD_HASH\b|$(cat $PROMETHEUS_PASSWORD_HASH_FILE)|g" \
  web-config.template.yml > web-config.yml
rm web-config.template.yml


echo "Getting Minio/Prometheus tokens..."
MINIO_JOB_BEARER_TOKEN=$(vault kv get -field=token secret/minio/prometheus/token_)
MINIO_JOB_NODE_BEARER_TOKEN=$(vault kv get -field=token secret/minio/prometheus/token_node)
MINIO_JOB_BUCKET_BEARER_TOKEN=$(vault kv get -field=token secret/minio/prometheus/token_bucket)
MINIO_JOB_RESOURCE_BEARER_TOKEN=$(vault kv get -field=token secret/minio/prometheus/token_resource)

echo "MINIO_JOB_BEARER_TOKEN: ${MINIO_JOB_BEARER_TOKEN}"
echo "MINIO_JOB_NODE_BEARER_TOKEN: ${MINIO_JOB_NODE_BEARER_TOKEN}"
echo "MINIO_JOB_BUCKET_BEARER_TOKEN: ${MINIO_JOB_BUCKET_BEARER_TOKEN}"
echo "MINIO_JOB_RESOURCE_BEARER_TOKEN: ${MINIO_JOB_RESOURCE_BEARER_TOKEN}"

echo "Getting AlertManager credentials..."
ALERTMANAGER_ROOT_USER=$(vault kv get -field=user secret/alertmanager/prometheus/credentials)
ALERTMANAGER_ROOT_PASSWORD=$(vault kv get -field=password secret/alertmanager/prometheus/credentials)

echo "Configuring scraping..."
sed \
  -e "s|\bALERTMANAGER_PROMETHEUS_CA_PATH\b|${ALERTMANAGER_PROMETHEUS_CA_PATH}|g" \
  -e "s|\bALERTMANAGER_SERVICE_NAME\b|${ALERTMANAGER_SERVICE_NAME}|g" \
  -e "s|\bALERTMANAGER_SERVICE_PORT\b|${ALERTMANAGER_SERVICE_PORT}|g" \
  -e "s|\bALERTMANAGER_ROOT_USER\b|${ALERTMANAGER_ROOT_USER}|g" \
  -e "s|\bALERTMANAGER_ROOT_PASSWORD\b|${ALERTMANAGER_ROOT_PASSWORD}|g" \
  -e "s|\bPROMETHEUS_PROMETHEUS_CA_PATH\b|${PROMETHEUS_PROMETHEUS_CA_PATH}|g" \
  -e "s|\bPROMETHEUS_ROOT_USER\b|${PROMETHEUS_ROOT_USER}|g" \
  -e "s|\bPROMETHEUS_ROOT_PASSWORD\b|${PROMETHEUS_ROOT_PASSWORD}|g" \
  -e "s|\bMINIO_PROMETHEUS_CA_PATH\b|${MINIO_PROMETHEUS_CA_PATH}|g" \
  -e "s|\bMINIO_SERVICE_NAME\b|${MINIO_SERVICE_NAME}|g" \
  -e "s|\bMINIO_SERVICE_PORT\b|${MINIO_SERVICE_PORT}|g" \
  -e "s|\bSERVICE_NAME\b|${SERVICE_NAME}|g" \
  -e "s|\bSERVICE_PORT\b|${SERVICE_PORT}|g" \
  -e "s|\bMINIO_JOB_BEARER_TOKEN\b|${MINIO_JOB_BEARER_TOKEN}|g" \
  -e "s|\bMINIO_JOB_NODE_BEARER_TOKEN\b|${MINIO_JOB_NODE_BEARER_TOKEN}|g" \
  -e "s|\bMINIO_JOB_BUCKET_BEARER_TOKEN\b|${MINIO_JOB_BUCKET_BEARER_TOKEN}|g" \
  -e "s|\bMINIO_JOB_RESOURCE_BEARER_TOKEN\b|${MINIO_JOB_RESOURCE_BEARER_TOKEN}|g" \
  prometheus.template.yml > prometheus.yml
rm prometheus.template.yml

echo "Configuring alerts..."
sed \
  -e "s|\bMINIO_SERVICE_NAME\b|${MINIO_SERVICE_NAME}|g" \
  -e "s|\bMINIO_SERVICE_PORT\b|${MINIO_SERVICE_PORT}|g" \
  instance_shutdown_rules.template.yml > instance_shutdown_rules.yml
rm instance_shutdown_rules.template.yml

echo "Starting prometheus..."
prometheus-$PROMETHEUS_VERSION.$ARCH/prometheus \
        --web.listen-address="0.0.0.0:${SERVICE_PORT}" \
        --storage.tsdb.retention.time=$PROMETHEUS_RETENTION_TIME \
        --storage.tsdb.retention.size=$PROMETHEUS_RETENTION_SIZE \
        --web.config.file="/app/web-config.yml" \
        --config.file="/app/prometheus.yml" &

echo "Prometheus started successfully!"
