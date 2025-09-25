#!/bin/bash
# Appeler le script Vault pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$VAULT_SERVICE_NAME/health)
    echo "Waiting for Vault service to be healthy."
    sleep 1
done

# Appeler le script Minio pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$MINIO_SERVICE_NAME/health)
    echo "Waiting for Minio service to be healthy."
    sleep 1
done

# Appeler le script Redis pour récupérer les certificats et la clé privée
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$REDIS_SERVICE_NAME/health)
# Vous pouvez ajouter une logique conditionnelle ici
until [ $HTTP_CODE -eq 200 ]; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$REDIS_SERVICE_NAME/health)
    echo "Waiting for Redis service to be healthy."
    sleep 1
done

if [ ${SERVICE_NAME} != ${AIRFLOW_API_SERVER_SERVICE_NAME} ]; then
  echo "Waiting for Airflow API server"
  # Appeler le script Airflow API-server pour récupérer les certificats et la clé privée
  HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$AIRFLOW_API_SERVER_SERVICE_NAME/health)
  # Vous pouvez ajouter une logique conditionnelle ici
  until [ $HTTP_CODE -eq 200 ]; do
      HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$AIRFLOW_API_SERVER_SERVICE_NAME/health)
      echo "Waiting for Airflow API server service to be healthy."
      sleep 1
  done
fi

# Se connecter à Vault et récupérer un token
export VAULT_SKIP_VERIFY="1"

mkdir -p $(dirname $MINIO_AIRFLOW_PEM_PATH) $(dirname $MINIO_AIRFLOW_CA_PATH)

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
vault kv get -field=certificate secret/$VAULT_USERNAME/ca > ${VAULT_USERNAME}_ca.crt
vault kv get -field=certificate secret/postgresql/ca > postgresql_ca.crt
vault kv get -field=certificate secret/redis/ca > redis_ca.crt
if [ ${SERVICE_NAME} != ${AIRFLOW_API_SERVER_SERVICE_NAME} ]; then
  vault kv get -field=certificate secret/${AIRFLOW_API_SERVER_SERVICE_NAME}/ca > ${AIRFLOW_API_SERVER_SERVICE_NAME}_ca.crt
fi

mkdir -p $(dirname $AIRFLOW_PEM_PATH)  
mkdir -p $(dirname $AIRFLOW_CA_PATH)
mkdir -p $(dirname $AIRFLOW_KEY_PATH)
mkdir -p $(dirname $AIRFLOW_CERT_PATH)
mkdir -p $(dirname $AIRFLOW_AIRFLOW_PEM_PATH)  
mkdir -p $(dirname $AIRFLOW_AIRFLOW_CA_PATH)
mkdir -p $(dirname $AIRFLOW_AIRFLOW_KEY_PATH)
mkdir -p $(dirname $AIRFLOW_AIRFLOW_CERT_PATH)
#mkdir -p $(dirname $AIRFLOW_FERNET_KEY_PATH)

cp ${VAULT_USERNAME}_ca.crt $AIRFLOW_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp ${VAULT_USERNAME}_ca.crt /usr/local/share/ca-certificates/
cp postgresql_ca.crt /usr/local/share/ca-certificates/
cp redis_ca.crt /usr/local/share/ca-certificates/
#cp airflow_fernet_key.txt /usr/local/share/ca-certificates/
if [ ${SERVICE_NAME} != ${AIRFLOW_API_SERVER_SERVICE_NAME} ]; then
  cp ${AIRFLOW_API_SERVER_SERVICE_NAME}_ca.crt /usr/local/share/ca-certificates/
  cat ${AIRFLOW_API_SERVER_SERVICE_NAME}_ca.crt >> $(python -c "import certifi; print(certifi.where())")
fi

cat ${VAULT_USERNAME}_ca.crt >> $(python -c "import certifi; print(certifi.where())")
cat redis_ca.crt >> $(python -c "import certifi; print(certifi.where())")

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

vault write -format=json pki_${VAULT_USERNAME}/issue/${VAULT_USERNAME} common_name="${VAULT_USERNAME}" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > ${VAULT_USERNAME}_cert.json

