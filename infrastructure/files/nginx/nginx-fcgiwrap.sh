#!/bin/bash
source /etc/environment

nginx-conf.sh

# Créer le répertoire pour le socket si nécessaire
mkdir -p $(dirname "$SOCKET_PATH")

set -m

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

nginx -t


nginx


jobs 

fg %1