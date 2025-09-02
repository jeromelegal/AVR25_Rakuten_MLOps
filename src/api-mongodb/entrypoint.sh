#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MONGODB_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MONGODB_SERVICE_NAME/health)
    echo "Waiting for Mongodb service to be healthy."
    sleep 1
done

#export MONGODB_IP=$(nslookup $MONGODB_SERVICE_NAME | awk '/^Address: / { print $2 }' | tail -n 1)

vault.sh

set -m

exec uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile $API_MONGODB_KEY_PATH --ssl-certfile $API_MONGODB_CERT_PATH  --ssl-ca-certs $API_MONGODB_CA_PATH --ssl-cert-reqs 2 &

#exec uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile $API_MONGODB_API_MONGODB_KEY_PATH --ssl-certfile $API_MONGODB_API_MONGODB_CERT_PATH  --ssl-ca-certs $API_MONGODB_API_MONGODB_CA_PATH &


jobs

nginx-fcgiwrap.sh

nginx-conf.sh

# curl --cert $API_MONGODB_API_MONGODB_CERT_PATH  \
#       --key $API_MONGODB_API_MONGODB_KEY_PATH  \
#       --cacert $API_MONGODB_API_MONGODB_CA_PATH\
#       https://$SERVICE_NAME:8000


fg %1