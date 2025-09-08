#!/bin/bash
echo "init.sh"

SAVE_VAULT_ADDR=$VAULT_ADDR
export VAULT_ADDR="https://127.0.0.1:8200"


echo "Start Vault"
vault server -config=$VAULT_CONFIG_FILE &
SERVER_VAULT_PID=$!
echo "Vault server started with PID $SERVER_VAULT_PID"

echo "Start auto-unseal"
/usr/bin/python3 /usr/local/bin/auto-unseal.py > python.log 2>&1 &
export AUTO_UNSEAL_PID=$!
echo "Started auto-unseal AUTO_UNSEAL_PID: $AUTO_UNSEAL_PID"

# /usr/bin/python3 /usr/local/bin/auto-unseal.py > python.log 2>&1 &
# export AUTO_UNSEAL_PID=$!

# Générer les certificats TLS
echo "Génération des certificats TLS..."

VAULT_TEMP_CA_CERT_FILE="$VAULT_TLS_DIR/temp_ca.crt"

# Générer une autorité de certification (CA)
openssl genrsa -out $VAULT_CA_KEY_FILE 4096
openssl req -x509 -new -nodes -key $VAULT_CA_KEY_FILE -sha256 -days 3650 -out $VAULT_TEMP_CA_CERT_FILE -subj "/CN=$VAULT_CA_CN"

cp $VAULT_TEMP_CA_CERT_FILE /usr/local/share/ca-certificates/

update-ca-certificates

# Obtenir toutes les adresses IP attribuées au système
ips=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

# Générer la section [alt_names] pour la configuration de certificat
alt_names="[alt_names]"
index=1
for ip in $ips; do
    alt_names+=$'\n'"IP.$index = $ip"
    index=$((index + 1))
done
alt_names+=$'\n'"DNS.1 = $SERVICE_NAME"

# Générer un certificat pour le serveur Vault
cat <<EOF > vault_san.cnf
[req]
distinguished_name = req_distinguished_name
req_extensions = req_ext
prompt = no

[req_distinguished_name]
CN = $VAULT_CERT_CN

[req_ext]
subjectAltName = @alt_names

$alt_names
EOF

# Générer la clé privée et la demande de certificat
openssl genrsa -out $VAULT_KEY_FILE 4096  > /dev/null 2>&1
openssl req -new -key $VAULT_KEY_FILE -out $VAULT_REQ_FILE -config vault_san.cnf  > /dev/null 2>&1

# Signer le certificat avec les SAN
openssl x509 -req -in $VAULT_REQ_FILE -CA $VAULT_TEMP_CA_CERT_FILE -CAkey $VAULT_CA_KEY_FILE -CAcreateserial -out $VAULT_CERT_FILE -days 365 -sha256 -extfile vault_san.cnf -extensions req_ext  > /dev/null 2>&1


chown vault:vault "$VAULT_TEMP_CA_CERT_FILE" && chmod 400 "$VAULT_TEMP_CA_CERT_FILE" && ls -l "$VAULT_TEMP_CA_CERT_FILE"
chown vault:vault "$VAULT_CERT_FILE" && chmod 400 "$VAULT_CERT_FILE" && ls -l "$VAULT_CERT_FILE"
chown vault:vault "$VAULT_KEY_FILE" && chmod 400 "$VAULT_KEY_FILE" && ls -l "$VAULT_KEY_FILE"

#openssl x509 -in $VAULT_CERT_FILE -text -noout

VAULT_LOCAL_DATA=/vault/data
mkdir -p $VAULT_LOCAL_DATA


# Nom du fichier de verrouillage
LOCK_FILE="/tmp/vault_config.lock"

# Écrire la configuration dans le fichier
{

  cat <<EOF > $VAULT_CONFIG_FILE
ui = true

storage "file" {
  path = "$VAULT_LOCAL_DATA"
}

listener "tcp" {
  address       = "127.0.0.1:8200"
  tls_cert_file = "$VAULT_CERT_FILE"
  tls_key_file  = "$VAULT_KEY_FILE"
}

api_addr = "https://127.0.0.1:8200"
cluster_addr = "https://127.0.0.1:8201"
disable_mlock = true

# Configuration des logs
log_level = "info"
log_file = "/var/log/vault.log"
EOF

    # Créer le fichier de verrouillage pour indiquer que l'écriture est terminée
    touch "$LOCK_FILE"
} &

