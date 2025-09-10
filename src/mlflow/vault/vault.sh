#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
    echo "Waiting for Vault service to be healthy."
    sleep 1
done

# Se connecter à Vault et récupérer un token
export VAULT_SKIP_VERIFY="1"

mkdir -p $(dirname $MLFLOW_PEM_PATH)  $(dirname $MLFLOW_CA_PATH) $(dirname $POSTGRESQL_MLFLOW_PEM_PATH) $(dirname $POSTGRESQL_MLFLOW_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/mongodb/ca > mongodb_ca.crt
vault kv get -field=certificate secret/api-mongodb/ca > api-mongodb_ca.crt

mkdir -p $(dirname $MLFLOW_PEM_PATH)
mkdir -p $(dirname $MLFLOW_CA_PATH)
mkdir -p $(dirname $MLFLOW_KEY_PATH)
mkdir -p $(dirname $MLFLOW_CERT_PATH)

cp api-mongodb_ca.crt $MLFLOW_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp mongodb_ca.crt /usr/local/share/ca-certificates/
cp api-mongodb_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_api-mongodb/issue/api-mongodb common_name="api-mongodb" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > api-mongodb_cert.json

cat <<EOF > $MLFLOW_PEM_PATH
$(jq -r '.data.private_key' api-mongodb_cert.json)
$(jq -r '.data.certificate' api-mongodb_cert.json)
$(jq -r '.data.issuing_ca' api-mongodb_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "MLFLOW_CERT_PATH = $MLFLOW_CERT_PATH"
cat <<EOF > $MLFLOW_CERT_PATH
$(jq -r '.data.certificate' api-mongodb_cert.json)
EOF
echo "MLFLOW_KEY_PATH = $MLFLOW_KEY_PATH"
cat <<EOF > $MLFLOW_KEY_PATH
$(jq -r '.data.private_key' api-mongodb_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown api-mongodb:api-mongodb $MLFLOW_PEM_PATH
chmod 400 $MLFLOW_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f api-mongodb_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-mongodb/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-mongodb/keyfile value=$key_value
fi

MLFLOW_SECRET_KEY=$(vault kv get -field=value secret/api-mongodb/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-mongodb/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-mongodb/internal_keyfile value=$key_value
fi

MLFLOW_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/api-mongodb/internal_keyfile)




# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-mongodb/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-mongodb/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-mongodb pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-mongodb/issue/api-mongodb common_name="api-mongodb"   ttl="72h" > api-mongodb_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  MLFLOW_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' api-mongodb_api-gateway_cert.json)
  MLFLOW_API_GATEWAY_CERT=$(jq -r '.data.certificate' api-mongodb_api-gateway_cert.json)
  MLFLOW_API_GATEWAY_KEY=$(jq -r '.data.private_key' api-mongodb_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-mongodb/api-gateway/certs cert="$MLFLOW_API_GATEWAY_CERT" key="$MLFLOW_API_GATEWAY_KEY" ca="$MLFLOW_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-mongodb_api-gateway_cert.json
fi



# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-mongodb/api-mongodb/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-mongodb/api-mongodb/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-mongodb pour le api-mongodb existent déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-mongodb/issue/api-mongodb common_name="api-mongodb"   ttl="72h" > api-mongodb_api-mongodb_cert.json

  # Extraire le certificat et la clé privée
  MLFLOW_MLFLOW_CA=$(jq -r '.data.ca_chain[0]' api-mongodb_api-mongodb_cert.json)
  MLFLOW_MLFLOW_CERT=$(jq -r '.data.certificate' api-mongodb_api-mongodb_cert.json)
  MLFLOW_MLFLOW_KEY=$(jq -r '.data.private_key' api-mongodb_api-mongodb_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-mongodb/api-mongodb/certs cert="$MLFLOW_MLFLOW_CERT" key="$MLFLOW_MLFLOW_KEY" ca="$MLFLOW_MLFLOW_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-mongodb_api-mongodb_cert.json
fi


cat <<EOF > $MLFLOW_MLFLOW_KEY_PATH
$(printf "%s" "$MLFLOW_MLFLOW_KEY")
EOF

cat <<EOF > $MLFLOW_MLFLOW_CERT_PATH
$(printf "%s" "$MLFLOW_MLFLOW_CERT")
EOF

cat <<EOF > $MLFLOW_MLFLOW_PEM_PATH
$(printf "%s" "$MLFLOW_MLFLOW_KEY")
$(printf "%s" "$MLFLOW_MLFLOW_CERT")
EOF

cat <<EOF > $MLFLOW_MLFLOW_CA_PATH
$(printf "%s" "$MLFLOW_MLFLOW_CA")
EOF



# Extraire le certificat et la clé privée
POSTGRESQL_MLFLOW_CA=$(vault kv get -field=ca secret/mongodb/api-mongodb/certs)
POSTGRESQL_MLFLOW_CERT=$(vault kv get -field=cert secret/mongodb/api-mongodb/certs)
POSTGRESQL_MLFLOW_KEY=$(vault kv get -field=key secret/mongodb/api-mongodb/certs)

cat <<EOF > $POSTGRESQL_MLFLOW_PEM_PATH
$(printf "%s" "$POSTGRESQL_MLFLOW_KEY")
$(printf "%s" "$POSTGRESQL_MLFLOW_CERT")
EOF

cat <<EOF > $POSTGRESQL_MLFLOW_CA_PATH
$(printf "%s" "$POSTGRESQL_MLFLOW_CA")
EOF