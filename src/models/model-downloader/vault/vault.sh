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

mkdir -p $(dirname $MODEL_DOWNLOADER_PEM_PATH)  $(dirname $MODEL_DOWNLOADER_CA_PATH) $(dirname $MINIO_MODEL_DOWNLOADER_PEM_PATH) $(dirname $MINIO_MODEL_DOWNLOADER_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/minio/ca > minio_ca.crt
vault kv get -field=certificate secret/model-downloader/ca > model-downloader_ca.crt

mkdir -p $(dirname $MODEL_DOWNLOADER_PEM_PATH)
mkdir -p $(dirname $MODEL_DOWNLOADER_CA_PATH)
mkdir -p $(dirname $MODEL_DOWNLOADER_KEY_PATH)
mkdir -p $(dirname $MODEL_DOWNLOADER_CERT_PATH)

cp model-downloader_ca.crt $MODEL_DOWNLOADER_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/
cp model-downloader_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_model-downloader/issue/model-downloader common_name="model-downloader" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > model-downloader_cert.json

cat <<EOF > $MODEL_DOWNLOADER_PEM_PATH
$(jq -r '.data.private_key' model-downloader_cert.json)
$(jq -r '.data.certificate' model-downloader_cert.json)
$(jq -r '.data.issuing_ca' model-downloader_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "MODEL_DOWNLOADER_CERT_PATH = $MODEL_DOWNLOADER_CERT_PATH"
cat <<EOF > $MODEL_DOWNLOADER_CERT_PATH
$(jq -r '.data.certificate' model-downloader_cert.json)
EOF
echo "MODEL_DOWNLOADER_KEY_PATH = $MODEL_DOWNLOADER_KEY_PATH"
cat <<EOF > $MODEL_DOWNLOADER_KEY_PATH
$(jq -r '.data.private_key' model-downloader_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown model-downloader:model-downloader $MODEL_DOWNLOADER_PEM_PATH
chmod 400 $MODEL_DOWNLOADER_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f model-downloader_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/model-downloader/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/model-downloader/keyfile value=$key_value
fi

MODEL_DOWNLOADER_SECRET_KEY=$(vault kv get -field=value secret/model-downloader/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/model-downloader/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/model-downloader/internal_keyfile value=$key_value
fi

MODEL_DOWNLOADER_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/model-downloader/internal_keyfile)

# Extraire le certificat et la clé privée
MINIO_MODEL_DOWNLOADER_CA=$(vault kv get -field=ca secret/minio/model-downloader/certs)
MINIO_MODEL_DOWNLOADER_CERT=$(vault kv get -field=cert secret/minio/model-downloader/certs)
MINIO_MODEL_DOWNLOADER_KEY=$(vault kv get -field=key secret/minio/model-downloader/certs)

cat <<EOF > $MINIO_MODEL_DOWNLOADER_PEM_PATH
$(printf "%s" "$MINIO_MODEL_DOWNLOADER_KEY")
$(printf "%s" "$MINIO_MODEL_DOWNLOADER_CERT")
EOF

cat <<EOF > $MINIO_MODEL_DOWNLOADER_CA_PATH
$(printf "%s" "$MINIO_MODEL_DOWNLOADER_CA")
EOF