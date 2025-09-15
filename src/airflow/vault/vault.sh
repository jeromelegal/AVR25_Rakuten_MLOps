#!/bin/bash
set -e

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
vault kv get -field=certificate secret/airflow/ca > airflow_ca.crt
vault kv get -field=value secret/airflow/fernet_key > airflow_fernet_key.txt

mkdir -p $(dirname $AIRFLOW_PEM_PATH)  
mkdir -p $(dirname $AIRFLOW_CA_PATH)
mkdir -p $(dirname $AIRFLOW_KEY_PATH)
mkdir -p $(dirname $AIRFLOW_CERT_PATH)
mkdir -p $(dirname $AIRFLOW_FERNET_KEY_PATH)

cp airflow_ca.crt $AIRFLOW_CA_PATH

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp airflow_ca.crt /usr/local/share/ca-certificates/
cp airflow_fernet_key.txt /usr/local/share/ca-certificates/

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
