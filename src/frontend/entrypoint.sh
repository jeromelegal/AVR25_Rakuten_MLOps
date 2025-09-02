#!/bin/bash


HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_GATEWAY_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$API_GATEWAY_SERVICE_NAME/health)
    echo "Waiting for API-Gateway service to be healthy."
    sleep 1
done

vault.sh


npm run generate-server

npm run build

set -m


jobs

#npx serve -s build &
npm run start-server &

nginx-fcgiwrap.sh

nginx-conf.sh


fg %1