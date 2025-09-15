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

mkdir -p $(dirname $MLFLOW_PEM_PATH)  $(dirname $MLFLOW_CA_PATH) $(dirname $POSTGRESQL_MLFLOW_PEM_PATH) $(dirname $POSTGRESQL_MLFLOW_CA_PATH) $(dirname $MINIO_MLFLOW_PEM_PATH) $(dirname $MINIO_MLFLOW_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 seconde..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/mlflow/ca > mlflow_ca.crt
vault kv get -field=certificate secret/minio/ca > minio_ca.crt
vault kv get -field=certificate secret/postgresql/ca > postgresql_ca.crt

mkdir -p $(dirname $MLFLOW_PEM_PATH)
mkdir -p $(dirname $MLFLOW_CA_PATH)
mkdir -p $(dirname $MLFLOW_KEY_PATH)
mkdir -p $(dirname $MLFLOW_CERT_PATH)

cp mlflow_ca.crt $MLFLOW_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp mlflow_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/
cp postgresql_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_mlflow/issue/mlflow common_name="mlflow" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > mlflow_cert.json

cat <<EOF > $MLFLOW_PEM_PATH
$(jq -r '.data.private_key' mlflow_cert.json)
$(jq -r '.data.certificate' mlflow_cert.json)
$(jq -r '.data.issuing_ca' mlflow_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "MLFLOW_CERT_PATH = $MLFLOW_CERT_PATH"
cat <<EOF > $MLFLOW_CERT_PATH
$(jq -r '.data.certificate' mlflow_cert.json)
EOF
echo "MLFLOW_KEY_PATH = $MLFLOW_KEY_PATH"
cat <<EOF > $MLFLOW_KEY_PATH
$(jq -r '.data.private_key' mlflow_cert.json)
EOF

chown mlflow:mlflow $MLFLOW_KEY_PATH
chmod 600 $MLFLOW_KEY_PATH


# Définir les permissions pour les fichiers de certificat et de clé
chown mlflow:mlflow $MLFLOW_PEM_PATH
chmod 400 $MLFLOW_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f mlflow_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/mlflow/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/mlflow/keyfile value=$key_value
fi

MLFLOW_SECRET_KEY=$(vault kv get -field=value secret/mlflow/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/mlflow/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/mlflow/internal_keyfile value=$key_value
fi

MLFLOW_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/mlflow/internal_keyfile)




# Vérifier si le certificat et la clé Vault pour API-Gateway existent déjà ou les créer
if vault kv get -field=cert secret/mlflow/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/mlflow/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS mlflow pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_mlflow/issue/mlflow common_name="mlflow"   ttl="72h" > mlflow_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  MLFLOW_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' mlflow_api-gateway_cert.json)
  MLFLOW_API_GATEWAY_CERT=$(jq -r '.data.certificate' mlflow_api-gateway_cert.json)
  MLFLOW_API_GATEWAY_KEY=$(jq -r '.data.private_key' mlflow_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/mlflow/api-gateway/certs cert="$MLFLOW_API_GATEWAY_CERT" key="$MLFLOW_API_GATEWAY_KEY" ca="$MLFLOW_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f mlflow_api-gateway_cert.json
fi



# Vérifier si le certificat et la clé Vault existent déjà pour MLFlow
if vault kv get -field=cert secret/mlflow/mlflow/certs > /dev/null 2>&1 && vault kv get -field=key secret/mlflow/mlflow/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS mlflow pour le mlflow existent déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_mlflow/issue/mlflow common_name="mlflow"   ttl="72h" > mlflow_mlflow_cert.json

  # Extraire le certificat et la clé privée
  MLFLOW_MLFLOW_CA=$(jq -r '.data.ca_chain[0]' mlflow_mlflow_cert.json)
  MLFLOW_MLFLOW_CERT=$(jq -r '.data.certificate' mlflow_mlflow_cert.json)
  MLFLOW_MLFLOW_KEY=$(jq -r '.data.private_key' mlflow_mlflow_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/mlflow/mlflow/certs cert="$MLFLOW_MLFLOW_CERT" key="$MLFLOW_MLFLOW_KEY" ca="$MLFLOW_MLFLOW_CA"

  # Nettoyage des fichiers temporaires
  rm -f mlflow_mlflow_cert.json
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

chown mlflow:mlflow $MLFLOW_MLFLOW_KEY_PATH
chmod 600 $MLFLOW_MLFLOW_KEY_PATH

# Extraire le certificat et la clé privée de PostGreSQL
POSTGRESQL_MLFLOW_CA=$(vault kv get -field=ca secret/postgresql/mlflow/certs)
POSTGRESQL_MLFLOW_CERT=$(vault kv get -field=cert secret/postgresql/mlflow/certs)
POSTGRESQL_MLFLOW_KEY=$(vault kv get -field=key secret/postgresql/mlflow/certs)

cat <<EOF > $POSTGRESQL_MLFLOW_PEM_PATH
$(printf "%s" "$POSTGRESQL_MLFLOW_KEY")
$(printf "%s" "$POSTGRESQL_MLFLOW_CERT")
EOF

cat <<EOF > $POSTGRESQL_MLFLOW_CA_PATH
$(printf "%s" "$POSTGRESQL_MLFLOW_CA")
EOF

cat <<EOF > "${POSTGRESQL_MLFLOW_KEY_PATH}"
$(printf "%s" "$POSTGRESQL_MLFLOW_KEY")
EOF

cat <<EOF > "${POSTGRESQL_MLFLOW_CERT_PATH}"
$(printf "%s" "$POSTGRESQL_MLFLOW_CERT")
EOF

chown mlflow:mlflow $POSTGRESQL_MLFLOW_KEY_PATH
chmod 600 $POSTGRESQL_MLFLOW_KEY_PATH

# Extraire le certificat et la clé privée de Minio
MINIO_MLFLOW_CA=$(vault kv get -field=ca secret/minio/mlflow/certs)
MINIO_MLFLOW_CERT=$(vault kv get -field=cert secret/minio/mlflow/certs)
MINIO_MLFLOW_KEY=$(vault kv get -field=key secret/minio/mlflow/certs)

cat <<EOF > $MINIO_MLFLOW_PEM_PATH
$(printf "%s" "$MINIO_MLFLOW_KEY")
$(printf "%s" "$MINIO_MLFLOW_CERT")
EOF

cat <<EOF > $MINIO_MLFLOW_CA_PATH
$(printf "%s" "$MINIO_MLFLOW_CA")
EOF

cat <<EOF > "${MINIO_MLFLOW_KEY_PATH}"
$(printf "%s" "$POSTGRESQL_MLFLOW_KEY")
EOF

cat <<EOF > "${MINIO_MLFLOW_CERT_PATH}"
$(printf "%s" "$POSTGRESQL_MLFLOW_CERT")
EOF

chown mlflow:mlflow $MINIO_MLFLOW_KEY_PATH
chmod 600 $MINIO_MLFLOW_KEY_PATH