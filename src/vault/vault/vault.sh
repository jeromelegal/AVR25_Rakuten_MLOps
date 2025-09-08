#!/bin/bash

echo "vault.sh"


# Mettre à jour la configuration du service Vault avec les nouveaux certificats
# export VAULT_ADDR=$SAVE_VAULT_ADDR

echo $VAULT_CONFIG_FILE
cat $VAULT_CONFIG_FILE

# Ajout d'une règle pour mettre le trafic en pause si il vient de l'extérieur. Le trafic sera débloqué une fois le vault déverrouillé
iptables -I INPUT -p tcp --dport 8200 ! -s 127.0.0.1 -j NFQUEUE --queue-num 1
# iptables -I INPUT -p tcp --dport 8200 -j NFQUEUE --queue-num 1

echo "Start Vault"
vault server -config=$VAULT_CONFIG_FILE &
SERVER_VAULT_PID=$!
echo "Vault server started with PID $SERVER_VAULT_PID"

echo "Start auto-unseal"
su - root -c "/usr/bin/python3 /usr/local/bin/auto-unseal.py > python.log 2>&1" &
export AUTO_UNSEAL_PID=$!
echo "Started auto-unseal AUTO_UNSEAL_PID: $AUTO_UNSEAL_PID"


# # Obtenir la variable d'environnement
# UNSEAL_KEYS=${UNSEAL_KEYS:-}

# # Vérifier si UNSEAL_KEYS n'est pas vide
# echo "Tentative déverrouillage"
# if [ -n "$UNSEAL_KEYS" ]; then
#     # Définir IFS pour diviser la chaîne en mots (clés)
#     IFS=' ' read -ra KEYS <<< "$UNSEAL_KEYS"
#     echo "Clés : $UNSEAL_KEYS"
#     # Boucler sur chaque clé
#     for key in "${KEYS[@]}"; do
#         echo "déverrouillage avec la clé  : $key"
#         address="https://127.0.0.1:8200"
#         vault operator unseal -address="$address" "$key"
#     done
# fi


# Fonction pour essayer de déverrouiller le Vault
attempt_unseal() {
    local keys=("$@") # Récupérer toutes les clés passées à la fonction
    local address="https://127.0.0.1:8200"
    for key in "${keys[@]}"; do
        echo "Déverrouillage avec la clé : $key"
        vault operator unseal -address="$address" "$key"
    done
}

# Vérifier si UNSEAL_KEYS n'est pas vide
UNSEAL_KEYS=${UNSEAL_KEYS:-}

if [ -n "$UNSEAL_KEYS" ]; then
    # Définir IFS pour diviser la chaîne en mots (clés)
    IFS=' ' read -ra KEYS <<< "$UNSEAL_KEYS"
    echo "Clés : $UNSEAL_KEYS"

    # Boucle pour tenter de déverrouiller le Vault
    while true; do
        echo "Tentative de déverrouillage..."

        # Appeler la fonction de déverrouillage
        attempt_unseal "${KEYS[@]}"

        # Vérifier le statut du Vault
        VAULT_STATUS=$(vault status -address="https://127.0.0.1:8200" 2>&1)
        if echo "$VAULT_STATUS" | grep -q "Sealed.*false"; then
            echo "Le Vault a été déverrouillé avec succès."
            break
        else
            echo "Le Vault n'a pas été déverrouillé. Nouvelle tentative dans 1 secondes..."
            sleep 1
        fi
    done
else
    echo "Aucune clé de déverrouillage fournie."
fi

until vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null ; do
    echo "VAULT_ADDR $VAULT_ADDR"
    echo "VAULT_USERNAME $VAULT_USERNAME"
    echo "VAULT_PASSWORD $VAULT_PASSWORD"
    echo "Échec de l'authentification. Nouvelle tentative dans 1 secondes..."
    sleep 1
done

# Récupérer les CA à ajouter aux magasins
vault kv get -field=certificate secret/vault/ca > vault_ca.crt
vault kv get -field=certificate secret/consul/ca > consul_ca.crt
vault kv get -field=certificate secret/mongodb/ca > mongodb_ca.crt

# Ajouter les CA aux magasins de certificats
cp vault_ca.crt /usr/local/share/ca-certificates/
cp consul_ca.crt /usr/local/share/ca-certificates/
cp mongodb_ca.crt /usr/local/share/ca-certificates/

update-ca-certificates


# Obtenir toutes les adresses IP attribuées au système
ips=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

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

vault write -format=json pki_vault/issue/vault common_name="vault" ip_sans="$ip_list" ttl="72h" > vault_service_cert.json

# Extraire le certificat et la clé privée
VAULT_SERVICE_CERT=$(jq -r '.data.certificate' vault_service_cert.json)
VAULT_SERVICE_KEY=$(jq -r '.data.private_key' vault_service_cert.json)

echo "$VAULT_SERVICE_CERT" > $VAULT_CERT_FILE
echo "$VAULT_SERVICE_KEY" > $VAULT_KEY_FILE

# Définir les permissions pour les fichiers de certificat et de clé
chown vault:vault $VAULT_CERT_FILE $VAULT_KEY_FILE
chmod 400 $VAULT_CERT_FILE $VAULT_KEY_FILE

# Nettoyage des fichiers temporaires
rm -f vault_ca.crt consul_ca.crt mongodb_ca.crt vault_service_cert.json


# # Mettre à jour la configuration du service Vault avec les nouveaux certificats
export VAULT_ADDR=$SAVE_VAULT_ADDR


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
  address       = "$SERVICE_NAME:8200"
  tls_cert_file = "$VAULT_CERT_FILE"
  tls_key_file  = "$VAULT_KEY_FILE"
}

listener "tcp" {
  address       = "127.0.0.1:8200"
  tls_cert_file = "$VAULT_CERT_FILE"
  tls_key_file  = "$VAULT_KEY_FILE"
}

api_addr = "https://vault:8200"
cluster_addr = "https://vault:8201"
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

