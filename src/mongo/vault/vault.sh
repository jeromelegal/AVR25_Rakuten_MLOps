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

mkdir -p $(dirname $MONGODB_PEM_PATH)  $(dirname $MONGODB_CA_PATH) $(dirname $MONGODB_MONGODB_PEM_PATH) $(dirname $MONGODB_MONGODB_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/mongodb/ca > mongodb_ca.crt

cp mongodb_ca.crt $MONGODB_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp mongodb_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_mongodb/issue/mongodb common_name="mongodb" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > mongodb_cert.json

cat <<EOF > $MONGODB_PEM_PATH
$(jq -r '.data.private_key' mongodb_cert.json)
$(jq -r '.data.certificate' mongodb_cert.json)
$(jq -r '.data.issuing_ca' mongodb_cert.json)
EOF

# Extraire le certificat et la clé privée

echo "MONGODB_CERT_PATH = $MONGODB_CERT_PATH"
cat <<EOF > $MONGODB_CERT_PATH
$(jq -r '.data.certificate' mongodb_cert.json)
EOF
echo "MONGODB_KEY_PATH = $MONGODB_KEY_PATH"
cat <<EOF > $MONGODB_KEY_PATH
$(jq -r '.data.private_key' mongodb_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown mongodb:mongodb $MONGODB_PEM_PATH
chmod 400 $MONGODB_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f mongo_service.json

# Vérifier si le certificat et la clé Backend existent déjà
if vault kv get -field=cert secret/mongodb/mongodb/certs > /dev/null 2>&1 && vault kv get -field=key secret/mongodb/mongodb/certs > /dev/null 2>&1; then
  echo "Le certificat et la clé Backend existent déjà"
  MONGODB_MONGODB_CA=$(vault kv get -field=ca secret/mongodb/mongodb/certs)
  MONGODB_MONGODB_CERT=$(vault kv get -field=cert secret/mongodb/mongodb/certs)
  MONGODB_MONGODB_KEY=$(vault kv get -field=key secret/mongodb/mongodb/certs)  

else
  # Générer le certificat et la clé pour Backend
  echo "Générer le certificat et la clé pour Backend"
  vault write -format=json pki_mongodb/issue/mongodb common_name="mongodb"   ttl="72h" > mongodb_mongodb_cert.json

  # Extraire le certificat et la clé privée
  MONGODB_MONGODB_CA=$(jq -r '.data.ca_chain' mongodb_mongodb_cert.json)
  MONGODB_MONGODB_CERT=$(jq -r '.data.certificate' mongodb_mongodb_cert.json)
  MONGODB_MONGODB_KEY=$(jq -r '.data.private_key' mongodb_mongodb_cert.json)
  
  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/mongodb/mongodb/certs cert="$MONGODB_MONGODB_CERT" key="$MONGODB_MONGODB_KEY" ca="$MONGODB_MONGODB_CA"
  # Nettoyage des fichiers temporaires
  rm -f mongodb_mongodb_cert.json
fi

cat <<EOF > $MONGODB_MONGODB_PEM_PATH
$(printf "%s" "$MONGODB_MONGODB_KEY")
$(printf "%s" "$MONGODB_MONGODB_CERT")
EOF

printf "%s" $MONGODB_MONGODB_CA > $MONGODB_MONGODB_CA_PATH

key_value=$(openssl rand -base64 741 | tr -d '\n' )

vault kv put secret/mongodb/keyfile value=$key_value

retrieve=$(vault kv get -field=value secret/mongodb/keyfile)

mkdir -p /etc/ssl/mongodb/
echo $retrieve > /etc/ssl/mongodb/mongodb-keyfile
chmod 600 /etc/ssl/mongodb/mongodb-keyfile

# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/mongodb/api-mongodb/certs > /dev/null 2>&1 && vault kv get -field=key secret/mongodb/api-mongodb/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS mongodb pour le api-mongodb existent déjà"
else
  # Générer le certificat et la clé pour Vault
  echo "Générer le certificat et la clé pour Vault"
  vault write -format=json pki_mongodb/issue/mongodb common_name="mongodb"   ttl="72h" > mongodb_api-mongodb_cert.json

  # Extraire le certificat et la clé privée
  MONGODB_API_MONGODB_CA=$(jq -r '.data.ca_chain[0]' mongodb_api-mongodb_cert.json)
  MONGODB_API_MONGODB_CERT=$(jq -r '.data.certificate' mongodb_api-mongodb_cert.json)
  MONGODB_API_MONGODB_KEY=$(jq -r '.data.private_key' mongodb_api-mongodb_cert.json)

  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/mongodb/api-mongodb/certs cert="$MONGODB_API_MONGODB_CERT" key="$MONGODB_API_MONGODB_KEY" ca="$MONGODB_API_MONGODB_CA"

  # Nettoyage des fichiers temporaires
  rm -f vault_service_cert.json
fi
