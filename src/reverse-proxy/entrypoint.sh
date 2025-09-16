#!/bin/bash


HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$FRONTEND_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$FRONTEND_SERVICE_NAME/health)
    echo "Waiting for Frontend service to be healthy."
    sleep 1
done

vault.sh

set -m




source nginx-fcgiwrap.sh

#nginx-conf.sh


jobs


fg %2