cat <<EOF > $AIRFLOW_PEM_PATH
$(jq -r '.data.private_key' ${VAULT_USERNAME}_cert.json)
$(jq -r '.data.certificate' ${VAULT_USERNAME}_cert.json)
$(jq -r '.data.issuing_ca' ${VAULT_USERNAME}_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "AIRFLOW_CERT_PATH = $AIRFLOW_CERT_PATH"
cat <<EOF > $AIRFLOW_CERT_PATH
$(jq -r '.data.certificate' ${VAULT_USERNAME}_cert.json)
EOF
echo "AIRFLOW_KEY_PATH = $AIRFLOW_KEY_PATH"
cat <<EOF > $AIRFLOW_KEY_PATH
$(jq -r '.data.private_key' ${VAULT_USERNAME}_cert.json)
EOF

chown airflow:airflow $AIRFLOW_KEY_PATH
chmod 600 $AIRFLOW_KEY_PATH


# Définir les permissions pour les fichiers de certificat et de clé
chown airflow:airflow $AIRFLOW_PEM_PATH
chmod 400 $AIRFLOW_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f ${VAULT_USERNAME}_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/${VAULT_USERNAME}/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/${VAULT_USERNAME}/keyfile value=$key_value
fi

AIRFLOW_SECRET_KEY=$(vault kv get -field=value secret/${VAULT_USERNAME}/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/${VAULT_USERNAME}/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/${VAULT_USERNAME}/internal_keyfile value=$key_value
fi

AIRFLOW_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/${VAULT_USERNAME}/internal_keyfile)

cat <<EOF > $AIRFLOW_INTERNAL_SECRET_KEY_PATH
$(printf "%s" "$AIRFLOW_INTERNAL_SECRET_KEY")
EOF


# Vérifier si le certificat et la clé Vault pour API-Gateway existent déjà ou les créer
if vault kv get -field=cert secret/${VAULT_USERNAME}/api-gateway/certs > /dev/null 2>&1 && vault kv get -field=key secret/${VAULT_USERNAME}/api-gateway/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS ${VAULT_USERNAME} pour le service api-gateway existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_${VAULT_USERNAME}/issue/${VAULT_USERNAME} common_name="${VAULT_USERNAME}"   ttl="72h" > ${VAULT_USERNAME}_api-gateway_cert.json

  # Extraire le certificat et la clé privée
  AIRFLOW_API_GATEWAY_CA=$(jq -r '.data.ca_chain[0]' ${VAULT_USERNAME}_api-gateway_cert.json)
  AIRFLOW_API_GATEWAY_CERT=$(jq -r '.data.certificate' ${VAULT_USERNAME}_api-gateway_cert.json)
  AIRFLOW_API_GATEWAY_KEY=$(jq -r '.data.private_key' ${VAULT_USERNAME}_api-gateway_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/${VAULT_USERNAME}/api-gateway/certs cert="$AIRFLOW_API_GATEWAY_CERT" key="$AIRFLOW_API_GATEWAY_KEY" ca="$AIRFLOW_API_GATEWAY_CA"

  # Nettoyage des fichiers temporaires
  rm -f ${VAULT_USERNAME}_api-gateway_cert.json
fi



# Vérifier si le certificat et la clé Vault existent déjà pour Airflow
if vault kv get -field=cert secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs > /dev/null 2>&1 && vault kv get -field=key secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS ${VAULT_USERNAME} pour le ${VAULT_USERNAME} existent déjà"
  AIRFLOW_AIRFLOW_CA=$(vault kv get -field=ca secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs)
  AIRFLOW_AIRFLOW_CERT=$(vault kv get -field=cert secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs)
  AIRFLOW_AIRFLOW_KEY=$(vault kv get -field=key secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs)
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_${VAULT_USERNAME}/issue/${VAULT_USERNAME} common_name="${VAULT_USERNAME}"   ttl="72h" > ${VAULT_USERNAME}_${VAULT_USERNAME}_cert.json

  # Extraire le certificat et la clé privée
  AIRFLOW_AIRFLOW_CA=$(jq -r '.data.ca_chain[0]' ${VAULT_USERNAME}_${VAULT_USERNAME}_cert.json)
  AIRFLOW_AIRFLOW_CERT=$(jq -r '.data.certificate' ${VAULT_USERNAME}_${VAULT_USERNAME}_cert.json)
  AIRFLOW_AIRFLOW_KEY=$(jq -r '.data.private_key' ${VAULT_USERNAME}_${VAULT_USERNAME}_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/${VAULT_USERNAME}/${VAULT_USERNAME}/certs cert="$AIRFLOW_AIRFLOW_CERT" key="$AIRFLOW_AIRFLOW_KEY" ca="$AIRFLOW_AIRFLOW_CA"

  # Nettoyage des fichiers temporaires
  rm -f ${VAULT_USERNAME}_${VAULT_USERNAME}_cert.json
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
echo "Getting PostgreSQL certificates"
POSTGRESQL_AIRFLOW_CA=$(vault kv get -field=ca secret/postgresql/$SERVICE_NAME/certs)
POSTGRESQL_AIRFLOW_CERT=$(vault kv get -field=cert secret/postgresql/$SERVICE_NAME/certs)
POSTGRESQL_AIRFLOW_KEY=$(vault kv get -field=key secret/postgresql/$SERVICE_NAME/certs)

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
echo "Getting Minio certificates"
MINIO_AIRFLOW_CA=$(vault kv get -field=ca secret/minio/${VAULT_USERNAME}/certs)
MINIO_AIRFLOW_CERT=$(vault kv get -field=cert secret/minio/${VAULT_USERNAME}/certs)
MINIO_AIRFLOW_KEY=$(vault kv get -field=key secret/minio/${VAULT_USERNAME}/certs)

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


# Extraire le certificat et la clé privée de Redis
echo "Getting Redis certificates"
REDIS_AIRFLOW_CA=$(vault kv get -field=ca secret/redis/$SERVICE_NAME/certs)
REDIS_AIRFLOW_CERT=$(vault kv get -field=cert secret/redis/$SERVICE_NAME/certs)
REDIS_AIRFLOW_KEY=$(vault kv get -field=key secret/redis/$SERVICE_NAME/certs)

cat <<EOF > $REDIS_AIRFLOW_PEM_PATH
$(printf "%s" "$REDIS_AIRFLOW_KEY")
$(printf "%s" "$REDIS_AIRFLOW_CERT")
EOF

cat <<EOF > $REDIS_AIRFLOW_CA_PATH
$(printf "%s" "$REDIS_AIRFLOW_CA")
EOF

cat <<EOF > "${REDIS_AIRFLOW_KEY_PATH}"
$(printf "%s" "$REDIS_AIRFLOW_KEY")
EOF

cat <<EOF > "${REDIS_AIRFLOW_CERT_PATH}"
$(printf "%s" "$REDIS_AIRFLOW_CERT")
EOF

chown airflow:airflow $REDIS_AIRFLOW_KEY_PATH
chmod 600 $REDIS_AIRFLOW_KEY_PATH

echo "Getting Airflow services certificates"
# All Airflow services must be able to communicate with Airflow API server
if [ "${SERVICE_NAME}" == "${AIRFLOW_API_SERVER_SERVICE_NAME}" ]; then
  #Liste des services pour lesquels générer les certificats
  services=("airflow-worker" "airflow-scheduler" "airflow-triggerer" "airflow-dag-processor")

  # Boucle sur chaque service
  for service_name in "${services[@]}"; do
    echo "Traitement du service : $service_name"

    # Vérifier si le certificat et la clé Vault existent déjà
    if vault kv get -field=cert "secret/${SERVICE_NAME}/${service_name}/certs" > /dev/null 2>&1 && \
      vault kv get -field=key "secret/${SERVICE_NAME}/${service_name}/certs" > /dev/null 2>&1; then
      echo "Le certificat mTLS ${SERVICE_NAME} pour le ${service_name} existe déjà"
      CA=$(vault kv get -field=ca "secret/${SERVICE_NAME}/${service_name}/certs")
      CERT=$(vault kv get -field=cert "secret/${SERVICE_NAME}/${service_name}/certs")
      KEY=$(vault kv get -field=key "secret/${SERVICE_NAME}/${service_name}/certs")
    else
      # Générer le certificat et la clé pour Vault
      echo "Générer le certificat et la clé pour Vault pour ${service_name}"
      vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="${SERVICE_NAME}" ttl="72h" > "${SERVICE_NAME}_${service_name}_cert.json"

      # Extraire le certificat et la clé privée
      CA=$(jq -r '.data.ca_chain[0]' "${SERVICE_NAME}_${service_name}_cert.json")
      CERT=$(jq -r '.data.certificate' "${SERVICE_NAME}_${service_name}_cert.json")
      KEY=$(jq -r '.data.private_key' "${SERVICE_NAME}_${service_name}_cert.json")

      # Enregistrer le certificat et la clé privée dans Vault
      vault kv put "secret/${SERVICE_NAME}/${service_name}/certs" cert="$CERT" key="$KEY" ca="$CA"

      # Nettoyage des fichiers temporaires
      rm -f "${SERVICE_NAME}_${service_name}_cert.json"
    fi
    
    
    # Écrire les fichiers de certificats et clés
    KEY_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${service_name}.key"
    CERT_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${service_name}.crt"
    PEM_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${service_name}.pem"
    CA_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${service_name}_ca.crt"

    cat <<EOF > "${KEY_PATH}"
$(printf "%s" "$KEY")
EOF

  cat <<EOF > "${CERT_PATH}"
$(printf "%s" "$CERT")
EOF

  cat <<EOF > "${PEM_PATH}"
$(printf "%s" "$KEY")
$(printf "%s" "$CERT")
EOF

  cat <<EOF > "${CA_PATH}"
$(printf "%s" "$CA")
EOF

    echo "Traitement terminé pour le service : $service_name"
  done
else
  AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CA=$(vault kv get -field=ca secret/${AIRFLOW_API_SERVER_SERVICE_NAME}/$SERVICE_NAME/certs)
  AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CERT=$(vault kv get -field=cert secret/${AIRFLOW_API_SERVER_SERVICE_NAME}/$SERVICE_NAME/certs)
  AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY=$(vault kv get -field=key secret/${AIRFLOW_API_SERVER_SERVICE_NAME}/$SERVICE_NAME/certs)

  cat <<EOF > $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_PEM_PATH
$(printf "%s" "$AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY")
$(printf "%s" "$AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CERT")
EOF

cat <<EOF > $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CA_PATH
$(printf "%s" "$AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CA")
EOF

cat <<EOF > $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY_PATH
$(printf "%s" "$AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY")
EOF

cat <<EOF > $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CERT_PATH
$(printf "%s" "$AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CERT")
EOF

chown airflow:airflow $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY_PATH
chmod 600 $AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY_PATH
fi