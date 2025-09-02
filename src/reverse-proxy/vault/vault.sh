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

mkdir -p $(dirname $REVERSE_PROXY_PEM_PATH)  $(dirname $REVERSE_PROXY_CA_PATH) $(dirname $FRONTEND_REVERSE_PROXY_PEM_PATH) $(dirname $FRONTEND_REVERSE_PROXY_CA_PATH) 

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD ; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/frontend/ca > frontend_ca.crt
vault kv get -field=certificate secret/reverse-proxy/ca > reverse-proxy_ca.crt

mkdir -p $(dirname $REVERSE_PROXY_PEM_PATH)
mkdir -p $(dirname $REVERSE_PROXY_CA_PATH)
mkdir -p $(dirname $REVERSE_PROXY_KEY_PATH)
mkdir -p $(dirname $REVERSE_PROXY_CERT_PATH)

cp reverse-proxy_ca.crt $REVERSE_PROXY_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp frontend_ca.crt /usr/local/share/ca-certificates/
cp reverse-proxy_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_reverse-proxy/issue/reverse-proxy common_name="reverse-proxy" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > reverse-proxy_cert.json

cat <<EOF > $REVERSE_PROXY_PEM_PATH
$(jq -r '.data.private_key' reverse-proxy_cert.json)
$(jq -r '.data.certificate' reverse-proxy_cert.json)
$(jq -r '.data.issuing_ca' reverse-proxy_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "REVERSE_PROXY_CERT_PATH = $REVERSE_PROXY_CERT_PATH"
cat <<EOF > $REVERSE_PROXY_CERT_PATH
$(jq -r '.data.certificate' reverse-proxy_cert.json)
EOF
echo "REVERSE_PROXY_KEY_PATH = $REVERSE_PROXY_KEY_PATH"
cat <<EOF > $REVERSE_PROXY_KEY_PATH
$(jq -r '.data.private_key' reverse-proxy_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown reverse-proxy:reverse-proxy $REVERSE_PROXY_PEM_PATH
chmod 400 $REVERSE_PROXY_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f reverse-proxy_cert.json

# Vérifier si le certificat et la clé REVERSE_PROXY existent déjà
if ! vault kv get -field=value secret/reverse-proxy/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/reverse-proxy/keyfile value=$key_value
fi

REVERSE_PROXY_SECRET_KEY=$(vault kv get -field=value secret/reverse-proxy/keyfile)

# Vérifier si le certificat et la clé REVERSE_PROXY existent déjà
if ! vault kv get -field=value secret/reverse-proxy/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/reverse-proxy/internal_keyfile value=$key_value
fi

REVERSE_PROXY_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/reverse-proxy/internal_keyfile)

# Extraire le certificat et la clé privée
FRONTEND_REVERSE_PROXY_CA=$(vault kv get -field=ca secret/frontend/reverse-proxy/certs)
FRONTEND_REVERSE_PROXY_CERT=$(vault kv get -field=cert secret/frontend/reverse-proxy/certs)
FRONTEND_REVERSE_PROXY_KEY=$(vault kv get -field=key secret/frontend/reverse-proxy/certs)

cat <<EOF > $FRONTEND_REVERSE_PROXY_PEM_PATH
$(printf "%s" "$FRONTEND_REVERSE_PROXY_KEY")
$(printf "%s" "$FRONTEND_REVERSE_PROXY_CERT")
EOF

cat <<EOF > $FRONTEND_REVERSE_PROXY_CA_PATH
$(printf "%s" "$FRONTEND_REVERSE_PROXY_CA")
EOF

cat <<EOF > $FRONTEND_REVERSE_PROXY_KEY_PATH
$(printf "%s" "$FRONTEND_REVERSE_PROXY_KEY")
EOF

cat <<EOF > $FRONTEND_REVERSE_PROXY_CERT_PATH
$(printf "%s" "$FRONTEND_REVERSE_PROXY_CERT")
EOF



# Extraire le certificat et la clé privée
API_GATEWAY_REVERSE_PROXY_CA=$(vault kv get -field=ca secret/api-gateway/reverse-proxy/certs)
API_GATEWAY_REVERSE_PROXY_CERT=$(vault kv get -field=cert secret/api-gateway/reverse-proxy/certs)
API_GATEWAY_REVERSE_PROXY_KEY=$(vault kv get -field=key secret/api-gateway/reverse-proxy/certs)

cat <<EOF > $API_GATEWAY_REVERSE_PROXY_PEM_PATH
$(printf "%s" "$API_GATEWAY_REVERSE_PROXY_KEY")
$(printf "%s" "$API_GATEWAY_REVERSE_PROXY_CERT")
EOF

cat <<EOF > $API_GATEWAY_REVERSE_PROXY_CA_PATH
$(printf "%s" "$API_GATEWAY_REVERSE_PROXY_CA")
EOF

cat <<EOF > $API_GATEWAY_REVERSE_PROXY_KEY_PATH
$(printf "%s" "$API_GATEWAY_REVERSE_PROXY_KEY")
EOF

cat <<EOF > $API_GATEWAY_REVERSE_PROXY_CERT_PATH
$(printf "%s" "$API_GATEWAY_REVERSE_PROXY_CERT")
EOF

