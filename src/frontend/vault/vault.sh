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

mkdir -p $(dirname $FRONTEND_PEM_PATH)  $(dirname $FRONTEND_CA_PATH) $(dirname $API_GATEWAY_FRONTEND_PEM_PATH) $(dirname $API_GATEWAY_FRONTEND_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD ; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/api-gateway/ca > api-gateway_ca.crt
vault kv get -field=certificate secret/frontend/ca > frontend_ca.crt

mkdir -p $(dirname $FRONTEND_PEM_PATH)
mkdir -p $(dirname $FRONTEND_CA_PATH)
mkdir -p $(dirname $FRONTEND_KEY_PATH)
mkdir -p $(dirname $FRONTEND_CERT_PATH)

cp frontend_ca.crt $FRONTEND_CA_PATH


# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp api-gateway_ca.crt /usr/local/share/ca-certificates/
cp frontend_ca.crt /usr/local/share/ca-certificates/


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

vault write -format=json pki_frontend/issue/frontend common_name="frontend" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > frontend_cert.json

cat <<EOF > $FRONTEND_PEM_PATH
$(jq -r '.data.private_key' frontend_cert.json)
$(jq -r '.data.certificate' frontend_cert.json)
$(jq -r '.data.issuing_ca' frontend_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "FRONTEND_CERT_PATH = $FRONTEND_CERT_PATH"
cat <<EOF > $FRONTEND_CERT_PATH
$(jq -r '.data.certificate' frontend_cert.json)
EOF
echo "FRONTEND_KEY_PATH = $FRONTEND_KEY_PATH"
cat <<EOF > $FRONTEND_KEY_PATH
$(jq -r '.data.private_key' frontend_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown frontend:frontend $FRONTEND_PEM_PATH
chmod 400 $FRONTEND_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f frontend_cert.json

# Vérifier si le certificat et la clé FRONTEND existent déjà
if ! vault kv get -field=value secret/frontend/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/frontend/keyfile value=$key_value
fi

FRONTEND_SECRET_KEY=$(vault kv get -field=value secret/frontend/keyfile)

# Vérifier si le certificat et la clé FRONTEND existent déjà
if ! vault kv get -field=value secret/frontend/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/frontend/internal_keyfile value=$key_value
fi

FRONTEND_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/frontend/internal_keyfile)






# Vérifier si le certificat et la clé Vault existent déjà
if vault kv get -field=cert secret/frontend/reverse-proxy/certs > /dev/null 2>&1 && vault kv get -field=key secret/frontend/reverse-proxy/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS frontend pour le reverse-proxy existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_frontend/issue/frontend common_name="frontend"   ttl="72h" > frontend_reverse-proxy_cert.json

  # Extraire le certificat et la clé privée
  FRONTEND_REVERSE_PROXY_CA=$(jq -r '.data.ca_chain[0]' frontend_reverse-proxy_cert.json)
  FRONTEND_REVERSE_PROXY_CERT=$(jq -r '.data.certificate' frontend_reverse-proxy_cert.json)
  FRONTEND_REVERSE_PROXY_KEY=$(jq -r '.data.private_key' frontend_reverse-proxy_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/frontend/reverse-proxy/certs cert="$FRONTEND_REVERSE_PROXY_CERT" key="$FRONTEND_REVERSE_PROXY_KEY" ca="$FRONTEND_REVERSE_PROXY_CA"

  # Nettoyage des fichiers temporaires
  rm -f frontend_reverse-proxy_cert.json
fi







# Extraire le certificat et la clé privée
API_GATEWAY_FRONTEND_CA=$(vault kv get -field=ca secret/api-gateway/frontend/certs)
API_GATEWAY_FRONTEND_CERT=$(vault kv get -field=cert secret/api-gateway/frontend/certs)
API_GATEWAY_FRONTEND_KEY=$(vault kv get -field=key secret/api-gateway/frontend/certs)

cat <<EOF > $API_GATEWAY_FRONTEND_PEM_PATH
$(printf "%s" "$API_GATEWAY_FRONTEND_KEY")
$(printf "%s" "$API_GATEWAY_FRONTEND_CERT")
EOF

cat <<EOF > $API_GATEWAY_FRONTEND_CA_PATH
$(printf "%s" "$API_GATEWAY_FRONTEND_CA")
EOF

cat <<EOF > $API_GATEWAY_FRONTEND_KEY_PATH
$(printf "%s" "$API_GATEWAY_FRONTEND_KEY")
EOF

cat <<EOF > $API_GATEWAY_FRONTEND_CERT_PATH
$(printf "%s" "$API_GATEWAY_FRONTEND_CERT")
EOF

