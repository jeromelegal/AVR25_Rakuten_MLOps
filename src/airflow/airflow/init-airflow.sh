#!/bin/bash
# set -euo pipefail

args=$1
echo "Airflow args: ${args}"

source utils.sh
set_dynamic_env_variables

# Début du script
echo "🚀 Démarrage du script d'entrée Airflow..."

# Vérification des variables d'environnement requises
info_msg "Vérification des variables d'environnement requises..."
if [ -z "${POSTGRESQL_SERVICE_NAME}" ]; then
    error_exit "La variable POSTGRESQL_SERVICE_NAME doit être définie."
fi
info_msg "POSTGRESQL_SERVICE_NAME est défini à: ${POSTGRESQL_SERVICE_NAME}"
if [ -z "${AIRFLOW_INTERNAL_SECRET_KEY_PATH}" ]; then
    error_exit "La variable AIRFLOW_INTERNAL_SECRET_KEY_PATH doit être définie."
fi
info_msg "AIRFLOW_INTERNAL_SECRET_KEY_PATH est défini à: ${AIRFLOW_INTERNAL_SECRET_KEY_PATH}"

# Attente de la disponibilité de PostgreSQL
info_msg "Attente de la disponibilité de PostgreSQL..."

HTTP_CODE=0
until [ $HTTP_CODE -eq 200 ] ; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" "https://${POSTGRESQL_SERVICE_NAME}/health")
    info_msg "En attente que le service PostgreSQL soit disponible (code HTTP: $HTTP_CODE)..."
    sleep 1
done
success_msg "Le service PostgreSQL est disponible."

# Attente de la disponibilité de Redis
info_msg "Attente de la disponibilité de Redis..."

HTTP_CODE=0
until [ $HTTP_CODE -eq 200 ] ; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" "https://${REDIS_SERVICE_NAME}/health")
    info_msg "En attente que le service Redis soit disponible (code HTTP: $HTTP_CODE)..."
    sleep 1
done
success_msg "Le service Redis est disponible."

# Configuration de la clé API Airflow
# TODO: share the key using Vault
info_msg "Configuration de la clé API Airflow..."
if [ -n "${AIRFLOW__API__SECRET_KEY:-}" ]; then
    info_msg "Utilisation de la clé API Airflow à partir de la variable d'environnement."
else
    if [ -f "$AIRFLOW_INTERNAL_SECRET_KEY_PATH" ]; then
        info_msg "Utilisation de la clé Vault pour récupérer la clé API Airflow."
        export AIRFLOW__API__SECRET_KEY=$(cat "$AIRFLOW_INTERNAL_SECRET_KEY_PATH")
        if [ -z "$AIRFLOW__API__SECRET_KEY" ]; then
            error_exit "La clé API Airflow récupérée à partir de $AIRFLOW_INTERNAL_SECRET_KEY_PATH est vide."
        fi
        info_msg "Clé API Airflow configurée avec succès."
    else
        error_exit "Aucune clé API Airflow disponible."
    fi
fi

if [[ "$args" == "api-server" ]]; then
    info_msg "Check if we should create an Airflow user..."
    res=$(airflow users list | grep "${AIRFLOW_USER}")

    info_msg "Requesting to create user."
    export _AIRFLOW_WWW_USER_CREATE='true'
    export _AIRFLOW_WWW_USER_USERNAME=${AIRFLOW_USER}
    export _AIRFLOW_WWW_USER_PASSWORD=${AIRFLOW_PASSWORD}

    info_msg "Requesting to migrate database."
    export _AIRFLOW_DB_MIGRATE='true'
    
    # source init-api-server.sh
    su airflow -c "exec /entrypoint airflow api-server " &
elif [[ "$args" == "triggerer" ]]; then
    # source init-triggerer.sh
    su airflow -c "exec /entrypoint airflow triggerer" &
elif [[ "$args" == "dag-processor" ]]; then
    # source init-dag-processor.sh
    su airflow -c "exec /entrypoint airflow dag-processor" &
elif [[ "$args" == "worker" ]]; then
    echo "DUMB_INIT_SETSID=${DUMB_INIT_SETSID}"
    # source init-worker.sh
    su airflow -c "exec /entrypoint airflow celery worker" &
elif [[ "$args" == "scheduler" ]]; then
    # source init-scheduler.sh
    su airflow -c "exec /entrypoint airflow scheduler" &
else
    error_exit "Commande $args non gérée"
    exit 1
fi

