#!/bin/bash
# Générer le fichier de configuration MongoDB


cat <<EOF > /etc/mongod.conf
# mongod.conf

# Options de stockage
storage:
  dbPath: ${DB_PATH}
  engine: "wiredTiger"
  wiredTiger:
    engineConfig:
      configString: "verbose=[recovery_progress=0,checkpoint_progress=0]"

systemLog:
  verbosity: 0  # Niveau de verbosité global par défaut
  quiet: true   # Mode silencieux pour limiter les logs
  traceAllExceptions: false  # Désactiver les informations de débogage détaillées
  logAppend: true
  logRotate: reopen
  timeStampFormat: iso8601-local
  component:
    accessControl: {verbosity: 0}
    command: {verbosity: 0}
    control: {verbosity: 0}
    ftdc: {verbosity: 0}
    geo: {verbosity: 0}
    index: {verbosity: 0}
    network: {verbosity: 0}
    query: {verbosity: 0}
    replication:
      verbosity: 0
      election: {verbosity: 0}
      heartbeats: {verbosity: 0}
      initialSync: {verbosity: 0}
      rollback: {verbosity: 0}
    sharding: {verbosity: 0}
    storage:
      verbosity: 0
      journal: {verbosity: 0}
      recovery: {verbosity: 0}
      wt:
        verbosity: 0
        wtBackup: {verbosity: 0}
        wtCheckpoint: {verbosity: 0}
        wtCompact: {verbosity: 0}
        wtEviction: {verbosity: 0}
        wtHS: {verbosity: 0}
        wtRecovery: {verbosity: 0}
        wtRTS: {verbosity: 0}
        wtSalvage: {verbosity: 0}
        wtTimestamp: {verbosity: 0}
        wtTransaction: {verbosity: 0}
        wtVerify: {verbosity: 0}
        wtWriteLog: {verbosity: 0}
    write: {verbosity: 0}
    transaction: {verbosity: 0}


# Options de réplication
replication:
  replSetName: ${REPLSET_NAME}

# Options de réseau
net:
  port: ${PORT}
  bindIp: ${BIND_IP}
EOF

# Ajouter les options SSL si activées
if [ "${TLS_MODE}" = "requireTLS" ]; then
  cat <<EOF >> /etc/mongod.conf
  tls:
    mode: ${TLS_MODE}
    certificateKeyFile: ${MONGODB_PEM_PATH}
    CAFile: ${MONGODB_CA_PATH}
    allowConnectionsWithoutCertificates: ${mTLS}
EOF
fi

# Ajouter les options de sécurité

if [ "${AUTHORIZATION}" = "enabled" ]; then
cat <<EOF >> /etc/mongod.conf
# Options de sécurité
security:
  authorization: ${AUTHORIZATION}
  keyFile: /etc/ssl/mongodb/mongodb-keyfile
EOF
fi
echo "Fichier de configuration MongoDB généré avec succès."


echo "affichage fichier configuration mongoDB"
cat /etc/mongod.conf










cat <<EOF > /usr/local/bin/init-mongodb-replicatset.js
rs.initiate({
   _id: "rs0",
   members: [
     { _id: 0, host: "$SERVICE_NAME:27017" }
   ]
})
EOF


echo "affichage fichier /usr/local/bin/init-mongodb-replicatset.js de mongoDB"
cat init-mongodb-replicatset.js
