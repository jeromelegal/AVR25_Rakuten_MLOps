#!/bin/bash

#capture tous les noms de domaine
export SERVICE_NAME="$(hostname)"
export NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
export NGINX_STATUS_FILE="/var/log/status"
export NGINX_CONTENT_FILE="/var/log/content"
export HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"
# Chemin du socket fcgiwrap
export SOCKET_PATH="/var/run/fcgiwrap/fcgiwrap.socket"

echo "SERVICE_NAME=$SERVICE_NAME" >> /etc/environment
echo "NGINX_CONFIG_FILE=$NGINX_CONFIG_FILE" >> /etc/environment
echo "NGINX_STATUS_FILE=$NGINX_STATUS_FILE" >> /etc/environment
echo "NGINX_CONTENT_FILE=$NGINX_CONTENT_FILE" >> /etc/environment
echo "HEALTH_CHECK_FILE=$HEALTH_CHECK_FILE" >> /etc/environment
echo "SOCKET_PATH=$SOCKET_PATH" >> /etc/environment



cp /opt/nginx/install.sh /usr/local/bin/install.sh



chmod +x /usr/local/bin/install.sh


/usr/local/bin/install.sh > /opt/nginx/log.log
