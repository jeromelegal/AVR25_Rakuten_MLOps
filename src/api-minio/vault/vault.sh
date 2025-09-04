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

mkdir -p $(dirname $API_MINIO_PEM_PATH)  $(dirname $API_MINIO_CA_PATH) $(dirname $MINIO_API_MINIO_PEM_PATH) $(dirname $MINIO_API_MINIO_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/minio/ca > minio_ca.crt
vault kv get -field=certificate secret/api-minio/ca > api-minio_ca.crt

mkdir -p $(dirname $API_MINIO_PEM_PATH)
mkdir -p $(dirname $API_MINIO_CA_PATH)
mkdir -p $(dirname $API_MINIO_KEY_PATH)
mkdir -p $(dirname $API_MINIO_CERT_PATH)

cp api-minio_ca.crt $API_MINIO_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/
cp api-minio_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_api-minio/issue/api-minio common_name="api-minio" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > api-minio_cert.json

cat <<EOF > $API_MINIO_PEM_PATH
$(jq -r '.data.private_key' api-minio_cert.json)
$(jq -r '.data.certificate' api-minio_cert.json)
$(jq -r '.data.issuing_ca' api-minio_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "API_MINIO_CERT_PATH = $API_MINIO_CERT_PATH"
cat <<EOF > $API_MINIO_CERT_PATH
$(jq -r '.data.certificate' api-minio_cert.json)
EOF
echo "API_MINIO_KEY_PATH = $API_MINIO_KEY_PATH"
cat <<EOF > $API_MINIO_KEY_PATH
$(jq -r '.data.private_key' api-minio_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown api-minio:api-minio $API_MINIO_PEM_PATH
chmod 400 $API_MINIO_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f api-minio_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-minio/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-minio/keyfile value=$key_value
fi

API_MINIO_SECRET_KEY=$(vault kv get -field=value secret/api-minio/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-minio/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-minio/internal_keyfile value=$key_value
fi

API_MINIO_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/api-minio/internal_keyfile)




# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-minio/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-minio/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-minio pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-minio/issue/api-minio common_name="api-minio"   ttl="72h" > api-minio_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  API_MINIO_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' api-minio_api-gateway_cert.json)
  API_MINIO_API_GATEWAY_CERT=$(jq -r '.data.certificate' api-minio_api-gateway_cert.json)
  API_MINIO_API_GATEWAY_KEY=$(jq -r '.data.private_key' api-minio_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-minio/api-gateway/certs cert="$API_MINIO_API_GATEWAY_CERT" key="$API_MINIO_API_GATEWAY_KEY" ca="$API_MINIO_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-minio_api-gateway_cert.json
fi



# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-minio/api-minio/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-minio/api-minio/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-minio pour le api-minio existent déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-minio/issue/api-minio common_name="api-minio"   ttl="72h" > api-minio_api-minio_cert.json

  # Extraire le certificat et la clé privée
  API_MINIO_API_MINIO_CA=$(jq -r '.data.ca_chain[0]' api-minio_api-minio_cert.json)
  API_MINIO_API_MINIO_CERT=$(jq -r '.data.certificate' api-minio_api-minio_cert.json)
  API_MINIO_API_MINIO_KEY=$(jq -r '.data.private_key' api-minio_api-minio_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-minio/api-minio/certs cert="$API_MINIO_API_MINIO_CERT" key="$API_MINIO_API_MINIO_KEY" ca="$API_MINIO_API_MINIO_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-minio_api-minio_cert.json
fi


cat <<EOF > $API_MINIO_API_MINIO_KEY_PATH
$(printf "%s" "$API_MINIO_API_MINIO_KEY")
EOF

cat <<EOF > $API_MINIO_API_MINIO_CERT_PATH
$(printf "%s" "$API_MINIO_API_MINIO_CERT")
EOF

cat <<EOF > $API_MINIO_API_MINIO_PEM_PATH
$(printf "%s" "$API_MINIO_API_MINIO_KEY")
$(printf "%s" "$API_MINIO_API_MINIO_CERT")
EOF

cat <<EOF > $API_MINIO_API_MINIO_CA_PATH
$(printf "%s" "$API_MINIO_API_MINIO_CA")
EOF



# Extraire le certificat et la clé privée
MINIO_API_MINIO_CA=$(vault kv get -field=ca secret/minio/api-minio/certs)
MINIO_API_MINIO_CERT=$(vault kv get -field=cert secret/minio/api-minio/certs)
MINIO_API_MINIO_KEY=$(vault kv get -field=key secret/minio/api-minio/certs)

cat <<EOF > $MINIO_API_MINIO_PEM_PATH
$(printf "%s" "$MINIO_API_MINIO_KEY")
$(printf "%s" "$MINIO_API_MINIO_CERT")
EOF

cat <<EOF > $MINIO_API_MINIO_CA_PATH
$(printf "%s" "$MINIO_API_MINIO_CA")
EOF