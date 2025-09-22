#!/bin/bash
set -euo pipefail

machine=$(gcc -dumpmachine)
# TODO: Change SIGNATURE values if the Alertmanager version is changed
if [ "$machine" = "arm64-apple-darwin24.5.0" ]; then
    echo "Architecture ARM64 sur Darwin détectée."
    ARCH="darwin-arm64"
    SIGNATURE="6ad077f9de99fe96843a68313f19dd2dbc1e8929135293e48bb10824bd6b4df4"
elif [ "$machine" = "aarch64-linux-gnu" ]; then
    echo "Architecture ARM64 sur Darwin détectée."
    ARCH="linux-arm64"
    SIGNATURE="d8832540e5b9f613d2fd759e31d603173b9c61cc7bb5e3bc7ae2f12038b1ce4f"
elif [ "$machine" = "x86_64-linux-gnu" ]; then
    echo "Architecture x86_64 sur Linux détectée."
    ARCH="linux-amd64"
    SIGNATURE="5ac7ab5e4b8ee5ce4d8fb0988f9cb275efcc3f181b4b408179fafee121693311"
else
    echo "L'architecture: $machine est non gérée"
    exit 1
fi
URL="https://github.com/prometheus/alertmanager/releases/download/v${ALERTMANAGER_VERSION}/alertmanager-${ALERTMANAGER_VERSION}.${ARCH}.tar.gz"
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
# echo $ALERTMANAGER_ROOT_PASSWORD | mkpasswd -m sha-512 -s > $ALERTMANAGER_PASSWORD_HASH_FILE

echo "Generating configuration file to enable mTLS..."
sed \
  -e "s|CERT_FILE|${ALERTMANAGER_CERT_PATH}|g" \
  -e "s|KEY_FILE|${ALERTMANAGER_KEY_PATH}|g" \
  -e "s|CA_FILE|${ALERTMANAGER_CA_PATH}|g" \
  -e "s|USER|${ALERTMANAGER_ROOT_USER}|g" \
  -e "s|PASSWORD_HASH|$(cat $ALERTMANAGER_PASSWORD_HASH_FILE)|g" \
  web-config.template.yml > web-config.yml
rm web-config.template.yml

echo "Configuring scraping..."
sed \
  -e "s|SLACK_API_URL|${SLACK_API_URL}|g" \
  -e "s|SLACK_NOTIFICATION_CHANNEL|${SLACK_NOTIFICATION_CHANNEL}|g" \
  alertmanager.template.yml > alertmanager.yml
rm alertmanager.template.yml

echo "Starting alertmanager..."
alertmanager-$ALERTMANAGER_VERSION.$ARCH/alertmanager \
        --web.listen-address="0.0.0.0:${SERVICE_PORT}" \
        --web.config.file="/app/web-config.yml" \
        --config.file="/app/alertmanager.yml" &

echo "Alertmanager started successfully!"
