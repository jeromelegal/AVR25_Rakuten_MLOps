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

mkdir -p $(dirname $API_GATEWAY_PEM_PATH) $(dirname $API_GATEWAY_CA_PATH) $(dirname $API_MONGODB_API_GATEWAY_PEM_PATH) $(dirname $API_MONGODB_API_GATEWAY_CA_PATH) $(dirname $API_POSTGRESQL_API_GATEWAY_PEM_PATH) $(dirname $API_POSTGRESQL_API_GATEWAY_CA_PATH)

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD ; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/api-mongodb/ca > api-mongodb_ca.crt
vault kv get -field=certificate secret/api-gateway/ca > api-gateway_ca.crt
vault kv get -field=certificate secret/api-postgresql/ca > api-postgresql_ca.crt
vault kv get -field=certificate secret/mlflow/ca > mlflow_ca.crt

mkdir -p $(dirname $API_GATEWAY_PEM_PATH)
mkdir -p $(dirname $API_GATEWAY_CA_PATH)
mkdir -p $(dirname $API_GATEWAY_KEY_PATH)
mkdir -p $(dirname $API_GATEWAY_CERT_PATH)

cp api-gateway_ca.crt $API_GATEWAY_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp api-mongodb_ca.crt /usr/local/share/ca-certificates/
cp api-gateway_ca.crt /usr/local/share/ca-certificates/
cp api-postgresql_ca.crt /usr/local/share/ca-certificates/
cp mlflow_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_api-gateway/issue/api-gateway common_name="api-gateway" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > api-gateway_cert.json

