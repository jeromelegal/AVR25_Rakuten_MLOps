#!/bin/bash


source /etc/environment

# # Créer le répertoire pour le socket si nécessaire
# mkdir -p $(dirname "$SOCKET_PATH")

# # Démarrer fcgiwrap en arrière-plan
# /usr/sbin/fcgiwrap -s unix:$SOCKET_PATH &
# FCGIWRAP_PID=$!

# # Attendre que le socket soit créé
# until [ -e "$SOCKET_PATH" ]; do
#   echo "Attente de la création du socket $SOCKET_PATH..."
#   sleep 1
# done

# Définir les permissions pour le socket et le script de vérification de santé
# chown nobody:nogroup $SOCKET_PATH /usr/local/bin/health-check.sh
# chmod 660 $SOCKET_PATH /usr/local/bin/health-check.sh
# chmod g+w $SOCKET_PATH /usr/local/bin/health-check.sh
# chmod +x /usr/local/bin/health-check.sh


# mkdir -p $(dirname $NGINX_STATUS_FILE)
# mkdir -p $(dirname $NGINX_CONTENT_FILE)

# echo "200 OK" > $NGINX_STATUS_FILE
# echo "Healthy" > $NGINX_CONTENT_FILE

# Générer la configuration Nginx
# nginx-conf.sh

# # Tester la configuration Nginx
# nginx -t

# # # Démarrer Nginx
# # nginx
# # NGINX_PID=$!

# sudo systemctl restart nginx


