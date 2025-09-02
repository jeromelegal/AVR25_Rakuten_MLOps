#!/bin/bash

echo "Start Vault"
vault server -config=$VAULT_CONFIG_FILE &
SERVER_VAULT_PID=$!
echo "Vault server started with PID $SERVER_VAULT_PID"

echo "Start auto-unseal"
/usr/bin/python3 /usr/local/bin/auto-unseal.py > python.log 2>&1 &
export AUTO_UNSEAL_PID=$!
echo "Started auto-unseal AUTO_UNSEAL_PID: $AUTO_UNSEAL_PID"

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD  > /dev/null ; do
    echo "Test Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$CONSUL_SERVER_HOST/health)

until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$CONSUL_SERVER_HOST/health)
    echo "Waiting for Consul service to be healthy."
    sleep 1
done
echo "Consul is up and running!"

CONSUL_VAULT_TOKEN=$(vault kv get -field=vault_token  secret/consul/vault/tokens)

# Récupérer le certificat et la clé Vault depuis les secrets
VAULT_SERVICE_CERT=$(vault kv get -field=vault_cert secret/consul/vault/certs)
VAULT_SERVICE_KEY=$(vault kv get -field=vault_key secret/consul/vault/certs)

# Stocker le certificat et la clé privée dans des fichiers
echo "$VAULT_SERVICE_CERT" > consul_vault_service.crt
echo "$VAULT_SERVICE_KEY" > consul_vault_service.key

# Définir les permissions pour les fichiers de certificat et de clé
chown vault:vault consul_vault_service.crt consul_vault_service.key
chmod 400 consul_vault_service.crt consul_vault_service.key

#export CONSUL_HTTP_TOKEN=$CONSUL_VAULT_TOKEN
cat <<EOF > $VAULT_CONFIG_FILE
ui = true

storage "consul" {
  address = "$CONSUL_SERVER_HOST:$CONSUL_SERVER_PORT"
  path    = "vault/"
  scheme  = "https"

  #tls_ca_file = "/usr/local/share/ca-certificates/vault_ca.crt"
  tls_cert_file = "consul_vault_service.crt"
  tls_key_file = "consul_vault_service.key"
  
  token = "$CONSUL_VAULT_TOKEN"
}

listener "tcp" {
  address       = "$SERVICE_NAME:8200"
  tls_cert_file = "$VAULT_CERT_FILE"
  tls_key_file  = "$VAULT_KEY_FILE"
}

listener "tcp" {
  address       = "127.0.0.1:8200"
  tls_cert_file = "$VAULT_CERT_FILE"
  tls_key_file  = "$VAULT_KEY_FILE"
}

api_addr = "https://$SERVICE_NAME:8200"
cluster_addr = "https://$SERVICE_NAME:8201"
disable_mlock = true

# Configuration des logs
log_level = "info"
log_file = "/var/log/vault.log"
EOF

VAULT_MIGRATE_CONFIG_FILE="$(pwd)/migrate.conf"

cat <<EOF > $VAULT_MIGRATE_CONFIG_FILE
storage_source "file" {
  path = "$VAULT_LOCAL_DATA"
}

storage_destination "consul" {
  address = "$CONSUL_SERVER_HOST:$CONSUL_SERVER_PORT"
  path    = "vault/"
  scheme  = "https"

  #tls_ca_file = "/usr/local/share/ca-certificates/vault_ca.crt"
  tls_cert_file = "consul_vault_service.crt"
  tls_key_file = "consul_vault_service.key"
  
  token = "$CONSUL_VAULT_TOKEN"
}
EOF

echo "Migrating Vault data to Consul..."
vault operator migrate -config $VAULT_MIGRATE_CONFIG_FILE > /dev/null 2>&1

# Arrêter le serveur Vault local
kill -SIGTERM $SERVER_VAULT_PID > /dev/null 2>&1
echo "Local Vault server stopped"

# Vérifier si le processus a été arrêté correctement
until ! ps -p $SERVER_VAULT_PID > /dev/null; do
  echo "Le processus Vault est en cours d'arrêt."
  sleep 1
done
echo "Le processus Vault a été arrêté avec succès."

# Démarrer Vault avec Consul comme backend
vault server -config=$VAULT_CONFIG_FILE &
export SERVER_VAULT_PID=$!

echo "Vault server started with Consul backend with PID $SERVER_VAULT_PID"

# Attendre que Vault soit prêt avec le nouveau backend
until curl -k -s $VAULT_ADDR/v1/sys/seal-status > /dev/null; do
  echo "Waiting for Vault to be ready to check if initialized..."
  sleep 1
done
echo "Vault is ready"

vault login -method=userpass username=vault password=vault   > /dev/null

echo "Stop Vault SERVER_VAULT_PID: $SERVER_VAULT_PID"
kill -SIGTERM $SERVER_VAULT_PID > /dev/null 2>&1
# Vérifier si le processus a été arrêté correctement
until ! ps -p $SERVER_VAULT_PID > /dev/null; do
  echo "Le processus Vault est en cours d'arrêt."
  sleep 1
done
echo "Le processus Vault a été arrêté avec succès."

echo "Stop Auto-Unseal AUTO_UNSEAL_PID: $AUTO_UNSEAL_PID"
kill -SIGTERM $AUTO_UNSEAL_PID > /dev/null 2>&1
# Vérifier si le processus a été arrêté correctement
until ! ps -p $AUTO_UNSEAL_PID > /dev/null; do
  echo "Le processus Auto-Unseal est en cours d'arrêt."
  sleep 1
done
echo "Le processus Auto-Unseal a été arrêté avec succès."
