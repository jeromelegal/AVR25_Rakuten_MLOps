#!/bin/bash
# set -euo pipefail

args=$1
echo "Airflow args: ${args}"
echo "POSTGRESQL_AIRFLOW_CONN = $POSTGRESQL_AIRFLOW_CONN"

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

echo $AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
shift
if [[ "$args" == "api-server" ]]; then
    # source init-api-server.sh
    exec /entrypoint airflow api-server &
elif [[ "$args" == "triggerer" ]]; then
    # source init-triggerer.sh
    exec /entrypoint airflow triggerer &
elif [[ "$args" == "dag-processor" ]]; then
    # source init-dag-processor.sh
    exec /entrypoint airflow dag-processor &
elif [[ "$args" == "worker" ]]; then
    echo "DUMB_INIT_SETSID=${DUMB_INIT_SETSID}"
    # source init-worker.sh
    exec /entrypoint airflow celery worker &
elif [[ "$args" == "scheduler" ]]; then
    # source init-scheduler.sh
    exec /entrypoint airflow scheduler &
else
    error_exit "Commande $args non gérée"
    exit 1
fi

