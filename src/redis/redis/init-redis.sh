#!/bin/bash

echo "Starting Redis server..."
redis-server --tls-port $SERVICE_PORT --port 0 \
    --tls-cert-file $REDIS_CERT_PATH \
    --tls-key-file $REDIS_KEY_PATH \
    --tls-ca-cert-file $REDIS_CA_PATH &
echo "Redis server started."