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

mkdir -p $(dirname $MINIO_PEM_PATH)  $(dirname $MINIO_CA_PATH) $(dirname $MINIO_MINIO_PEM_PATH) $(dirname $MINIO_MINIO_CA_PATH) $(dirname $MINIO_MLFLOW_PEM_PATH) $(dirname $MINIO_MLFLOW_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/minio/ca > minio_ca.crt
vault kv get -field=certificate secret/mlflow/ca > mlflow_ca.crt

cp minio_ca.crt $MINIO_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/
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

vault write -format=json pki_minio/issue/minio common_name="minio" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > minio_cert.json

cat <<EOF > $MINIO_PEM_PATH
$(jq -r '.data.private_key' minio_cert.json)
$(jq -r '.data.certificate' minio_cert.json)
$(jq -r '.data.issuing_ca' minio_cert.json)
EOF

# Extraire le certificat et la clé privée

echo "MINIO_CERT_PATH = $MINIO_CERT_PATH"
cat <<EOF > $MINIO_CERT_PATH
$(jq -r '.data.certificate' minio_cert.json)
EOF
echo "MINIO_KEY_PATH = $MINIO_KEY_PATH"
cat <<EOF > $MINIO_KEY_PATH
$(jq -r '.data.private_key' minio_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown minio:minio $MINIO_PEM_PATH
chmod 400 $MINIO_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f mongo_service.json

# Vérifier si le certificat et la clé Backend existent déjà
if vault kv get -field=cert secret/minio/minio/certs > /dev/null 2>&1 && vault kv get -field=key secret/minio/minio/certs > /dev/null 2>&1; then
  echo "Le certificat et la clé Backend existent déjà"
  MINIO_MINIO_CA=$(vault kv get -field=ca secret/minio/minio/certs)
  MINIO_MINIO_CERT=$(vault kv get -field=cert secret/minio/minio/certs)
  MINIO_MINIO_KEY=$(vault kv get -field=key secret/minio/minio/certs)  

else
  # Générer le certificat et la clé pour Backend
  echo "Générer le certificat et la clé pour Backend"
  vault write -format=json pki_minio/issue/minio common_name="minio"   ttl="72h" > minio_minio_cert.json

  # Extraire le certificat et la clé privée
  MINIO_MINIO_CA=$(jq -r '.data.ca_chain' minio_minio_cert.json)
  MINIO_MINIO_CERT=$(jq -r '.data.certificate' minio_minio_cert.json)
  MINIO_MINIO_KEY=$(jq -r '.data.private_key' minio_minio_cert.json)
  
  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/minio/minio/certs cert="$MINIO_MINIO_CERT" key="$MINIO_MINIO_KEY" ca="$MINIO_MINIO_CA"
  # Nettoyage des fichiers temporaires
  rm -f minio_minio_cert.json
fi

cat <<EOF > $MINIO_MINIO_PEM_PATH
$(printf "%s" "$MINIO_MINIO_KEY")
$(printf "%s" "$MINIO_MINIO_CERT")
EOF

printf "%s" $MINIO_MINIO_CA > $MINIO_MINIO_CA_PATH

key_value=$(openssl rand -base64 741 | tr -d '\n' )

vault kv put secret/minio/keyfile value=$key_value

retrieve=$(vault kv get -field=value secret/minio/keyfile)

mkdir -p /etc/ssl/minio/
echo $retrieve > /etc/ssl/minio/minio-keyfile
chmod 600 /etc/ssl/minio/minio-keyfile

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/minio/api-minio/certs > /dev/null 2>&1 && vault kv get -field=key secret/minio/api-minio/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS minio pour le service api-minio existe déjà"
else
  # Générer le certificat et la clé pour Vault
  echo "Générer le certificat et la clé pour Vault"
  vault write -format=json pki_minio/issue/minio common_name="minio"   ttl="72h" > minio_api-minio_cert.json
  # TODO: Define certificate duration as an env variable

  # Extraire le certificat et la clé privée
  MINIO_API_MINIO_CA=$(jq -r '.data.ca_chain[0]' minio_api-minio_cert.json)
  MINIO_API_MINIO_CERT=$(jq -r '.data.certificate' minio_api-minio_cert.json)
  MINIO_API_MINIO_KEY=$(jq -r '.data.private_key' minio_api-minio_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/minio/api-minio/certs cert="$MINIO_API_MINIO_CERT" key="$MINIO_API_MINIO_KEY" ca="$MINIO_API_MINIO_CA"

  # Nettoyage des fichiers temporaires
  rm -f vault_service_cert.json
fi

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/minio/mlflow/certs > /dev/null 2>&1 && vault kv get -field=key secret/minio/mlflow/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS minio pour le service mlflow existe déjà"
  MINIO_MLFLOW_CA=$(vault kv get -field=ca secret/minio/mlflow/certs)
  MINIO_MLFLOW_CERT=$(vault kv get -field=cert secret/minio/mlflow/certs)
  MINIO_MLFLOW_KEY=$(vault kv get -field=key secret/minio/mlflow/certs)  
else
  # Générer le certificat et la clé pour Vault
  echo "Générer le certificat et la clé pour Vault"
  vault write -format=json pki_minio/issue/minio common_name="minio"   ttl="72h" > minio_mlflow_cert.json
  # TODO: Define certificate duration as an env variable

  # Extraire le certificat et la clé privée
  MINIO_MLFLOW_CA=$(jq -r '.data.ca_chain[0]' minio_mlflow_cert.json)
  MINIO_MLFLOW_CERT=$(jq -r '.data.certificate' minio_mlflow_cert.json)
  MINIO_MLFLOW_KEY=$(jq -r '.data.private_key' minio_mlflow_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/minio/mlflow/certs cert="$MINIO_MLFLOW_CERT" key="$MINIO_MLFLOW_KEY" ca="$MINIO_MLFLOW_CA"
  # Nettoyage des fichiers temporaires
  rm -f vault_service_cert.json
fi

cat <<EOF > $MINIO_MLFLOW_PEM_PATH
$(printf "%s" "$MINIO_MLFLOW_KEY")
$(printf "%s" "$MINIO_MLFLOW_CERT")
EOF

printf "%s" $MINIO_MLFLOW_CA > $MINIO_MLFLOW_CA_PATH

# Vérifier si le certificat et la clé Vault existent déjà pour le model downloader
if vault kv get -field=cert secret/minio/model-downloader/certs > /dev/null 2>&1 && vault kv get -field=key secret/minio/model-downloader/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS minio pour le service model-downloader existe déjà"
else
  # Générer le certificat et la clé pour Vault
  echo "Générer le certificat et la clé pour Vault pour le model-downloader"
  vault write -format=json pki_minio/issue/minio common_name="minio"   ttl="72h" > minio_model-downloader_cert.json
  # TODO: Define certificate duration as an env variable

  # Extraire le certificat et la clé privée
  MINIO_MODEL_DOWNLOADER_CA=$(jq -r '.data.ca_chain[0]' minio_model-downloader_cert.json)
  MINIO_MODEL_DOWNLOADER_CERT=$(jq -r '.data.certificate' minio_model-downloader_cert.json)
  MINIO_MODEL_DOWNLOADER_KEY=$(jq -r '.data.private_key' minio_model-downloader_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/minio/model-downloader/certs cert="$MINIO_MODEL_DOWNLOADER_CERT" key="$MINIO_MODEL_DOWNLOADER_KEY" ca="$MINIO_MODEL_DOWNLOADER_CA"

  # Nettoyage des fichiers temporaires
  rm -f vault_service_cert.json
fi