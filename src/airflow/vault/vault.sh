#!/bin/bash
set -e

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

echo "Vault login..."
echo $VAULT_USERNAME

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done


echo "Vault récupère les certificats ..."
# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/airflow/ca > airflow_ca.crt

mkdir -p $(dirname $AIRFLOW_PEM_PATH)  
mkdir -p $(dirname $AIRFLOW_CA_PATH)
mkdir -p $(dirname $AIRFLOW_KEY_PATH)
mkdir -p $(dirname $AIRFLOW_CERT_PATH)
#mkdir -p $(dirname $AIRFLOW_FERNET_KEY_PATH)

cp airflow_ca.crt $AIRFLOW_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp airflow_ca.crt /usr/local/share/ca-certificates/
#cp airflow_fernet_key.txt /usr/local/share/ca-certificates/

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

vault write -format=json pki_airflow/issue/airflow common_name="airflow" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > airflow_cert.json

cat <<EOF > $AIRFLOW_PEM_PATH
$(jq -r '.data.private_key' airflow_cert.json)
$(jq -r '.data.certificate' airflow_cert.json)
$(jq -r '.data.issuing_ca' airflow_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "AIRFLOW_CERT_PATH = $AIRFLOW_CERT_PATH"
cat <<EOF > $AIRFLOW_CERT_PATH
$(jq -r '.data.certificate' airflow_cert.json)
EOF
echo "AIRFLOW_KEY_PATH = $AIRFLOW_KEY_PATH"
cat <<EOF > $AIRFLOW_KEY_PATH
$(jq -r '.data.private_key' airflow_cert.json)
EOF

chown airflow:airflow $AIRFLOW_KEY_PATH
chmod 600 $AIRFLOW_KEY_PATH


# Définir les permissions pour les fichiers de certificat et de clé
chown airflow:airflow $AIRFLOW_PEM_PATH
chmod 400 $AIRFLOW_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f airflow_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/airflow/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/airflow/keyfile value=$key_value
fi

AIRFLOW_SECRET_KEY=$(vault kv get -field=value secret/airflow/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/airflow/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/airflow/internal_keyfile value=$key_value
fi

AIRFLOW_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/airflow/internal_keyfile)




# Vérifier si le certificat et la clé Vault pour API-Gateway existent déjà ou les créer
if vault kv get -field=cert secret/airflow/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/airflow/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS airflow pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_airflow/issue/airflow common_name="airflow"   ttl="72h" > airflow_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  AIRFLOW_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' airflow_api-gateway_cert.json)
  AIRFLOW_API_GATEWAY_CERT=$(jq -r '.data.certificate' airflow_api-gateway_cert.json)
  AIRFLOW_API_GATEWAY_KEY=$(jq -r '.data.private_key' airflow_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/airflow/api-gateway/certs cert="$AIRFLOW_API_GATEWAY_CERT" key="$AIRFLOW_API_GATEWAY_KEY" ca="$AIRFLOW_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f airflow_api-gateway_cert.json
fi



# Vérifier si le certificat et la clé Vault existent déjà pour Airflow
if vault kv get -field=cert secret/airflow/airflow/certs > /dev/null 2>&1 && vault kv get -field=key secret/airflow/airflow/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS airflow pour le airflow existent déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_airflow/issue/airflow common_name="airflow"   ttl="72h" > airflow_airflow_cert.json

  # Extraire le certificat et la clé privée
  AIRFLOW_AIRFLOW_CA=$(jq -r '.data.ca_chain[0]' airflow_airflow_cert.json)
  AIRFLOW_AIRFLOW_CERT=$(jq -r '.data.certificate' airflow_airflow_cert.json)
  AIRFLOW_AIRFLOW_KEY=$(jq -r '.data.private_key' airflow_airflow_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/airflow/airflow/certs cert="$AIRFLOW_AIRFLOW_CERT" key="$AIRFLOW_AIRFLOW_KEY" ca="$AIRFLOW_AIRFLOW_CA"

  # Nettoyage des fichiers temporaires
  rm -f airflow_airflow_cert.json
fi


cat <<EOF > $AIRFLOW_AIRFLOW_KEY_PATH
$(printf "%s" "$AIRFLOW_AIRFLOW_KEY")
EOF

cat <<EOF > $AIRFLOW_AIRFLOW_CERT_PATH
$(printf "%s" "$AIRFLOW_AIRFLOW_CERT")
EOF

cat <<EOF > $AIRFLOW_AIRFLOW_PEM_PATH
$(printf "%s" "$AIRFLOW_AIRFLOW_KEY")
$(printf "%s" "$AIRFLOW_AIRFLOW_CERT")
EOF

cat <<EOF > $AIRFLOW_AIRFLOW_CA_PATH
$(printf "%s" "$AIRFLOW_AIRFLOW_CA")
EOF

chown airflow:airflow $AIRFLOW_AIRFLOW_KEY_PATH
chmod 600 $AIRFLOW_AIRFLOW_KEY_PATH

# Extraire le certificat et la clé privée de PostGreSQL
POSTGRESQL_AIRFLOW_CA_PATH=${POSTGRESQL_AIRFLOW_CA_PATH:-"/etc/ssl/postgresql/postgresql_airflow_ca.crt"}
POSTGRESQL_AIRFLOW_CA=$(vault kv get -field=ca secret/postgresql/airflow/certs)
POSTGRESQL_AIRFLOW_CERT=$(vault kv get -field=cert secret/postgresql/airflow/certs)
POSTGRESQL_AIRFLOW_KEY=$(vault kv get -field=key secret/postgresql/airflow/certs)

cat <<EOF > $POSTGRESQL_AIRFLOW_PEM_PATH
$(printf "%s" "$POSTGRESQL_AIRFLOW_KEY")
$(printf "%s" "$POSTGRESQL_AIRFLOW_CERT")
EOF

cat <<EOF > $POSTGRESQL_AIRFLOW_CA_PATH
$(printf "%s" "$POSTGRESQL_AIRFLOW_CA")
EOF

cat <<EOF > "${POSTGRESQL_AIRFLOW_KEY_PATH}"
$(printf "%s" "$POSTGRESQL_AIRFLOW_KEY")
EOF

cat <<EOF > "${POSTGRESQL_AIRFLOW_CERT_PATH}"
$(printf "%s" "$POSTGRESQL_AIRFLOW_CERT")
EOF

chown airflow:airflow $POSTGRESQL_AIRFLOW_KEY_PATH
chmod 600 $POSTGRESQL_AIRFLOW_KEY_PATH

# Extraire le certificat et la clé privée de Minio
MINIO_AIRFLOW_CA=$(vault kv get -field=ca secret/minio/airflow/certs)
MINIO_AIRFLOW_CERT=$(vault kv get -field=cert secret/minio/airflow/certs)
MINIO_AIRFLOW_KEY=$(vault kv get -field=key secret/minio/airflow/certs)

cat <<EOF > $MINIO_AIRFLOW_PEM_PATH
$(printf "%s" "$MINIO_AIRFLOW_KEY")
$(printf "%s" "$MINIO_AIRFLOW_CERT")
EOF

cat <<EOF > $MINIO_AIRFLOW_CA_PATH
$(printf "%s" "$MINIO_AIRFLOW_CA")
EOF

cat <<EOF > "${MINIO_AIRFLOW_KEY_PATH}"
$(printf "%s" "$POSTGRESQL_AIRFLOW_KEY")
EOF

cat <<EOF > "${MINIO_AIRFLOW_CERT_PATH}"
$(printf "%s" "$POSTGRESQL_AIRFLOW_CERT")
EOF

chown airflow:airflow $MINIO_AIRFLOW_KEY_PATH
chmod 600 $MINIO_AIRFLOW_KEY_PATH