# Attendre que le fichier de verrouillage soit créé
until [ -f "$LOCK_FILE" ]; do
    echo "Attente de la libération de $LOCK_FILE"
    sleep 1
done

# Supprimer le fichier de verrouillage
rm "$LOCK_FILE"

#exec vault server -config=$VAULT_CONFIG_FILE &
vault server -config=$VAULT_CONFIG_FILE &
SERVER_VAULT_PID=$!
echo "Vault server started with PID $SERVER_VAULT_PID"

until curl -s $VAULT_ADDR/v1/sys/seal-status > /dev/null; do
  echo "Waiting for Vault to be ready..."
  sleep 1
done
echo "Vault is ready!"

# Initialiser Vault et obtenir la sortie au format JSON
INIT_OUTPUT=$(vault operator init -key-shares=1 -key-threshold=1 -format=json)

# Extraire la clé d'unsealing avec jq
export UNSEAL_KEYS=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[]')
echo $UNSEAL_KEYS > UNSEAL_KEYS.var

# Extraire le token root avec jq
ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

# Exporter le token root
export VAULT_TOKEN=$ROOT_TOKEN

# Unseal Vault
for KEY in $UNSEAL_KEYS; do
  vault operator unseal $KEY
done

# Activer le moteur KV
vault secrets enable -path=secret kv

# Créer une policy pour accéder au chemin root-token
vault policy write root_token - <<EOF
path "secret/root-token" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Attacher la policy au token root
vault token create -policy=$ROOT_TOKEN_POLICY  > /dev/null

# Stocker le token root dans Vault
vault kv put secret/root-token token=$ROOT_TOKEN 

# Activer le moteur d'authentification userpass
vault auth enable userpass

# Fonction pour configurer les moteurs PKI pour chaque service
configure_pki_engine() {
    local service=$1
    vault secrets enable -path=pki_${service} pki
    vault secrets tune -max-lease-ttl=8760h pki_${service}
    vault write -field=certificate pki_${service}/root/generate/internal common_name="${service}.root.local" issuer_name="root-${service}" ttl="8760h" > ${service}_root_cert.crt
}

# Fonction pour générer les certificats intermédiaires
generate_intermediate_cert() {
    local service=$1
    local issuer_name="int-${service}"
    local csr_file="${service}_intermediate.csr"
    local crt_file="${service}_intermediate_bundle.crt"

    vault write -format=json pki_${service}/intermediate/generate/internal common_name="${service}.intermediate.local" issuer_name="${issuer_name}" ttl="4380h" | jq -r '.data.csr' > ${csr_file}
    vault write -format=json pki_${service}/root/sign-intermediate csr=@${csr_file} format=pem_bundle ttl="4380h" | jq -r '.data.certificate' > ${crt_file}
    vault write pki_${service}/intermediate/set-signed certificate=@${crt_file}
}

# Fonction pour créer les politiques CA pour chaque service
create_ca_policy() {
    local service=$1
    shift
    local services=("$@")
    local policy_file="/tmp/${service}-ca-policy"

    # Initialiser le fichier de politique
    cat <<EOF > $policy_file
path "pki_${service}/issue/${service}" {
  capabilities = ["create", "update"]
}
path "secret/${service}/ca" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

    # Ajouter dynamiquement les permissions de lecture pour les CA des autres services
    for other_service in "${services[@]}"; do
        if [ "$other_service" != "$service" ]; then
            cat <<EOF >> $policy_file
path "secret/${other_service}/ca" {
  capabilities = ["read", "list"]
}
EOF
        fi
    done

    # Appliquer la politique
    vault policy write ${service}-ca $policy_file

    # Nettoyer le fichier temporaire
    rm -f $policy_file
}

# Fonction pour créer les politiques secrets pour chaque service
create_secrets_policy() {
    local service=$1
    shift
    local services=("$@")
    local policy_file="/tmp/${service}-secrets-policy"

    # Initialiser le fichier de politique
    cat <<EOF > $policy_file
path "secret/${service}/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/${service}/${service}/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

    # Ajouter dynamiquement les permissions de lecture pour les sous-chemins des autres services
    for other_service in "${services[@]}"; do
        if [ "$other_service" != "$service" ]; then
            cat <<EOF >> $policy_file
path "secret/${other_service}/${service}/*" {
  capabilities = ["read", "list"]
}
EOF
        fi
    done

    # Appliquer la politique
    vault policy write ${service}-secrets $policy_file

    # Nettoyer le fichier temporaire
    rm -f $policy_file
}

