#!/bin/bash


# Vérifier si le serveur a été initialisé
if [ "$INITIALIZED" = "true" ]; then
  echo "Le serveur Vault a été initialisé."
else
  echo "Le serveur Vault n'a pas été initialisé."
  source init.sh
fi

source vault.sh

if [ -n $UNSEAL_KEYS ]; then
  if [ -f "UNSEAL_KEYS.var" ]; then
    echo "Le fichier existe à l'emplacement : UNSEAL_KEYS.var"
    export UNSEAL_KEYS=$(cat "UNSEAL_KEYS.var")
  fi
else
  echo $UNSEAL_KEYS > UNSEAL_KEYS.var
fi

if [ "$CONSUL_BACKEND" = "true" ]; then

  echo "Configuration du backend avec Consul."
  source consul.sh
fi

ALL_ARGS=("$@" "-config=$VAULT_CONFIG_FILE")


jobs_output=$(jobs 2>&1)
# Vérifie si la sortie de jobs est vide
until [[ -z "$jobs_output" ]]; do
  jobs_output=$(jobs 2>&1)
  jobs
  sleep 1
done

set -m

vault server -config=$VAULT_CONFIG_FILE &

/usr/bin/python3 /usr/local/bin/auto-unseal.py > python.log 2>&1 &
export AUTO_UNSEAL_PID=$!

source nginx-conf.sh
source nginx-fcgiwrap.sh

fg %1


