#!/bin/bash
source /etc/environment


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

# 2. Copier les fichiers depuis /opt/nginx/ vers leurs destinations
cp /opt/nginx/nginx-fcgiwrap.sh /usr/local/bin/
cp /opt/nginx/health-check.sh /usr/local/bin/
cp /opt/nginx/nginx-conf.sh /usr/local/bin/
cp /opt/nginx/nginx-fcgiwrap.service /etc/systemd/system/nginx-fcgiwrap.service

# 3. Configurer les permissions
chmod +x /usr/local/bin/*.sh

# Créer le répertoire pour le socket si nécessaire
mkdir -p $(dirname "$SOCKET_PATH")
mkdir -p $(dirname $NGINX_STATUS_FILE)
mkdir -p $(dirname $NGINX_CONTENT_FILE)

echo "200 OK" > $NGINX_STATUS_FILE
echo "Healthy" > $NGINX_CONTENT_FILE

nginx-conf.sh

sudo systemctl daemon-reload
systemctl enable nginx-fcgiwrap.service
systemctl start nginx-fcgiwrap.service