# Fonction pour configurer les URLs AIA pour chaque service
configure_aia_urls() {
    local service=$1
#    vault write pki_${service}/roles/${service} issuer_ref="$(vault read -field=default pki_${service}/config/issuers)" allowed_domains="${service}" allow_subdomains=true allow_bare_domains=true allow_ip_sans=true  allow_any_name=true max_ttl="72h"
    vault write pki_${service}/roles/${service} issuer_ref="$(vault read -field=default pki_${service}/config/issuers)" allowed_domains="${service}" allow_subdomains=true allow_bare_domains=true allow_ip_sans=true  allow_any_name=true cn_validations="disabled" max_ttl="72h"
    vault write pki_${service}/config/urls issuing_certificates="$VAULT_ADDR/v1/pki_${service}/ca" crl_distribution_points="$VAULT_ADDR/v1/pki_${service}/crl"

    echo "configure_pki_roles Display vault read"
    vault read pki_${service}/roles/${service}


    # Afficher les CN autorisés pour le rôle
    echo "Affichage des CN autorisés pour le rôle PKI : $service"
    role_config=$(vault read -format=json pki_${service}/roles/${service})

    # Extraire et afficher les domaines autorisés
    allowed_domains=$(echo "$role_config" | jq -r '.data.allowed_domains[]?')
    echo "Domaines autorisés : $allowed_domains"


    # Vérifier si allow_any_name est activé
    allow_any_name=$(echo "$role_config" | jq -r '.data.allow_any_name')
    if [ "$allow_any_name" = "true" ]; then
        echo "Le rôle permet n'importe quel nom (allow_any_name est activé)."
    else
        echo "Le rôle ne permet que les noms spécifiés dans allowed_domains."
    fi


}


# Fonction pour créer des utilisateurs et attribuer des politiques
create_users_and_assign_policies() {
    local service=$1
    local password=$2
    local ca_policy="${service}-ca"
    local secrets_policy="${service}-secrets"

    # Créer un utilisateur avec un mot de passe
    vault write auth/userpass/users/${service} password=${password} policies=${ca_policy},${secrets_policy}
}


configure_pki_roles() {
    local service=$1
    vault write pki_${service}/roles/${service} issuer_ref="$(vault read -field=default pki_${service}/config/issuers)" allowed_domains="${service}" allow_subdomains=true allow_bare_domains=true allow_ip_sans=true  allow_any_name=true max_ttl="72h"
}


# Fonction pour stocker les certificats intermédiaires dans des secrets
store_intermediate_certs() {
    local service=$1
    local cert_file="${service}_intermediate_bundle.crt"
    vault kv put "secret/${service}/ca" certificate=@${cert_file}
}

# Liste des services
services=("vault" "consul" "mongodb" "api-mongodb" "postgresql" "api-postgresql"  "api-gateway" "frontend" "reverse-proxy" "zookeeper" "kafka" "minio" "api-minio" "mlflow")

# Appel des fonctions pour chaque service
for service in "${services[@]}"; do
    configure_pki_engine $service
    generate_intermediate_cert $service
    create_ca_policy $service "${services[@]}"
    create_secrets_policy $service "${services[@]}"
    configure_aia_urls $service
    create_users_and_assign_policies $service $service
    store_intermediate_certs $service
done




echo "Stop Vault SERVER_VAULT_PID: $SERVER_VAULT_PID"
kill -SIGTERM $SERVER_VAULT_PID > /dev/null 2>&1
# Vérifier si le processus a été arrêté correctement
until ! ps -p $SERVER_VAULT_PID > /dev/null; do
  echo "Le processus Vault est en cours d'arrêt."
  sleep 1
done
echo "Le processus Vault a été arrêté avec succès."

echo "Stop Auto-Unseal AUTO_UNSEAL_PID: $AUTO_UNSEAL_PID"
kill -SIGTERM $AUTO_UNSEAL_PID > /dev/null 2>&1
# Vérifier si le processus a été arrêté correctement
until ! ps -p $AUTO_UNSEAL_PID > /dev/null; do
  echo "Le processus Auto-Unseal est en cours d'arrêt."
  sleep 1
done
echo "Le processus Auto-Unseal a été arrêté avec succès."

