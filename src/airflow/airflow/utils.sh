# !/bin/bash

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

# Fonction pour afficher un message d'avertissement
warning_msg() {
    echo "⚠️ WARNING: $1"
}

waiting_airflow_server() {
    # Attendre que le serveur Airflow soit disponible
    info_msg "Attente de la disponibilité du serveur Airflow..."
    URL=https://${AIRFLOW_API_SERVER_SERVICE_NAME}:${AIRFLOW_API_SERVER_SERVICE_PORT}/api/v2/monitor/health
    until curl -s $URL | jq -e '.metadatabase.status == "healthy"' > /dev/null; do
        echo "Attente que le serveur Airflow soit healthy..."
        sleep 1  # Attendre 1 seconde avant de vérifier à nouveau
    done
    success_msg "Le serveur d'Airflow est healthy"
}

set_dynamic_env_variables() {
    # Postgresql
    export POSTGRESQL_AIRFLOW_PEM_PATH="/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.pem"
    export POSTGRESQL_AIRFLOW_KEY_PATH="/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.key"
    export POSTGRESQL_AIRFLOW_CERT_PATH="/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.crt"
    export POSTGRESQL_AIRFLOW_CA_PATH="/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}_ca.crt"

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
    export AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql:///?${qs}"

    # Redis
    export REDIS_AIRFLOW_KEY_PATH="/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.key"
    export REDIS_AIRFLOW_CERT_PATH="/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.crt"
    export REDIS_AIRFLOW_CA_PATH="/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}_ca.crt"
    export REDIS_AIRFLOW_PEM_PATH="/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.pem"
    qs_redis=$(python3 -c "import urllib.parse; \
    params = \"ssl_cert_reqs=required&ssl_ca_certs=${REDIS_AIRFLOW_CA_PATH}&ssl_certfile=${REDIS_AIRFLOW_CERT_PATH}&ssl_keyfile=${REDIS_AIRFLOW_KEY_PATH}&ssl=True\"; \
    print(urllib.parse.quote_plus(params))" \
    )
    export AIRFLOW__CELERY__BROKER_URL="redis://:${REDIS_PASSWORD}@${REDIS_SERVICE_NAME}:${REDIS_SERVICE_PORT}/0?${qs_redis}"
    export AIRFLOW__CELERY__SSL_ACTIVE="true"
    export AIRFLOW__CELERY__SSL_CACERT=$REDIS_AIRFLOW_CA_PATH
    export AIRFLOW__CELERY__SSL_CERT=$REDIS_AIRFLOW_CERT_PATH
    export AIRFLOW__CELERY__SSL_KEY=$REDIS_AIRFLOW_KEY_PATH

    export AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_PEM_PATH="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}.pem"
    export AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CA_PATH="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}_ca.crt"
    export AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_KEY_PATH="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}.key"
    export AIRFLOW_API_SERVER_AIRFLOW_COMPONENT_CERT_PATH="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}.crt"


    # Settings all dynamic environment variables
    export AIRFLOW__CORE__EXECUTION_API_SERVER_URL="https://${AIRFLOW_API_SERVER_SERVICE_NAME}:${AIRFLOW_API_SERVER_SERVICE_PORT}/execution/"
    export AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK="true"
    export AIRFLOW_CA_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_ca.crt"
    export AIRFLOW_KEY_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.key"
    export AIRFLOW_CERT_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.crt"
    export AIRFLOW_PEM_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.pem"
    export AIRFLOW_INTERNAL_SECRET_KEY_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_internal_secret.key"
    export AIRFLOW_AIRFLOW_PEM_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.pem"
    export AIRFLOW_AIRFLOW_KEY_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.key"
    export AIRFLOW_AIRFLOW_CERT_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.crt"
    export AIRFLOW_AIRFLOW_CA_PATH="/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}_ca.crt"
    export AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW_HOME}/dags"
    export _AIRFLOW_WWW_USER_USERNAME="${AIRFLOW_USER}"
    export _AIRFLOW_WWW_USER_PASSWORD="${AIRFLOW_PASSWORD}"
    export AIRFLOW__API__SSL_CERT="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}.crt"
    export AIRFLOW__API__SSL_KEY="/etc/ssl/${SERVICE_NAME}/${AIRFLOW_API_SERVER_SERVICE_NAME}_${SERVICE_NAME}.key"
    export AIRFLOW__API_AUTH__JWT_SECRET='ykJsrdqOKXTe14WM+zDScA=='    
    export AIRFLOW__API__SECRET_KEY='ykJsrdqOKXTe14WM+zDScA=='

}