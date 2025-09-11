#!/bin/bash

# Chemin du socket fcgiwrap
SOCKET_PATH="/var/run/fcgiwrap/fcgiwrap.socket"

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

# Définir les permissions pour le socket et le script de vérification de santé
chown nobody:nogroup $SOCKET_PATH /usr/local/bin/health-check.sh
chmod 660 $SOCKET_PATH /usr/local/bin/health-check.sh
chmod g+w $SOCKET_PATH /usr/local/bin/health-check.sh
chmod +x /usr/local/bin/health-check.sh


mkdir -p $(dirname $NGINX_STATUS_FILE)
mkdir -p $(dirname $NGINX_CONTENT_FILE)

echo "200 OK" > $NGINX_STATUS_FILE
echo "Healthy" > $NGINX_CONTENT_FILE

# Générer la configuration Nginx
nginx-conf.sh

# Tester la configuration Nginx
nginx -t

# Démarrer Nginx
nginx
NGINX_PID=$!

# Vérifier la santé du service
HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}\n" https://$SERVICE_NAME/health)

# Afficher le code de réponse
echo "HTTP Code: $HTTP_CODE"

# Vérifier si le service est sain
until [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 300 ]; do
  HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}\n" https://$SERVICE_NAME/health)
  # Afficher le code de réponse
  echo "HTTP Code: $HTTP_CODE"
  echo "Service is unhealthy."
  sleep 1
done


echo "Service HTTP CODE: $HTTP_CODE."

