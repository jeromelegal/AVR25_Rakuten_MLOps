FROM ubuntu:noble-20250127 

WORKDIR /app
# Création de l’utilisateur airflow
RUN groupadd --gid 999 airflow && \
    useradd --uid 999 --gid airflow --home-dir /home/airflow airflow && \
    mkdir -p /home/airflow && \
    chown -R airflow:airflow /home/airflow

# Variables d’environnement Airflow
ENV AIRFLOW_HOME=/opt/airflow
ENV PATH="/opt/airflow_venv/bin:$PATH"
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__PARALLELISM=8
#ENV AIRFLOW__CORE__EXECUTOR=KubernetesExecutor
ENV AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV SERVICE_NAME=${SERVICE_NAME:-"airflow"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8793"}
ENV AIRFLOW__WEBSERVER__WEB_SERVER_PORT="$SERVICE_PORT"
ENV AIRFLOW__WEBSERVER__AUTHENTICATE="True"
#ENV AIRFLOW__WEBSERVER__AUTH_BACKEND="airflow.www.security.DefaultAuthBackend"

# Variables d'env Vault & NGINX
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"airflow"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"airflow"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}


ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
#ENV TLS_MODE=${TLS_MODE:-"requireTLS"}

ENV AIRFLOW_USER=${AIRFLOW_USER:-"airflow-user"}
ENV AIRFLOW_PASSWORD=${AIRFLOW_PASSWORD:-"airflow-password"}
ENV AIRFLOW_CA_PATH=${AIRFLOW_CA_PATH:-"/etc/ssl/airflow/airflow.ca"}
ENV AIRFLOW_KEY_PATH=${AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/airflow.key"}
ENV AIRFLOW_CERT_PATH=${AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/airflow_ca.crt"}
ENV AIRFLOW_PEM_PATH=${AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/airflow_airflow.pem"}
ENV AIRFLOW_INTERNAL_SECRET_KEY_PATH=${AIRFLOW_INTERNAL_SECRET_KEY_PATH:-"/etc/ssl/airflow/airflow_internal_secret.key"}
ENV AIRFLOW__API__SECRET_KEY=${AIRFLOW___API__SECRET_KEY:-""}

ENV AIRFLOW_AIRFLOW_PEM_PATH=${AIRFLOW_AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/airflow_airflow.pem"}
ENV AIRFLOW_AIRFLOW_KEY_PATH=${AIRFLOW_AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/airflow_airflow.key"}
ENV AIRFLOW_AIRFLOW_CERT_PATH=${AIRFLOW_AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/airflow_airflow.crt"}
ENV AIRFLOW_AIRFLOW_CA_PATH=${AIRFLOW_AIRFLOW_CA_PATH:-"/etc/ssl/airflow/airflow_airflow_ca.crt"}



ENV POSTGRESQL_SERVICE_NAME ${POSTGRESQL_SERVICE_NAME:-"postgresql"}
ENV POSTGRESQL_SERVICE_PORT ${POSTGRESQL_SERVICE_PORT:-"5432"}
ENV POSTGRESQL_AIRFLOW_USER ${POSTGRESQL_AIRFLOW_USER:-"airflow_user"}
ENV POSTGRESQL_AIRFLOW_SCHEMA=${POSTGRESQL_AIRFLOW_SCHEMA:-"airflow_schema"}
ENV POSTGRESQL_AIRFLOW_PASSWORD ${POSTGRESQL_AIRFLOW_PASSWORD:-"airflow_user_password"}
ENV POSTGRESQL_AIRFLOW_DATABASE ${POSTGRESQL_AIRFLOW_DATABASE:-"airflow"}

ENV POSTGRESQL_AIRFLOW_PEM_PATH=${POSTGRESQL_AIRFLOW_PEM_PATH:-"/etc/ssl/airflow/postgresql_airflow.pem"}
ENV POSTGRESQL_AIRFLOW_KEY_PATH=${POSTGRESQL_AIRFLOW_KEY_PATH:-"/etc/ssl/airflow/postgresql_airflow.key"}
ENV POSTGRESQL_AIRFLOW_CERT_PATH=${POSTGRESQL_AIRFLOW_CERT_PATH:-"/etc/ssl/airflow/postgresql_airflow.crt"}
ENV POSTGRESQL_AIRFLOW_CA_PATH=${POSTGRESQL_AIRFLOW_CA_PATH:-"/etc/ssl/airflow/postgresql_airflow_ca.crt"}
#ENV AIRFLOW__DATABASE__SQL_ALCHEMY_SCHEMA="$POSTGRESQL_AIRFLOW_SCHEMA"
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow_user:airflow_user_password@postgresql:5432/airflow?sslmode=verify-full&sslcert=/etc/ssl/airflow/postgresql_airflow.crt&sslkey=/etc/ssl/airflow/postgresql_airflow.key&sslrootcert=/etc/ssl/airflow/postgresql_airflow_ca.crt"

ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS="admin:admin"
ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS='{"admin": "admin"}'
#ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__API__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"
ENV AIRFLOW__API__AUTH_BACKEND="airflow.providers.fab.auth_manager.api.auth.backend.basic_auth" 



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
ENV SERVICE_NAME=${SERVICE_NAME:-"airflow"}

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
RUN pip install --break-system-packages -r requirements.txt
# Création d’un environnement virtuel
# RUN python3 -m venv /opt/airflow_venv
# ENV PATH="/opt/airflow_venv/bin:$PATH"

# Installation d’Airflow et des providers nécessaires
# RUN pip install --upgrade pip && \
#     pip install apache-airflow \
#     apache-airflow-providers-cncf-kubernetes \
#     apache-airflow-providers-mongo \
#     apache-airflow-providers-docker \
#     apache-airflow-providers-http \
#     apache-airflow-providers-slack \
#     requests \
#     psycopg2-binary \
#     asyncpg \
#     apache-airflow-providers-fab\
#     && rm -rf /root/.cache/pip
#psycopg[sqlalchemy,binary] \
#psycopg-pool \

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

# Copie des DAGs et scripts
COPY dags/ ${AIRFLOW__CORE__DAGS_FOLDER}

# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY vault/vault.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vault.sh

# Ports exposés (webserver)
EXPOSE 8793 8795

# Point d’entrée
ENTRYPOINT ["entrypoint.sh"]




# Copie de l’environnement virtuel
#COPY --from=builder /opt/airflow_venv /opt/airflow_venv

# Rendre les scripts exécutables
#RUN chmod +x /opt/airflow/scripts/*.sh

# Création des dossiers nécessaires
#RUN mkdir -p /opt/airflow/logs && chown -R airflow:airflow /opt/airflow

