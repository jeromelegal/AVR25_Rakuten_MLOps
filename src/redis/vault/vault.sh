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

# Vérifier si le certificat et la clé Backend existent déjà
if vault kv get -field=cert secret/redis/redis/certs > /dev/null 2>&1 && vault kv get -field=key secret/redis/redis/certs > /dev/null 2>&1; then
  echo "Le certificat et la clé Backend existent déjà"
  REDIS_REDIS_CA=$(vault kv get -field=ca secret/redis/redis/certs)
  REDIS_REDIS_CERT=$(vault kv get -field=cert secret/redis/redis/certs)
  REDIS_REDIS_KEY=$(vault kv get -field=key secret/redis/redis/certs)  

else
  # Générer le certificat et la clé pour Backend
  echo "Générer le certificat et la clé pour Backend"
  vault write -format=json pki_redis/issue/redis common_name="redis"   ttl="72h" > redis_redis_cert.json

  # Extraire le certificat et la clé privée
  REDIS_REDIS_CA=$(jq -r '.data.ca_chain' redis_redis_cert.json)
  REDIS_REDIS_CERT=$(jq -r '.data.certificate' redis_redis_cert.json)
  REDIS_REDIS_KEY=$(jq -r '.data.private_key' redis_redis_cert.json)
  
  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/redis/redis/certs cert="$REDIS_REDIS_CERT" key="$REDIS_REDIS_KEY" ca="$REDIS_REDIS_CA"
  # Nettoyage des fichiers temporaires
  rm -f redis_redis_cert.json
fi

cat <<EOF > $REDIS_REDIS_PEM_PATH
$(printf "%s" "$REDIS_REDIS_KEY")
$(printf "%s" "$REDIS_REDIS_CERT")
EOF

printf "%s" $REDIS_REDIS_CA > $REDIS_REDIS_CA_PATH

key_value=$(openssl rand -base64 741 | tr -d '\n' )

vault kv put secret/redis/keyfile value=$key_value

retrieve=$(vault kv get -field=value secret/redis/keyfile)

mkdir -p /etc/ssl/redis/
echo $retrieve > /etc/ssl/redis/redis-keyfile
chmod 600 /etc/ssl/redis/redis-keyfile

# # Vérifier si le certificat et la clé Vault existent déjà
# if vault kv get -field=cert secret/redis/mlflow/certs > /dev/null 2>&1 && vault kv get -field=key secret/redis/mlflow/certs > /dev/null 2>&1; then
#   echo "Le certificat mTLS redis pour le service mlflow existe déjà"
#   REDIS_MLFLOW_CA=$(vault kv get -field=ca secret/redis/mlflow/certs)
#   REDIS_MLFLOW_CERT=$(vault kv get -field=cert secret/redis/mlflow/certs)
#   REDIS_MLFLOW_KEY=$(vault kv get -field=key secret/redis/mlflow/certs)  
# else
#   # Générer le certificat et la clé pour Vault
#   echo "Générer le certificat et la clé pour Vault"
#   vault write -format=json pki_redis/issue/redis common_name="redis"   ttl="72h" > redis_mlflow_cert.json
#   # TODO: Define certificate duration as an env variable

#   # Extraire le certificat et la clé privée
#   REDIS_MLFLOW_CA=$(jq -r '.data.ca_chain[0]' redis_mlflow_cert.json)
#   REDIS_MLFLOW_CERT=$(jq -r '.data.certificate' redis_mlflow_cert.json)
#   REDIS_MLFLOW_KEY=$(jq -r '.data.private_key' redis_mlflow_cert.json)

#   # Enregistrer le certificat et la clé privée dans Vault
#   vault kv put secret/redis/mlflow/certs cert="$REDIS_MLFLOW_CERT" key="$REDIS_MLFLOW_KEY" ca="$REDIS_MLFLOW_CA"
#   # Nettoyage des fichiers temporaires
#   rm -f vault_service_cert.json
# fi

# # Vérifier si le certificat et la clé Vault existent déjà
# if vault kv get -field=cert secret/redis/airflow/certs > /dev/null 2>&1 && vault kv get -field=key secret/redis/airflow/certs > /dev/null 2>&1; then
#   echo "Le certificat mTLS redis pour le service airflow existe déjà"
#   REDIS_AIRFLOW_CA=$(vault kv get -field=ca secret/redis/airflow/certs)
#   REDIS_AIRFLOW_CERT=$(vault kv get -field=cert secret/redis/airflow/certs)
#   REDIS_AIRFLOW_KEY=$(vault kv get -field=key secret/redis/airflow/certs)
# else
#   # Générer le certificat et la clé pour Vault
#   echo "Générer le certificat et la clé pour Vault"
#   vault write -format=json pki_redis/issue/redis common_name="redis"   ttl="72h" > redis_airflow_cert.json
#   # TODO: Define certificate duration as an env variable

#   # Extraire le certificat et la clé privée
#   REDIS_AIRFLOW_CA=$(jq -r '.data.ca_chain[0]' redis_airflow_cert.json)
#   REDIS_AIRFLOW_CERT=$(jq -r '.data.certificate' redis_airflow_cert.json)
#   REDIS_AIRFLOW_KEY=$(jq -r '.data.private_key' redis_airflow_cert.json)

#   # Enregistrer le certificat et la clé privée dans Vault
#   vault kv put secret/redis/airflow/certs cert="$REDIS_AIRFLOW_CERT" key="$REDIS_AIRFLOW_KEY" ca="$REDIS_AIRFLOW_CA"
#   # Nettoyage des fichiers temporaires
#   rm -f vault_service_cert.json
# fi

# cat <<EOF > $REDIS_MLFLOW_PEM_PATH
# $(printf "%s" "$REDIS_MLFLOW_KEY")
# $(printf "%s" "$REDIS_MLFLOW_CERT")
# EOF

# printf "%s" $REDIS_MLFLOW_CA > $REDIS_MLFLOW_CA_PATH

