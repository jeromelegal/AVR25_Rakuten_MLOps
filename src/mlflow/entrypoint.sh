#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MONGODB_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MONGODB_SERVICE_NAME/health)
    echo "Waiting for Mongodb service to be healthy."
    sleep 1
done


# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done



vault.sh

set -m

su - postgresql -c "mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./artifacts \
    --host 0.0.0.0 \
    --port $SERVICE_PORT \
    --serve-artifacts \
    --gunicorn-opts "--keyfile /path/to/private.key --certfile /path/to/certificate.crt" &


jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1