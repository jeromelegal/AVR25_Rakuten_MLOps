#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_MONGODB_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_MONGODB_SERVICE_NAME/health)
    echo "Waiting for Mongodb service to be healthy."
    sleep 1
done

# Vérifier la santé du service PostgreSQL
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_POSTGRESQL_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_POSTGRESQL_SERVICE_NAME/health)
    echo "Waiting for PostgreSQL service to be healthy."
    sleep 1
done


# Vérifier la santé du service MLFlow
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MLFLOW_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MLFLOW_SERVICE_NAME/health)
    echo "Waiting for MLFlow service to be healthy."
    sleep 1
done

# Vérifier la santé du service API processing
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_PROCESSING_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_PROCESSING_SERVICE_NAME/health)
    echo "Waiting for API processing service to be healthy."
    sleep 1
done

vault.sh

API_GATEWAY_INTERNAL_SECRET_KEY=$(cat $API_GATEWAY_INTERNAL_SECRET_KEY_PATH)

set -m


uvicorn main:app \
  --reload \
  --host 0.0.0.0 \
  --port $SERVICE_PORT \
  --ssl-keyfile $API_GATEWAY_KEY_PATH \
  --ssl-certfile $API_GATEWAY_CERT_PATH \
  --ssl-ca-certs $API_GATEWAY_CA_PATH \
  --ssl-cert-reqs 2 \
  --log-level $UVICORN_LOG_LEVEL &



jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
