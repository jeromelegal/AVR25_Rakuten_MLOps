#!/bin/bash
source /etc/environment

# 2. Copier les fichiers depuis /opt/nginx/ vers leurs destinations
cp /opt/nginx/nginx-fcgiwrap.sh /usr/local/bin/
cp /opt/nginx/health-check.sh /usr/local/bin/
cp /opt/nginx/nginx-conf.sh /usr/local/bin/

# 3. Configurer les permissions
chmod +x /usr/local/bin/*.sh

# Créer le répertoire pour le socket si nécessaire
mkdir -p $(dirname "$SOCKET_PATH")

# Démarrer fcgiwrap en arrière-plan
/usr/sbin/fcgiwrap -s unix:$SOCKET_PATH &
FCGIWRAP_PID=$!

# Attendre que le socket soit créé
until [ -e "$SOCKET_PATH" ]; do
  echo "Attente de la création du socket $SOCKET_PATH..."
  sleep 1
done

chown nobody:nogroup $SOCKET_PATH /usr/local/bin/health-check.sh
chmod 660 $SOCKET_PATH /usr/local/bin/health-check.sh
chmod g+w $SOCKET_PATH /usr/local/bin/health-check.sh
chmod +x /usr/local/bin/health-check.sh


mkdir -p $(dirname $NGINX_STATUS_FILE)
mkdir -p $(dirname $NGINX_CONTENT_FILE)

echo "200 OK" > $NGINX_STATUS_FILE
echo "Healthy" > $NGINX_CONTENT_FILE

nginx-conf.sh


# Tester la configuration Nginx
nginx -t

# Démarrer Nginx
nginx
NGINX_PID=$!

