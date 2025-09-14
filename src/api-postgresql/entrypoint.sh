#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$POSTGRESQL_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$POSTGRESQL_SERVICE_NAME/health)
    echo "Waiting for PostgreSQL service to be healthy."
    sleep 1
done

vault.sh

API_POSTGRESQL_INTERNAL_SECRET_KEY=$(cat $API_POSTGRESQL_INTERNAL_SECRET_KEY_PATH)

set -m

exec uvicorn main:app --host 0.0.0.0 --port $SERVICE_PORT --ssl-keyfile $API_POSTGRESQL_KEY_PATH --ssl-certfile $API_POSTGRESQL_CERT_PATH --ssl-ca-certs $API_POSTGRESQL_CA_PATH --ssl-cert-reqs 2 --log-level info &

jobs

nginx-fcgiwrap.sh

nginx-conf.sh

fg %1
