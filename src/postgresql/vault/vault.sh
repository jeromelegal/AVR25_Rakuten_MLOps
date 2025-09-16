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

mkdir -p  /etc/ssl/${SERVICE_NAME}

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 seconde..."
    sleep 1
done


services=("${SERVICE_NAME}" "vault" "consul")

# Boucle sur chaque service
for service_name in "${services[@]}"; do
  vault kv get -field=certificate secret/${service_name}/ca > ${service_name}_ca.crt
  cp ${service_name}_ca.crt /usr/local/share/ca-certificates/
done

cp ${SERVICE_NAME}_ca.crt /etc/ssl/${SERVICE_NAME}/

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

vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="${SERVICE_NAME}" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > ${SERVICE_NAME}_cert.json

cat <<EOF > /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.pem
$(jq -r '.data.private_key' ${SERVICE_NAME}_cert.json)
$(jq -r '.data.certificate' ${SERVICE_NAME}_cert.json)
EOF

# Extraire le certificat et la clé privée


cat <<EOF > /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.crt
$(jq -r '.data.certificate' ${SERVICE_NAME}_cert.json)
EOF
cat <<EOF > /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.key
$(jq -r '.data.private_key' ${SERVICE_NAME}_cert.json)
EOF
cat <<EOF > /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_ca.crt
$(jq -r '.data.ca_chain[0]' ${SERVICE_NAME}_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown ${SERVICE_NAME}:${SERVICE_NAME} /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.pem
chmod 400 /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.pem

# Nettoyage des fichiers temporaires
rm -f ${SERVICE_NAME}_cert.json

key_value=$(openssl rand -base64 741 | tr -d '\n')

vault kv put secret/${SERVICE_NAME}/keyfile value=$key_value

retrieve=$(vault kv get -field=value secret/${SERVICE_NAME}/keyfile)

mkdir -p /etc/ssl/${SERVICE_NAME}/
echo $retrieve > /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}-keyfile
chmod 600 /etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}-keyfile





#Liste des services pour lesquels générer les certificats
services=("${SERVICE_NAME}" "api-postgresql" "mlflow" "airflow")

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

    if [[ "$service_name" == "api-postgresql" ]]; then
        vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="db_manager_user" ttl="72h" > "${SERVICE_NAME}_${service_name}_cert.json"
    elif [[ "$service_name" == "mlflow" ]]; then
        vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="${MLFLOW_USER}" ttl="72h" > "${SERVICE_NAME}_${service_name}_cert.json"
    elif [[ "$service_name" == "airflow" ]]; then
        vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="${AIRFLOW_USER}" ttl="72h" > "${SERVICE_NAME}_${service_name}_cert.json"
    else
        vault write -format=json pki_${SERVICE_NAME}/issue/${SERVICE_NAME} common_name="${service_name}" ttl="72h" > "${SERVICE_NAME}_${service_name}_cert.json"
    fi

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

echo "KEY_PATH $KEY_PATH"
echo "CERT_PATH $CERT_PATH"
echo "PEM_PATH $PEM_PATH"
echo "CA_PATH $CA_PATH"


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






