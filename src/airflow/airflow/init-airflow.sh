#!/bin/bash
# set -euo pipefail

# Fonction pour afficher un message d'erreur et quitter
error_exit() {
    echo "❌ ERREUR: $1" >&2
    # exit 1
}

# Fonction pour afficher un message d'information
info_msg() {
    echo "ℹ️ INFO: $1"
}

# Fonction pour afficher un message de succès
success_msg() {
    echo "✅ SUCCÈS: $1"
}

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

# Appel du script Vault
info_msg "Appel du script Vault pour récupérer les certificats et les clés..."
vault.sh
if [ $? -ne 0 ]; then
    error_exit "Le script Vault a échoué."
fi
success_msg "Le script Vault s'est exécuté avec succès."

# Configuration de la clé API Airflow
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

# Generate backend URI using DSN
qs=$(python3 -c "import urllib.parse; \
params = { \
    \"host\": \"${POSTGRESQL_SERVICE_NAME}\", \
    \"port\": \"${POSTGRESQL_SERVICE_PORT}\", \
    \"user\": \"${POSTGRESQL_AIRFLOW_USER}\", \
    \"password\": \"${POSTGRESQL_AIRFLOW_PASSWORD}\", \
    \"dbname\": \"${POSTGRESQL_AIRFLOW_DATABASE}\", \
    \"sslmode\": \"verify-full\", \
    \"sslcert\": \"${POSTGRESQL_AIRFLOW_CERT_PATH}\", \
    \"sslkey\": \"${POSTGRESQL_AIRFLOW_KEY_PATH}\", \
    \"sslrootcert\": \"${POSTGRESQL_AIRFLOW_CA_PATH}\", \
}; \
print(urllib.parse.urlencode(params))" \
)
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2:///?${qs}"
echo "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}"

# Migration de la base de données Airflow
info_msg "Migration de la base de données Airflow..."
airflow db migrate
if [ $? -ne 0 ]; then
    error_exit "Échec de la migration de la base de données Airflow."
fi
success_msg "Migration de la base de données Airflow réussie."

info_msg "Création du user admin..."
if ! airflow users list | grep -q "^${AIRFLOW_USER}\b"; then
    airflow users create \
      --username "${AIRFLOW_USER}" \
      --firstname Admin \
      --lastname Admin \
      --password ${AIRFLOW_PASSWORD} \
      --role Admin \
      --email admin@example.org
else
    echo "User '${AIRFLOW_USER}' already exists, skipping creation."
fi
success_msg "Création de l'utilisateur réussie."

info_msg "Création de l'API server..."
airflow api-server \
    --host $SERVICE_NAME \
    --ssl-cert $AIRFLOW_AIRFLOW_CERT_PATH \
    --ssl-key $AIRFLOW_AIRFLOW_KEY_PATH \
    --port $SERVICE_PORT &


# Attendre que le serveur Airflow soit disponible
info_msg "Attente de la disponibilité du serveur Airflow..."
URL=https://${SERVICE_NAME}:${SERVICE_PORT}/api/v2/monitor/health
until curl -s $URL | jq -e '.metadatabase.status == "healthy"' > /dev/null; do
    echo "Attente que le serveur Airflow soit healthy..."
    sleep 1  # Attendre 1 seconde avant de vérifier à nouveau
done
success_msg "Le serveur d'Airflow est healthy"

info_msg "Création du scheduler..."
airflow scheduler &

until curl -s $URL | jq -e '.metadatabase.status == "healthy" and .scheduler.status == "healthy"' > /dev/null; do
    echo "Attente que le scheduler d'Airflow soit healthy..."
    sleep 1  # Attendre 1 seconde avant de vérifier à nouveau
done
success_msg "Le scheduler d'Airflow est healthy"
  
info_msg "Création du DAG processor..."
airflow dag-processor &

until curl -s $URL | jq -e '.metadatabase.status == "healthy" and .scheduler.status == "healthy" and .dag_processor.status == "healthy"' > /dev/null; do
    echo "Attente que le DAG creator d'Airflow soit healthy..."
    sleep 1  # Attendre 1 seconde avant de vérifier à nouveau
done
success_msg "Le DAG creator d'Airflow est healthy"

info_msg "Création du triggerer..."
airflow triggerer &

until curl -s $URL | jq -e '.metadatabase.status == "healthy" and .scheduler.status == "healthy" and .dag_processor.status == "healthy" and .triggerer.status == "healthy"' > /dev/null; do
    echo "Attente que le triggerer d'Airflow soit healthy..."
    sleep 1  # Attendre 1 seconde avant de vérifier à nouveau
done
success_msg "Le triggerer d'Airflow est healthy"

