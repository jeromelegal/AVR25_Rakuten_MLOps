#!/bin/bash
source /etc/environment


echo "Script started" >> /var/log/health-check.log


echo -e "Status: $(cat $NGINX_STATUS_FILE)\r"
echo -e "Content-Type: text/plain\r\n\r"
echo "$(cat $NGINX_CONTENT_FILE)"


echo "Script finished" >> /var/log/health-check.log