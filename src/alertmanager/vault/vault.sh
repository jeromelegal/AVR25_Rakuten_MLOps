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

mkdir -p $(dirname $ALERTMANAGER_PEM_PATH) $(dirname $ALERTMANAGER_CA_PATH)

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 seconde..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/alertmanager/ca > alertmanager_ca.crt
vault kv get -field=certificate secret/alertmanager/ca > alertmanager_ca.crt

mkdir -p $(dirname $ALERTMANAGER_PEM_PATH)
mkdir -p $(dirname $ALERTMANAGER_CA_PATH)
mkdir -p $(dirname $ALERTMANAGER_KEY_PATH)
mkdir -p $(dirname $ALERTMANAGER_CERT_PATH)

cp alertmanager_ca.crt $ALERTMANAGER_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp alertmanager_ca.crt /usr/local/share/ca-certificates/
cp minio_ca.crt /usr/local/share/ca-certificates/

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

vault write -format=json pki_alertmanager/issue/alertmanager common_name="alertmanager" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > alertmanager_cert.json

cat <<EOF > $ALERTMANAGER_PEM_PATH
$(jq -r '.data.private_key' alertmanager_cert.json)
$(jq -r '.data.certificate' alertmanager_cert.json)
$(jq -r '.data.issuing_ca' alertmanager_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "ALERTMANAGER_CERT_PATH = $ALERTMANAGER_CERT_PATH"
cat <<EOF > $ALERTMANAGER_CERT_PATH
$(jq -r '.data.certificate' alertmanager_cert.json)
EOF
echo "ALERTMANAGER_KEY_PATH = $ALERTMANAGER_KEY_PATH"
cat <<EOF > $ALERTMANAGER_KEY_PATH
$(jq -r '.data.private_key' alertmanager_cert.json)
EOF

chown alertmanager:alertmanager $ALERTMANAGER_KEY_PATH
chmod 600 $ALERTMANAGER_KEY_PATH


# Définir les permissions pour les fichiers de certificat et de clé
chown alertmanager:alertmanager $ALERTMANAGER_PEM_PATH
chmod 400 $ALERTMANAGER_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f alertmanager_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/alertmanager/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/alertmanager/keyfile value=$key_value
fi

ALERTMANAGER_SECRET_KEY=$(vault kv get -field=value secret/alertmanager/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/alertmanager/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/alertmanager/internal_keyfile value=$key_value
fi

ALERTMANAGER_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/alertmanager/internal_keyfile)


# Vérifier si le certificat et la clé Vault existent déjà pour Alertmanager
if vault kv get -field=cert secret/alertmanager/alertmanager/certs > /dev/null 2>&1 && vault kv get -field=key secret/alertmanager/alertmanager/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS alertmanager pour le alertmanager existe déjà"
  ALERTMANAGER_ALERTMANAGER_CA=$(vault kv get -field=ca secret/alertmanager/alertmanager/certs)
  ALERTMANAGER_ALERTMANAGER_CERT=$(vault kv get -field=cert secret/alertmanager/alertmanager/certs)
  ALERTMANAGER_ALERTMANAGER_KEY=$(vault kv get -field=key secret/alertmanager/alertmanager/certs)
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_alertmanager/issue/alertmanager common_name="alertmanager"   ttl="72h" > alertmanager_alertmanager_cert.json

  # Extraire le certificat et la clé privée
  ALERTMANAGER_ALERTMANAGER_CA=$(jq -r '.data.ca_chain[0]' alertmanager_alertmanager_cert.json)
  ALERTMANAGER_ALERTMANAGER_CERT=$(jq -r '.data.certificate' alertmanager_alertmanager_cert.json)
  ALERTMANAGER_ALERTMANAGER_KEY=$(jq -r '.data.private_key' alertmanager_alertmanager_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/alertmanager/alertmanager/certs cert="$ALERTMANAGER_ALERTMANAGER_CERT" key="$ALERTMANAGER_ALERTMANAGER_KEY" ca="$ALERTMANAGER_ALERTMANAGER_CA"

  # Nettoyage des fichiers temporaires
  rm -f alertmanager_alertmanager_cert.json
fi


cat <<EOF > $ALERTMANAGER_ALERTMANAGER_KEY_PATH
$(printf "%s" "$ALERTMANAGER_ALERTMANAGER_KEY")
EOF

cat <<EOF > $ALERTMANAGER_ALERTMANAGER_CERT_PATH
$(printf "%s" "$ALERTMANAGER_ALERTMANAGER_CERT")
EOF

cat <<EOF > $ALERTMANAGER_ALERTMANAGER_PEM_PATH
$(printf "%s" "$ALERTMANAGER_ALERTMANAGER_KEY")
$(printf "%s" "$ALERTMANAGER_ALERTMANAGER_CERT")
EOF

cat <<EOF > $ALERTMANAGER_ALERTMANAGER_CA_PATH
$(printf "%s" "$ALERTMANAGER_ALERTMANAGER_CA")
EOF

chown alertmanager:alertmanager $ALERTMANAGER_ALERTMANAGER_KEY_PATH
chmod 600 $ALERTMANAGER_ALERTMANAGER_KEY_PATH

# Vérifier si le certificat et la clé Vault existent déjà pour Prometheus
if vault kv get -field=cert secret/alertmanager/prometheus/certs > /dev/null 2>&1 && vault kv get -field=key secret/alertmanager/prometheus/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS alertmanager pour le service prometheus existe déjà"
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_alertmanager/issue/alertmanager common_name="alertmanager"   ttl="72h" > alertmanager_prometheus_cert.json

  # Extraire le certificat et la clé privée
  ALERTMANAGER_PROMETHEUS_CA=$(jq -r '.data.ca_chain[0]' alertmanager_prometheus_cert.json)
  ALERTMANAGER_PROMETHEUS_CERT=$(jq -r '.data.certificate' alertmanager_prometheus_cert.json)
  ALERTMANAGER_PROMETHEUS_KEY=$(jq -r '.data.private_key' alertmanager_prometheus_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/alertmanager/prometheus/certs cert="$ALERTMANAGER_PROMETHEUS_CERT" key="$ALERTMANAGER_PROMETHEUS_KEY" ca="$ALERTMANAGER_PROMETHEUS_CA"

  # Nettoyage des fichiers temporaires
  rm -f alertmanager_prometheus_cert.json
fi

# Store credentials for Prometheus to use them
# TODO: Instead of root credentials, we should create specific credentials
vault kv put secret/alertmanager/prometheus/credentials user="$ALERTMANAGER_ROOT_USER" password="$ALERTMANAGER_ROOT_PASSWORD"