FROM apache/airflow:3.0.6
WORKDIR /app

USER root
# Création de l’utilisateur airflow
RUN groupadd --gid 999 airflow && \
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
ENV AIRFLOW_API_SERVER_SERVICE_NAME=${AIRFLOW_API_SERVER_SERVICE_NAME:-"airflow-api-server"}
ENV AIRFLOW_API_SERVER_SERVICE_PORT=${AIRFLOW_API_SERVER_SERVICE_PORT:-"8790"}
ENV AIRFLOW_USER=${AIRFLOW_USER:-"airflow-user"}
ENV AIRFLOW_PASSWORD=${AIRFLOW_PASSWORD:-"airflow-password"}
ENV AIRFLOW_HOME=${AIRFLOW_HOME:-"/opt/airflow"}
ENV AIRFLOW__CORE__EXECUTOR=${AIRFLOW__CORE__EXECUTOR:-"CeleryExecutor"}
ENV AIRFLOW__CORE__LOAD_EXAMPLES=${AIRFLOW__CORE__LOAD_EXAMPLES:-"false"}
ENV AIRFLOW__CORE__AUTH_MANAGER=${AIRFLOW__CORE__AUTH_MANAGER:-"airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"}
ENV AIRFLOW__API__PORT=${SERVICE_PORT}
ENV AIRFLOW__API__EXPOSE_CONFIG=${AIRFLOW__API__EXPOSE_CONFIG:-"false"}
ENV AIRFLOW__API__EXPOSE_STACKTRACE=${AIRFLOW__API__EXPOSE_STACKTRACE:-"false"}
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=${AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION:-"true"}
ENV AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=${AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK:-"true"}
ENV AIRFLOW__CORE__FERNET_KEY=${AIRFLOW__CORE__FERNET_KEY:-"vYgDn-AesJP0QqFphmuOyuX4Qmw0CYeyWjULGiROzmE="}
ENV AIRFLOW__CORE__HOSTNAME_CALLABLE="airflow.utils.net.get_host_ip_address"
ENV AIRFLOW__LOGGING__REMOTE_LOGGING="true"
ENV AIRFLOW__LOGGING__LOG_SERVER_HOST=${AIRFLOW__LOGGING__LOG_SERVER_HOST:-"minio:9000"}
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER="s3://airflow-logs"
ENV AIRFLOW__LOGGING__DELETE_LOCAL_LOGS="false"
ENV AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID="minio_s3_conn"


ENV POSTGRESQL_SERVICE_NAME=${POSTGRESQL_SERVICE_NAME:-"postgresql"}
ENV POSTGRESQL_SERVICE_PORT=${POSTGRESQL_SERVICE_PORT:-"5432"}
ENV POSTGRESQL_AIRFLOW_USER=${POSTGRESQL_AIRFLOW_USER:-"airflow_user"}
ENV POSTGRESQL_AIRFLOW_PASSWORD=${POSTGRESQL_AIRFLOW_PASSWORD:-"airflow_user_password"}
ENV POSTGRESQL_AIRFLOW_DATABASE=${POSTGRESQL_AIRFLOW_DATABASE:-"airflow"}

ENV REDIS_SERVICE_NAME=${REDIS_SERVICE_NAME:-"redis"}
ENV REDIS_SERVICE_PORT=${REDIS_SERVICE_PORT:-"6379"}
ENV REDIS_AIRFLOW_USER=${REDIS_AIRFLOW_USER:-"airflow_user"}
ENV REDIS_AIRFLOW_PASSWORD=${REDIS_AIRFLOW_PASSWORD:-"airflow_user_password"}
ENV REDIS_AIRFLOW_DATABASE=${REDIS_AIRFLOW_DATABASE:-"airflow"}