cat <<EOF > $API_GATEWAY_PEM_PATH
$(jq -r '.data.private_key' api-gateway_cert.json)
$(jq -r '.data.certificate' api-gateway_cert.json)
$(jq -r '.data.issuing_ca' api-gateway_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "API_GATEWAY_CERT_PATH = $API_GATEWAY_CERT_PATH"
cat <<EOF > $API_GATEWAY_CERT_PATH
$(jq -r '.data.certificate' api-gateway_cert.json)
EOF
echo "API_GATEWAY_KEY_PATH = $API_GATEWAY_KEY_PATH"
cat <<EOF > $API_GATEWAY_KEY_PATH
$(jq -r '.data.private_key' api-gateway_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown api-gateway:api-gateway $API_GATEWAY_PEM_PATH
chmod 400 $API_GATEWAY_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f api-gateway_cert.json

# Vérifier si le certificat et la clé API_GATEWAY existent déjà
if ! vault kv get -field=value secret/api-gateway/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-gateway/keyfile value=$key_value
fi

API_GATEWAY_SECRET_KEY=$(vault kv get -field=value secret/api-gateway/keyfile)

# Vérifier si le certificat et la clé API_GATEWAY existent déjà
if ! vault kv get -field=value secret/api-gateway/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-gateway/internal_keyfile value=$key_value
fi

API_GATEWAY_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/api-gateway/internal_keyfile)

cat <<EOF > $API_GATEWAY_INTERNAL_SECRET_KEY_PATH
$(printf "%s" "$API_GATEWAY_INTERNAL_SECRET_KEY")
EOF


# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-gateway/frontend/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-gateway/frontend/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-gateway pour le frontend existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-gateway/issue/api-gateway common_name="api-gateway" ttl="72h" > api-gateway_frontend_cert.json

  # Extraire le certificat et la clé privée
  API_GATEWAY_FRONTEND_CA=$(jq -r '.data.ca_chain[0]' api-gateway_frontend_cert.json)
  API_GATEWAY_FRONTEND_CERT=$(jq -r '.data.certificate' api-gateway_frontend_cert.json)
  API_GATEWAY_FRONTEND_KEY=$(jq -r '.data.private_key' api-gateway_frontend_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-gateway/frontend/certs cert="$API_GATEWAY_FRONTEND_CERT" key="$API_GATEWAY_FRONTEND_KEY" ca="$API_GATEWAY_FRONTEND_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-gateway_frontend_cert.json
fi

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-gateway/reverse-proxy/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-gateway/reverse-proxy/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-gateway pour le reverse-proxy existent déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-gateway/issue/api-gateway common_name="api-gateway" ttl="72h" > api-gateway_reverse-proxy_cert.json

  # Extraire le certificat et la clé privée
  API_GATEWAY_REVERSE_PROXY_CA=$(jq -r '.data.ca_chain[0]' api-gateway_reverse-proxy_cert.json)
  API_GATEWAY_REVERSE_PROXY_CERT=$(jq -r '.data.certificate' api-gateway_reverse-proxy_cert.json)
  API_GATEWAY_REVERSE_PROXY_KEY=$(jq -r '.data.private_key' api-gateway_reverse-proxy_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-gateway/reverse-proxy/certs cert="$API_GATEWAY_REVERSE_PROXY_CERT" key="$API_GATEWAY_REVERSE_PROXY_KEY" ca="$API_GATEWAY_REVERSE_PROXY_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-gateway_reverse-proxy_cert.json
fi

# Extraire le certificat et la clé privée pour MongoDB
API_MONGODB_API_GATEWAY_CA=$(vault kv get -field=ca secret/api-mongodb/api-gateway/certs)
API_MONGODB_API_GATEWAY_CERT=$(vault kv get -field=cert secret/api-mongodb/api-gateway/certs)
API_MONGODB_API_GATEWAY_KEY=$(vault kv get -field=key secret/api-mongodb/api-gateway/certs)

cat <<EOF > $API_MONGODB_API_GATEWAY_PEM_PATH
$(printf "%s" "$API_MONGODB_API_GATEWAY_KEY")
$(printf "%s" "$API_MONGODB_API_GATEWAY_CERT")
EOF

cat <<EOF > $API_MONGODB_API_GATEWAY_CA_PATH
$(printf "%s" "$API_MONGODB_API_GATEWAY_CA")
EOF

cat <<EOF > $API_MONGODB_API_GATEWAY_KEY_PATH
$(printf "%s" "$API_MONGODB_API_GATEWAY_KEY")
EOF

cat <<EOF > $API_MONGODB_API_GATEWAY_CERT_PATH
$(printf "%s" "$API_MONGODB_API_GATEWAY_CERT")
EOF

# Extraire le certificat et la clé privée pour PostgreSQL
API_POSTGRESQL_API_GATEWAY_CA=$(vault kv get -field=ca secret/api-postgresql/api-gateway/certs)
API_POSTGRESQL_API_GATEWAY_CERT=$(vault kv get -field=cert secret/api-postgresql/api-gateway/certs)
API_POSTGRESQL_API_GATEWAY_KEY=$(vault kv get -field=key secret/api-postgresql/api-gateway/certs)

cat <<EOF > $API_POSTGRESQL_API_GATEWAY_PEM_PATH
$(printf "%s" "$API_POSTGRESQL_API_GATEWAY_KEY")
$(printf "%s" "$API_POSTGRESQL_API_GATEWAY_CERT")
EOF

cat <<EOF > $API_POSTGRESQL_API_GATEWAY_CA_PATH
$(printf "%s" "$API_POSTGRESQL_API_GATEWAY_CA")
EOF

cat <<EOF > $API_POSTGRESQL_API_GATEWAY_KEY_PATH
$(printf "%s" "$API_POSTGRESQL_API_GATEWAY_KEY")
EOF

cat <<EOF > $API_POSTGRESQL_API_GATEWAY_CERT_PATH
$(printf "%s" "$API_POSTGRESQL_API_GATEWAY_CERT")
EOF

# Extraire le certificat et la clé privée pour MLFlow
MLFLOW_API_GATEWAY_CA=$(vault kv get -field=ca secret/mlflow/api-gateway/certs)
MLFLOW_API_GATEWAY_CERT=$(vault kv get -field=cert secret/mlflow/api-gateway/certs)
MLFLOW_API_GATEWAY_KEY=$(vault kv get -field=key secret/mlflow/api-gateway/certs)

cat <<EOF > $MLFLOW_API_GATEWAY_PEM_PATH
$(printf "%s" "$MLFLOW_API_GATEWAY_KEY")
$(printf "%s" "$MLFLOW_API_GATEWAY_CERT")
EOF

cat <<EOF > $MLFLOW_API_GATEWAY_CA_PATH
$(printf "%s" "$MLFLOW_API_GATEWAY_CA")
EOF

cat <<EOF > $MLFLOW_API_GATEWAY_KEY_PATH
$(printf "%s" "$MLFLOW_API_GATEWAY_KEY")
EOF

cat <<EOF > $MLFLOW_API_GATEWAY_CERT_PATH
$(printf "%s" "$MLFLOW_API_GATEWAY_CERT")
EOF
