#!/bin/bash

SAVE_AUTHORIZATION=$AUTHORIZATION
AUTHORIZATION=disabled
mkdir -p $(dirname $LOG_PATH) $DB_PATH
generate-config.sh

# Démarrer MongoDB en arrière-plan sans authentification
mongod --config /etc/mongod.conf & #--logpath /var/log/mongodb/mongod.log 
PID_MONGO=$!

echo "Waiting for MongoDB to be ready..."
# Attendre que MongoDB soit prêt
until mongosh --host 127.0.0.1 --port 27017 --tls --tlsCAFile $MONGODB_MONGODB_CA_PATH  --tlsCertificateKeyFile $MONGODB_MONGODB_PEM_PATH  --eval 'quit(0)' &> /dev/null; do
  echo "Waiting for MongoDB to be ready..."
  sleep 1
done


echo "Init du replicat set DEBUT"
cat /usr/local/bin/init-mongodb-replicatset.js
mongosh --host 127.0.0.1 --port 27017 --tls --tlsCAFile $MONGODB_MONGODB_CA_PATH  --tlsCertificateKeyFile $MONGODB_MONGODB_PEM_PATH < /usr/local/bin/init-mongodb-replicatset.js 
mongosh --host 127.0.0.1 --port 27017 --tls --tlsCAFile $MONGODB_MONGODB_CA_PATH  --tlsCertificateKeyFile $MONGODB_MONGODB_PEM_PATH  --eval "rs.status()"
echo "Init du replicat set FIN"
echo "Init du base DEBUT"
mongosh --host 127.0.0.1 --port 27017 --tls --tlsCAFile $MONGODB_MONGODB_CA_PATH  --tlsCertificateKeyFile $MONGODB_MONGODB_PEM_PATH <  /usr/local/bin/init-mongodb.js 
echo "Init du base FIN"






kill -SIGTERM $PID_MONGO > /dev/null 2>&1

# Boucle jusqu'à ce que MongoDB soit arrêté
until ! pgrep -x "mongod" > /dev/null ; do
    echo "MongoDB est en cours d'exécution. Attente de l'arrêt..."
    sleep 1 
done
echo "MongoDB est arrêté."

AUTHORIZATION=$SAVE_AUTHORIZATION
generate-config.sh

