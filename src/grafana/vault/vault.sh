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

mkdir -p $(dirname $GRAFANA_PEM_PATH) $(dirname $GRAFANA_CA_PATH) $(dirname $GRAFANA_GRAFANA_PEM_PATH) $(dirname $GRAFANA_GRAFANA_CA_PATH)

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null; do
    echo "Échec de l'authentification. Nouvelle tentative dans 1 seconde..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/grafana/ca > grafana_ca.crt
vault kv get -field=certificate secret/prometheus/ca > prometheus_ca.crt

mkdir -p $(dirname $GRAFANA_PEM_PATH)
mkdir -p $(dirname $GRAFANA_CA_PATH)
mkdir -p $(dirname $GRAFANA_KEY_PATH)
mkdir -p $(dirname $GRAFANA_CERT_PATH)

cp grafana_ca.crt $GRAFANA_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp grafana_ca.crt /usr/local/share/ca-certificates/
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

vault write -format=json pki_grafana/issue/grafana common_name="grafana" ip_sans="$ip_list" alt_names="$SERVICE_NAME" ttl="72h" > grafana_cert.json

cat <<EOF > $GRAFANA_PEM_PATH
$(jq -r '.data.private_key' grafana_cert.json)
$(jq -r '.data.certificate' grafana_cert.json)
$(jq -r '.data.issuing_ca' grafana_cert.json)
EOF

# Extraire le certificat et la clé privée
echo "GRAFANA_CERT_PATH = $GRAFANA_CERT_PATH"
cat <<EOF > $GRAFANA_CERT_PATH
$(jq -r '.data.certificate' grafana_cert.json)
EOF
echo "GRAFANA_KEY_PATH = $GRAFANA_KEY_PATH"
cat <<EOF > $GRAFANA_KEY_PATH
$(jq -r '.data.private_key' grafana_cert.json)
EOF

chown grafana:grafana $GRAFANA_KEY_PATH
chmod 600 $GRAFANA_KEY_PATH


# Définir les permissions pour les fichiers de certificat et de clé
chown grafana:grafana $GRAFANA_PEM_PATH
chmod 400 $GRAFANA_PEM_PATH

# Nettoyage des fichiers temporaires
rm -f grafana_cert.json

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/grafana/keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/grafana/keyfile value=$key_value
fi

GRAFANA_SECRET_KEY=$(vault kv get -field=value secret/grafana/keyfile)

# Vérifier si le certificat et la clé Backend existent déjà
if ! vault kv get -field=value secret/grafana/internal_keyfile > /dev/null 2>&1; then
  key_value=$(openssl rand -base64 741 | tr -d '\n' )
  vault kv put secret/grafana/internal_keyfile value=$key_value
fi

GRAFANA_INTERNAL_SECRET_KEY=$(vault kv get -field=value secret/grafana/internal_keyfile)


# Vérifier si le certificat et la clé Vault existent déjà pour Grafana
if vault kv get -field=cert secret/grafana/grafana/certs > /dev/null 2>&1 && vault kv get -field=key secret/grafana/grafana/certs > /dev/null 2>&1; then
  echo "Le certificat mTLS grafana pour le grafana existe déjà"
  GRAFANA_GRAFANA_CA=$(vault kv get -field=ca secret/grafana/grafana/certs)
  GRAFANA_GRAFANA_CERT=$(vault kv get -field=cert secret/grafana/grafana/certs)
  GRAFANA_GRAFANA_KEY=$(vault kv get -field=key secret/grafana/grafana/certs)
else
  # Générer le certificat et la clé
  echo "Générer le certificat et la clé"
  vault write -format=json pki_grafana/issue/grafana common_name="grafana"   ttl="72h" > grafana_grafana_cert.json

  # Extraire le certificat et la clé privée
  GRAFANA_GRAFANA_CA=$(jq -r '.data.ca_chain[0]' grafana_grafana_cert.json)
  GRAFANA_GRAFANA_CERT=$(jq -r '.data.certificate' grafana_grafana_cert.json)
  GRAFANA_GRAFANA_KEY=$(jq -r '.data.private_key' grafana_grafana_cert.json)


  # Enregistrer le certificat et la clé privée dans Vault
  vault kv put secret/grafana/grafana/certs cert="$GRAFANA_GRAFANA_CERT" key="$GRAFANA_GRAFANA_KEY" ca="$GRAFANA_GRAFANA_CA"

  # Nettoyage des fichiers temporaires
  rm -f grafana_grafana_cert.json
fi


cat <<EOF > $GRAFANA_GRAFANA_KEY_PATH
$(printf "%s" "$GRAFANA_GRAFANA_KEY")
EOF

cat <<EOF > $GRAFANA_GRAFANA_CERT_PATH
$(printf "%s" "$GRAFANA_GRAFANA_CERT")
EOF

cat <<EOF > $GRAFANA_GRAFANA_PEM_PATH
$(printf "%s" "$GRAFANA_GRAFANA_KEY")
$(printf "%s" "$GRAFANA_GRAFANA_CERT")
EOF

cat <<EOF > $GRAFANA_GRAFANA_CA_PATH
$(printf "%s" "$GRAFANA_GRAFANA_CA")
EOF

chown grafana:grafana $GRAFANA_GRAFANA_KEY_PATH
chmod 600 $GRAFANA_GRAFANA_KEY_PATH

# Extraire le certificat et la clé privée
PROMETHEUS_GRAFANA_CA=$(vault kv get -field=ca secret/prometheus/grafana/certs)
PROMETHEUS_GRAFANA_CERT=$(vault kv get -field=cert secret/prometheus/grafana/certs)
PROMETHEUS_GRAFANA_KEY=$(vault kv get -field=key secret/prometheus/grafana/certs)

cat <<EOF > $PROMETHEUS_GRAFANA_PEM_PATH
$(printf "%s" "$PROMETHEUS_GRAFANA_KEY")
$(printf "%s" "$PROMETHEUS_GRAFANA_CERT")
EOF

cat <<EOF > $PROMETHEUS_GRAFANA_CA_PATH
$(printf "%s" "$PROMETHEUS_GRAFANA_CA")
EOF

cat <<EOF > $PROMETHEUS_GRAFANA_KEY_PATH
$(printf "%s" "$PROMETHEUS_GRAFANA_KEY")
EOF

cat <<EOF > $PROMETHEUS_GRAFANA_CERT_PATH
$(printf "%s" "$PROMETHEUS_GRAFANA_CERT")
EOF