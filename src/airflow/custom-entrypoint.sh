#!/bin/bash
args=$1

source utils.sh

set_dynamic_env_variables

# Appel du script Vault
info_msg "Appel du script Vault pour récupérer les certificats et les clés..."
vault.sh
if [ $? -ne 0 ]; then
    error_exit "Le script Vault a échoué."
fi
success_msg "Le script Vault s'est exécuté avec succès."

set -m

# Appeler le script d'initialisation
source init-airflow.sh $args

nginx-fcgiwrap.sh
nginx-conf.sh

jobs 

fg %1