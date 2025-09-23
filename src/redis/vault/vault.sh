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

mkdir -p $(dirname $REDIS_PEM_PATH)  $(dirname $REDIS_CA_PATH) $(dirname $REDIS_REDIS_PEM_PATH) $(dirname $REDIS_REDIS_CA_PATH) # $(dirname $REDIS_MLFLOW_PEM_PATH) $(dirname $REDIS_MLFLOW_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/redis/ca > redis_ca.crt
# vault kv get -field=certificate secret/mlflow/ca > mlflow_ca.crt

cp redis_ca.crt $REDIS_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp redis_ca.crt /usr/local/share/ca-certificates/
# cp mlflow_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_redis/issue/redis common_name="redis" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > redis_cert.json

cat <<EOF > $REDIS_PEM_PATH
$(jq -r '.data.private_key' redis_cert.json)
$(jq -r '.data.certificate' redis_cert.json)
$(jq -r '.data.issuing_ca' redis_cert.json)
EOF

# Extraire le certificat et la clé privée

echo "REDIS_CERT_PATH = $REDIS_CERT_PATH"
cat <<EOF > $REDIS_CERT_PATH
$(jq -r '.data.certificate' redis_cert.json)
EOF
echo "REDIS_KEY_PATH = $REDIS_KEY_PATH"
cat <<EOF > $REDIS_KEY_PATH
$(jq -r '.data.private_key' redis_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown redis:redis $REDIS_PEM_PATH
chmod 400 $REDIS_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f redis_cert.json

#Liste des services pour lesquels générer les certificats
services=("${SERVICE_NAME}")

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