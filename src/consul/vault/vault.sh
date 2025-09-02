#!/bin/bash

export VAULT_SKIP_VERIFY="1"

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD  > /dev/null ; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

echo "Authentification réussie!"

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/mongodb/ca > mongodb_ca.crt

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp mongodb_ca.crt /usr/local/share/ca-certificates/

update-ca-certificates

export VAULT_SKIP_VERIFY="0"
ips=$(ip -o -4 addr list | awk '{print $4}' | cut -d/ -f1)
# Variable pour stocker les adresses IP séparées par des virgules
ip_list=""
# Boucle pour traiter chaque adresse IP
for ip in $ips; do
  if [ -z "$ip_list" ]; then
    ip_list="$ip"
  else
    ip_list="$ip_list,$ip"
  fi
done

vault write -format=json pki_consul/issue/consul common_name="consul" ip_sans="$ip_list" alt_names="server.dc1.consul, consul" ttl="72h" > consul_service_cert.json

# Extraire le certificat et la clé privée
CONSUL_SERVICE_CERT=$(jq -r '.data.certificate' consul_service_cert.json)
CONSUL_SERVICE_KEY=$(jq -r '.data.private_key' consul_service_cert.json)

# Stocker le certificat et la clé privée dans des fichiers
echo "$CONSUL_SERVICE_CERT" > $CONSUL_CERT_FILE
echo "$CONSUL_SERVICE_KEY" > $CONSUL_KEY_FILE

# Définir les permissions pour les fichiers de certificat et de clé
chown consul:consul $CONSUL_CERT_FILE $CONSUL_KEY_FILE
chmod 400 $CONSUL_CERT_FILE $CONSUL_KEY_FILE

# Nettoyage des fichiers temporaires
rm -f vault_ca.crt consul_ca.crt mongodb_ca.crt consul_service.json

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=vault_cert secret/consul/vault/certs > /dev/null 2>&1 && vault kv get -field=vault_key secret/consul/vault/certs > /dev/null 2>&1; then
  echo "Le certificat et la clé Vault existent déjà"
  VAULT_SERVICE_CERT=$(vault kv get -field=vault_cert secret/consul/vault/certs)
  VAULT_SERVICE_KEY=$(vault kv get -field=vault_key secret/consul/vault/certs)
else
  # Générer le certificat et la clé pour Vault
  echo "Générer le certificat et la clé pour Vault"
  vault write -format=json pki_consul/issue/consul common_name="consul"   ttl="72h" > vault_service_cert.json

  # Extraire le certificat et la clé privée
  VAULT_SERVICE_CERT=$(jq -r '.data.certificate' vault_service_cert.json)
  VAULT_SERVICE_KEY=$(jq -r '.data.private_key' vault_service_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/consul/vault/certs vault_cert="$VAULT_SERVICE_CERT" vault_key="$VAULT_SERVICE_KEY"

  # Nettoyage des fichiers temporaires
  rm -f vault_service_cert.json
fi

# Stocker le certificat et la clé privée dans des fichiers
echo "$VAULT_SERVICE_CERT" > vault_service.crt
echo "$VAULT_SERVICE_KEY" > vault_service.key

# Définir les permissions pour les fichiers de certificat et de clé
chown vault:vault vault_service.crt vault_service.key
chmod 400 vault_service.crt vault_service.key
