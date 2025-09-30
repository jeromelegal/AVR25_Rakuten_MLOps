#!/bin/bash

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
    echo "Waiting for Vault service to be healthy."
    sleep 1
done

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MLFLOW_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MLFLOW_SERVICE_NAME/health)
    echo "Waiting for MLFlow service to be healthy."
    sleep 1
done

# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done

# Se connecter à Vault et récupérer un token
export VAULT_SKIP_VERIFY="1"

mkdir -p $(dirname $API_TEXT_PROCESSING_PEM_PATH)  $(dirname $API_TEXT_PROCESSING_CA_PATH) $(dirname $MLFLOW_API_TEXT_PROCESSING_PEM_PATH) $(dirname $MLFLOW_API_TEXT_PROCESSING_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/api-text-processing/ca > api-text-processing_ca.crt
vault kv get -field=certificate secret/mlflow/ca > mlflow_ca.crt
vault kv get -field=certificate secret/minio/ca > minio_ca.crt
vault kv get -field=certificate secret/api-processing/ca > api-processing_ca.crt
# vault kv get -field=certificate secret/api-gateway/ca > api-gateway_ca.crt

mkdir -p $(dirname $API_TEXT_PROCESSING_PEM_PATH)
mkdir -p $(dirname $API_TEXT_PROCESSING_CA_PATH)
mkdir -p $(dirname $API_TEXT_PROCESSING_KEY_PATH)
mkdir -p $(dirname $API_TEXT_PROCESSING_CERT_PATH)

cp api-text-processing_ca.crt $API_TEXT_PROCESSING_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp api-text-processing_ca.crt /usr/local/share/ca-certificates/
# cp api-gateway_ca.crt /usr/local/share/ca-certificates/
cp mlflow_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/
cp api-processing_ca.crt /usr/local/share/ca-certificates/

cat mlflow_ca.crt >> $(python3 -c "import certifi; print(certifi.where())")
cat api-text-processing_ca.crt >> $(python3 -c "import certifi; print(certifi.where())")
cat minio_ca.crt >> $(python3 -c "import certifi; print(certifi.where())")
cat api-processing_ca.crt >> $(python3 -c "import certifi; print(certifi.where())")

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

vault write -format=json pki_api-text-processing/issue/api-text-processing common_name="api-text-processing" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > api-text-processing_cert.json

cat <<EOF > $API_TEXT_PROCESSING_PEM_PATH
$(jq -r '.data.private_key' api-text-processing_cert.json)
$(jq -r '.data.certificate' api-text-processing_cert.json)
$(jq -r '.data.issuing_ca' api-text-processing_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "API_TEXT_PROCESSING_CERT_PATH = $API_TEXT_PROCESSING_CERT_PATH"
cat <<EOF > $API_TEXT_PROCESSING_CERT_PATH
$(jq -r '.data.certificate' api-text-processing_cert.json)
EOF
echo "API_TEXT_PROCESSING_KEY_PATH = $API_TEXT_PROCESSING_KEY_PATH"
cat <<EOF > $API_TEXT_PROCESSING_KEY_PATH
$(jq -r '.data.private_key' api-text-processing_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown api-text-processing:api-text-processing $API_TEXT_PROCESSING_PEM_PATH
chmod 400 $API_TEXT_PROCESSING_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f api-text-processing_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-text-processing/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-text-processing/keyfile value=$key_value
fi

API_TEXT_PROCESSING_SECRET_KEY=$(vault kv get -field=value secret/api-text-processing/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/api-text-processing/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/api-text-processing/internal_keyfile value=$key_value
fi

API_TEXT_PROCESSING_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/api-text-processing/internal_keyfile)

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/api-text-processing/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-text-processing/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-text-processing pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-text-processing/issue/api-text-processing common_name="api-text-processing"   ttl="72h" > api-text-processing_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  API_TEXT_PROCESSING_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' api-text-processing_api-gateway_cert.json)
  API_TEXT_PROCESSING_API_GATEWAY_CERT=$(jq -r '.data.certificate' api-text-processing_api-gateway_cert.json)
  API_TEXT_PROCESSING_API_GATEWAY_KEY=$(jq -r '.data.private_key' api-text-processing_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-text-processing/api-gateway/certs cert="$API_TEXT_PROCESSING_API_GATEWAY_CERT" key="$API_TEXT_PROCESSING_API_GATEWAY_KEY" ca="$API_TEXT_PROCESSING_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-text-processing_api-gateway_cert.json
fi

# Ajouter les certificats pour l'API de processing générale
if vault kv get -field=cert secret/api-text-processing/api-processing/certs > /dev/null 2>&1 && vault kv get -field=key secret/api-text-processing/api-processing/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS api-text-processing pour le service api-processing existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_api-text-processing/issue/api-text-processing common_name="api-text-processing"   ttl="72h" > api-text-processing_api-processing_cert.json

  # Extraire le certificat et la clé privée
  API_TEXT_PROCESSING_API_PROCESSING_CA=$(jq -r '.data.ca_chain[0]' api-text-processing_api-processing_cert.json)
  API_TEXT_PROCESSING_API_PROCESSING_CERT=$(jq -r '.data.certificate' api-text-processing_api-processing_cert.json)
  API_TEXT_PROCESSING_API_PROCESSING_KEY=$(jq -r '.data.private_key' api-text-processing_api-processing_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/api-text-processing/api-processing/certs cert="$API_TEXT_PROCESSING_API_PROCESSING_CERT" key="$API_TEXT_PROCESSING_API_PROCESSING_KEY" ca="$API_TEXT_PROCESSING_API_PROCESSING_CA"

  # Nettoyage des fichiers temporaires
  rm -f api-text-processing_api-processing_cert.json
fi

# Extraire le certificat et la clé privée de MLFlow
MLFLOW_API_TEXT_PROCESSING_CA=$(vault kv get -field=ca secret/mlflow/api-text-processing/certs)
MLFLOW_API_TEXT_PROCESSING_CERT=$(vault kv get -field=cert secret/mlflow/api-text-processing/certs)
MLFLOW_API_TEXT_PROCESSING_KEY=$(vault kv get -field=key secret/mlflow/api-text-processing/certs)

cat <<EOF > $MLFLOW_API_TEXT_PROCESSING_PEM_PATH
$(printf "%s" "$MLFLOW_API_TEXT_PROCESSING_KEY")
$(printf "%s" "$MLFLOW_API_TEXT_PROCESSING_CERT")
EOF

cat <<EOF > $MLFLOW_API_TEXT_PROCESSING_CA_PATH
$(printf "%s" "$MLFLOW_API_TEXT_PROCESSING_CA")
EOF

cat <<EOF > "${MLFLOW_API_TEXT_PROCESSING_KEY_PATH}"
$(printf "%s" "$MLFLOW_API_TEXT_PROCESSING_KEY")
EOF

cat <<EOF > "${MLFLOW_API_TEXT_PROCESSING_CERT_PATH}"
$(printf "%s" "$MLFLOW_API_TEXT_PROCESSING_CERT")
EOF

chown api-text-processing:api-text-processing $MLFLOW_API_TEXT_PROCESSING_KEY_PATH
chmod 600 $MLFLOW_API_TEXT_PROCESSING_KEY_PATH

# Extraire le certificat et la clé privée de Minio
MINIO_API_TEXT_PROCESSING_CA=$(vault kv get -field=ca secret/minio/api-text-processing/certs)
MINIO_API_TEXT_PROCESSING_CERT=$(vault kv get -field=cert secret/minio/api-text-processing/certs)
MINIO_API_TEXT_PROCESSING_KEY=$(vault kv get -field=key secret/minio/api-text-processing/certs)

cat <<EOF > $MINIO_API_TEXT_PROCESSING_PEM_PATH
$(printf "%s" "$MINIO_API_TEXT_PROCESSING_KEY")
$(printf "%s" "$MINIO_API_TEXT_PROCESSING_CERT")
EOF

cat <<EOF > $MINIO_API_TEXT_PROCESSING_CA_PATH
$(printf "%s" "$MINIO_API_TEXT_PROCESSING_CA")
EOF

cat <<EOF > "${MINIO_API_TEXT_PROCESSING_KEY_PATH}"
$(printf "%s" "$MINIO_API_TEXT_PROCESSING_KEY")
EOF

cat <<EOF > "${MINIO_API_TEXT_PROCESSING_CERT_PATH}"
$(printf "%s" "$MINIO_API_TEXT_PROCESSING_CERT")
EOF

chown api-text-processing:api-text-processing $MINIO_API_TEXT_PROCESSING_KEY_PATH
chmod 600 $MINIO_API_TEXT_PROCESSING_KEY_PATH