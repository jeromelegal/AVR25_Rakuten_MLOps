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

mkdir -p $(dirname $PROMETHEUS_PEM_PATH)  $(dirname $PROMETHEUS_CA_PATH) $(dirname $PROMETHEUS_PROMETHEUS_PEM_PATH) $(dirname $PROMETHEUS_PROMETHEUS_CA_PATH)

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/prometheus/ca > prometheus_ca.crt

cp prometheus_ca.crt $PROMETHEUS_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp prometheus_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_prometheus/issue/prometheus common_name="prometheus" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > prometheus_cert.json

cat <<EOF > $PROMETHEUS_PEM_PATH
$(jq -r '.data.private_key' prometheus_cert.json)
$(jq -r '.data.certificate' prometheus_cert.json)
$(jq -r '.data.issuing_ca' prometheus_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "PROMETHEUS_CERT_PATH = $PROMETHEUS_CERT_PATH"
cat <<EOF > $PROMETHEUS_CERT_PATH
$(jq -r '.data.certificate' prometheus_cert.json)
EOF
echo "PROMETHEUS_KEY_PATH = $PROMETHEUS_KEY_PATH"
cat <<EOF > $PROMETHEUS_KEY_PATH
$(jq -r '.data.private_key' prometheus_cert.json)
EOF

# Définir les permissions pour les fichiers de certificat et de clé
chown prometheus:prometheus $PROMETHEUS_PEM_PATH
chmod 400 $PROMETHEUS_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f prometheus_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if vault kv get -field=cert secret/prometheus/prometheus/certs > /dev/null 2>&1 && vault kv get -field=key secret/prometheus/prometheus/certs > /dev/null 2>&1; then
  echo "Le certificat et la clé Backend existent déjà"
  PROMETHEUS_PROMETHEUS_CA=$(vault kv get -field=ca secret/prometheus/prometheus/certs)
  PROMETHEUS_PROMETHEUS_CERT=$(vault kv get -field=cert secret/prometheus/prometheus/certs)
  PROMETHEUS_PROMETHEUS_KEY=$(vault kv get -field=key secret/prometheus/prometheus/certs)  
else
  # Générer le certificat et la clé pour Backend
  echo "Générer le certificat et la clé pour Backend"
  vault write -format=json pki_prometheus/issue/prometheus common_name="prometheus"   ttl="72h" > prometheus_prometheus_cert.json

  # Extraire le certificat et la clé privée
  PROMETHEUS_PROMETHEUS_CA=$(jq -r '.data.ca_chain' prometheus_prometheus_cert.json)
  PROMETHEUS_PROMETHEUS_CERT=$(jq -r '.data.certificate' prometheus_prometheus_cert.json)
  PROMETHEUS_PROMETHEUS_KEY=$(jq -r '.data.private_key' prometheus_prometheus_cert.json)
  
  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/prometheus/prometheus/certs cert="$PROMETHEUS_PROMETHEUS_CERT" key="$PROMETHEUS_PROMETHEUS_KEY" ca="$PROMETHEUS_PROMETHEUS_CA"
  # Nettoyage des fichiers temporaires
  rm -f prometheus_prometheus_cert.json
fi

cat <<EOF > $PROMETHEUS_PROMETHEUS_PEM_PATH
$(printf "%s" "$PROMETHEUS_PROMETHEUS_KEY")
$(printf "%s" "$PROMETHEUS_PROMETHEUS_CERT")
EOF

printf "%s" $PROMETHEUS_PROMETHEUS_CA > $PROMETHEUS_PROMETHEUS_CA_PATH

key_value=$(openssl rand -base64 741 | tr -d '\n' )

vault kv put secret/prometheus/keyfile value=$key_value

retrieve=$(vault kv get -field=value secret/prometheus/keyfile)

mkdir -p /etc/ssl/prometheus/
echo $retrieve > /etc/ssl/prometheus/prometheus-keyfile
chmod 600 /etc/ssl/prometheus/prometheus-keyfile