ENV MINIO_AIRFLOW_PEM_PATH=${MINIO_AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/minio_airflow.pem"}
ENV MINIO_AIRFLOW_KEY_PATH=${MINIO_AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/minio_airflow.key"}
ENV MINIO_AIRFLOW_CERT_PATH=${MINIO_AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/minio_airflow.crt"}
ENV MINIO_AIRFLOW_CA_PATH=${MINIO_AIRFLOW_CA_PATH:-"/etc/ssl/airflow/minio_airflow_ca.crt"}
ENV MINIO_SERVICE_NAME=${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT=${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_DEFAULT_AIRFLOW_ARTIFACT_BUCKET=${MINIO_DEFAULT_AIRFLOW_ARTIFACT_BUCKET:-"airflow"}
ENV MINIO_AIRFLOW_USER=${MINIO_AIRFLOW_USER:-"minio-user"}
ENV MINIO_AIRFLOW_PASSWORD=${MINIO_AIRFLOW_PASSWORD:-"minio-password"}

ENV API_GATEWAY_SERVICE_NAME=${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_USER_NAME=${API_GATEWAY_SERVICE_NAME:-"airflow"}
ENV API_GATEWAY_USER_PASSWORD=${API_GATEWAY_SERVICE_NAME:-"airflow-password"}
ENV API_GATEWAY_USER_EMAIL=${API_GATEWAY_SERVICE_NAME:-"airflow@example.org"}
ENV API_GATEWAY_AIRFLOW_PEM_PATH=${API_GATEWAY_AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/api-gateway_airflow.pem"}
ENV API_GATEWAY_AIRFLOW_CA_PATH=${API_GATEWAY_AIRFLOW_CA_PATH:-"/etc/ssl/airflow/api-gateway_airflow.key"}
ENV API_GATEWAY_AIRFLOW_KEY_PATH=${API_GATEWAY_AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/api-gateway_airflow.crt"}
ENV API_GATEWAY_AIRFLOW_CERT_PATH=${API_GATEWAY_AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/api-gateway_airflow_ca.crt"}

ENV TRAIN_TEST_SPLIT_TARGETED=${TRAIN_TEST_SPLIT_TARGETED:-"0.8"}


ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/airflow/airflow.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"
# Préparation de l’environnement Python
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Since we got issue with SSL connection to redis, we used these commands as detailed in
# https://stackoverflow.com/questions/72627218/openssl-error-messages-error0a000126ssl-routinesunexpected-eof-while-readin
# Redis error was: Error accepting a client connection: error:0A000126:SSL routines::unexpected eof while reading (conn: fd=8)

RUN apt autoremove && \
    apt-get update && \
    apt-get install -y libssl-dev autoconf libtool make && \
    cd /usr/local/src && \
    wget https://curl.haxx.se/download/curl-7.88.1.zip && \
    unzip curl-7.88.1.zip && \
    cd curl-7.88.1 && \
    ./buildconf && \
    ./configure --with-ssl  && \
    make && \
    sudo make install && \
    sudo cp /usr/local/bin/curl /usr/bin/curl && \
    sudo ldconfig && \
    cd .. && rm curl-7.88.1.zip

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt

# Installer les dépendances en contournant la restriction
USER airflow
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r requirements.txt

USER root
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
ENV AIRFLOW_S3_ENDPOINT_URL=https://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}
ENV AWS_ACCESS_KEY_ID=${MINIO_AIRFLOW_USER}
ENV AWS_SECRET_ACCESS_KEY=${MINIO_AIRFLOW_PASSWORD}
ENV AWS_CA_BUNDLE=${MINIO_AIRFLOW_CA_PATH}
# ENV REQUESTS_CA_BUNDLE=${AIRFLOW_PEM_PATH}
# Copie des DAGs et scripts
COPY --chown=airflow:root dags/ /opt/airflow/dags
# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY vault/vault.sh /usr/local/bin/vault.sh
COPY custom-entrypoint.sh /usr/local/bin/custom-entrypoint.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY airflow/init-airflow.sh /usr/local/bin/
COPY airflow/utils.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

# Ports exposés (webserver)
EXPOSE 8790 80 443
# Point d’entrée
ENTRYPOINT ["/usr/bin/dumb-init", "--", "custom-entrypoint.sh"]
