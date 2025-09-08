#!/bin/bash


echo "Script started" >> /var/log/health-check.log





while true; do

    if true ;

echo "200 OK" > $NGINX_STATUS_FILE
echo "Healthy" > $NGINX_CONTENT_FILE
else
echo "500 OK" > $NGINX_STATUS_FILE
echo "Unhealthy" > $NGINX_CONTENT_FILE

fi

echo "Script finished" >> /var/log/health-check.log
  sleep 1
done
