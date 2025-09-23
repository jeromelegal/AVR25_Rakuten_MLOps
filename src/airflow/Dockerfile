FROM ubuntu:noble-20250127
WORKDIR /app
# Création de l’utilisateur airflow
RUN groupadd --gid 999 airflow && \
    useradd --uid 999 --gid airflow --home-dir /home/airflow airflow && \
    mkdir -p /home/airflow && \
    chown -R airflow:airflow /home/airflow

# Variables d’environnement Airflow
ENV TZ=UTC
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"airflow"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"airflow"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}

ENV SERVICE_NAME=${SERVICE_NAME:-"airflow"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8790"}
ENV AIRFLOW_API_SERVER_SERVICE_NAME=${AIRFLOW_API_SERVER_SERVICE_NAME:-"airflow-apiserver"}
ENV AIRFLOW_API_SERVER_SERVICE_PORT=${AIRFLOW_API_SERVER_SERVICE_PORT:-"8790"}
ENV AIRFLOW_USER=${AIRFLOW_USER:-"airflow-user"}
ENV AIRFLOW_PASSWORD=${AIRFLOW_PASSWORD:-"airflow-password"}
ENV AIRFLOW_HOME=${AIRFLOW_HOME:-"/opt/airflow"}
ENV AIRFLOW__CORE__EXECUTOR=${AIRFLOW__CORE__EXECUTOR:-"LocalExecutor"}
ENV AIRFLOW__CORE__LOAD_EXAMPLES=${AIRFLOW__CORE__LOAD_EXAMPLES:-"false"}
ENV AIRFLOW__CORE__AUTH_MANAGER=${AIRFLOW__CORE__AUTH_MANAGER:-"airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"}
ENV AIRFLOW__API__PORT=${SERVICE_PORT}
ENV AIRFLOW__API__EXPOSE_CONFIG=${AIRFLOW__API__EXPOSE_CONFIG:-"false"}
ENV AIRFLOW__API__EXPOSE_STACKTRACE=${AIRFLOW__API__EXPOSE_STACKTRACE:-"false"}
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=${AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION:-"true"}
ENV AIRFLOW__CORE__EXECUTION_API_SERVER_URL=${AIRFLOW__CORE__EXECUTION_API_SERVER_URL:-"https://${AIRFLOW_API_SERVER_SERVICE_NAME}:${AIRFLOW_API_SERVER_SERVICE_PORT}/execution/"}
ENV AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=${AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK:-"true"}
ENV AIRFLOW_CA_PATH=${AIRFLOW_CA_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.ca"}
ENV AIRFLOW_KEY_PATH=${AIRFLOW_KEY_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.key"}
ENV AIRFLOW_CERT_PATH=${AIRFLOW_CERT_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_ca.crt"}
ENV AIRFLOW_PEM_PATH=${AIRFLOW_PEM_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}.pem"}
ENV AIRFLOW_INTERNAL_SECRET_KEY_PATH=${AIRFLOW_INTERNAL_SECRET_KEY_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_internal_secret.key"}
ENV AIRFLOW_AIRFLOW_PEM_PATH=${AIRFLOW_AIRFLOW_PEM_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.pem"}
ENV AIRFLOW_AIRFLOW_KEY_PATH=${AIRFLOW_AIRFLOW_KEY_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.key"}
ENV AIRFLOW_AIRFLOW_CERT_PATH=${AIRFLOW_AIRFLOW_CERT_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}.crt"}
ENV AIRFLOW_AIRFLOW_CA_PATH=${AIRFLOW_AIRFLOW_CA_PATH:-"/etc/ssl/${SERVICE_NAME}/${SERVICE_NAME}_${SERVICE_NAME}_ca.crt"}
ENV AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW_HOME}/dags"
ENV AIRFLOW__CORE__EXECUTION_API_SERVER_URL="https://${SERVICE_NAME}:${SERVICE_PORT}"
ENV AIRFLOW__CORE__FERNET_KEY=${AIRFLOW__CORE__FERNET_KEY:-"vYgDn-AesJP0QqFphmuOyuX4Qmw0CYeyWjULGiROzmE="}
ENV AIRFLOW__API__SSL_CERT=${AIRFLOW_CERT_PATH}
ENV AIRFLOW__API__SSL_KEY=${AIRFLOW_KEY_PATH}

ENV POSTGRESQL_SERVICE_NAME=${POSTGRESQL_SERVICE_NAME:-"postgresql"}
ENV POSTGRESQL_SERVICE_PORT=${POSTGRESQL_SERVICE_PORT:-"5432"}
ENV POSTGRESQL_AIRFLOW_USER=${POSTGRESQL_AIRFLOW_USER:-"airflow_user"}
ENV POSTGRESQL_AIRFLOW_PASSWORD=${POSTGRESQL_AIRFLOW_PASSWORD:-"airflow_user_password"}
ENV POSTGRESQL_AIRFLOW_DATABASE=${POSTGRESQL_AIRFLOW_DATABASE:-"airflow"}
ENV POSTGRESQL_AIRFLOW_PEM_PATH=${POSTGRESQL_AIRFLOW_PEM_PATH:-"/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.pem"}
ENV POSTGRESQL_AIRFLOW_KEY_PATH=${POSTGRESQL_AIRFLOW_KEY_PATH:-"/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.key"}
ENV POSTGRESQL_AIRFLOW_CERT_PATH=${POSTGRESQL_AIRFLOW_CERT_PATH:-"/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}.crt"}
ENV POSTGRESQL_AIRFLOW_CA_PATH=${POSTGRESQL_AIRFLOW_CA_PATH:-"/etc/ssl/${SERVICE_NAME}/postgresql_${SERVICE_NAME}_ca.crt"}
ENV POSTGRESQL_AIRFLOW_CONN=${POSTGRESQL_AIRFLOW_CONN:-"${POSTGRESQL_AIRFLOW_USER}:${POSTGRESQL_AIRFLOW_PASSWORD}@${POSTGRESQL_SERVICE_NAME}:${POSTGRESQL_SERVICE_PORT}/${POSTGRESQL_AIRFLOW_DATABASE}?sslmode=verify-full&sslcert=${POSTGRESQL_AIRFLOW_CERT_PATH}&sslkey=${POSTGRESQL_AIRFLOW_KEY_PATH}&sslrootcert=${POSTGRESQL_AIRFLOW_CA_PATH}"}
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN:-"postgresql+psycopg2://${POSTGRES_AIRFLOW_CONN}"}
ENV AIRFLOW__CELERY__RESULT_BACKEND=${AIRFLOW__CELERY__RESULT_BACKEND:-"db+postgresql://${POSTGRES_AIRFLOW_CONN}"}

ENV REDIS_SERVICE_NAME=${REDIS_SERVICE_NAME:-"redis"}
ENV REDIS_SERVICE_PORT=${REDIS_SERVICE_PORT:-"6379"}
ENV REDIS_AIRFLOW_USER=${REDIS_AIRFLOW_USER:-"airflow_user"}
ENV REDIS_AIRFLOW_PASSWORD=${REDIS_AIRFLOW_PASSWORD:-"airflow_user_password"}
ENV REDIS_AIRFLOW_DATABASE=${REDIS_AIRFLOW_DATABASE:-"airflow"}
ENV REDIS_AIRFLOW_PEM_PATH=${REDIS_AIRFLOW_PEM_PATH:-"/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.pem"}
ENV REDIS_AIRFLOW_KEY_PATH=${REDIS_AIRFLOW_KEY_PATH:-"/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.key"}
ENV REDIS_AIRFLOW_CERT_PATH=${REDIS_AIRFLOW_CERT_PATH:-"/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}.crt"}
ENV REDIS_AIRFLOW_CA_PATH=${REDIS_AIRFLOW_CA_PATH:-"/etc/ssl/${SERVICE_NAME}/redis_${SERVICE_NAME}_ca.crt"}
ENV AIRFLOW__CELERY__BROKER_URL=${AIRFLOW__CELERY__BROKER_URL:-"redis://:${REDIS_PASSWORD}@${REDIS_SERVICE_NAME}:${REDIS_SERVICE_PORT}/0?ssl_cert_reqs=required&ssl_ca_certs=${REDIS_AIRFLOW_CA_PATH}&ssl_certfile=${REDIS_AIRFLOW_CERT_PATH}&ssl_keyfile=${REDIS_AIRFLOW_KEY_PATH}&ssl=True"}

ENV MINIO_AIRFLOW_PEM_PATH=${MINIO_AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/minio_airflow.pem"}
ENV MINIO_AIRFLOW_KEY_PATH=${MINIO_AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/minio_airflow.key"}
ENV MINIO_AIRFLOW_CERT_PATH=${MINIO_AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/minio_airflow.crt"}
ENV MINIO_AIRFLOW_CA_PATH=${MINIO_AIRFLOW_CA_PATH:-"/etc/ssl/airflow/minio_airflow_ca.crt"}
ENV MINIO_SERVICE_NAME ${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT ${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_AIRFLOW_USER ${MINIO_AIRFLOW_USER:-"minio-user"}
ENV MINIO_DEFAULT_AIRFLOW_ARTIFACT_BUCKET ${MINIO_DEFAULT_AIRFLOW_ARTIFACT_BUCKET:-"models"}
ENV MINIO_AIRFLOW_PASSWORD ${MINIO_AIRFLOW_PASSWORD:-"minio-password"}

ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/airflow/airflow.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"
# Préparation de l’environnement Python
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3-venv \
    build-essential \
    curl \
    git \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt

# Installer les dépendances en contournant la restriction
RUN pip install --break-system-packages --force-reinstall -r requirements.txt
# Mettre à jour la liste des paquets et installer wget, gpg et lsb-release
RUN apt-get update && apt-get install -y wget gpg lsb-release curl iptables jq openssl libcap2-bin iproute2 ca-certificates dnsutils
RUN apt install -y nginx fcgiwrap
# Télécharger la clé GPG de HashiCorp et l'ajouter au keyring
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
# Ajouter le dépôt HashiCorp à la liste des sources
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
# Mettre à jour la liste des paquets et installer Vault
RUN apt-get update && apt-get install -y vault
#Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault
RUN vault --version
# Defining Minio related env. variables and certificates here to not mess with pip certificates
# ENV AIRFLOW_S3_ENDPOINT_URL=https://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}
# ENV AWS_ACCESS_KEY_ID=${MINIO_AIRFLOW_USER}
# ENV AWS_SECRET_ACCESS_KEY=${MINIO_AIRFLOW_PASSWORD}
# ENV AWS_CA_BUNDLE=${MINIO_AIRFLOW_CA_PATH}
# ENV REQUESTS_CA_BUNDLE=${AIRFLOW_PEM_PATH}
# Copie des DAGs et scripts
COPY dags/ ${AIRFLOW__CORE__DAGS_FOLDER}
# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY vault/vault.sh /usr/local/bin/vault.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh 
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY airflow/init-airflow.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

# Ports exposés (webserver)
EXPOSE 8790 80 443
# Point d’entrée
ENTRYPOINT ["entrypoint.sh"]
