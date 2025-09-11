FROM ubuntu:noble-20250127 AS builder

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

# Création d’un environnement virtuel
RUN python3 -m venv /opt/airflow_venv
ENV PATH="/opt/airflow_venv/bin:$PATH"

# Installation d’Airflow et des providers nécessaires
RUN pip install --upgrade pip && \
    pip install apache-airflow==2.8.1 \
    apache-airflow-providers-cncf-kubernetes \
    apache-airflow-providers-mongo \
    apache-airflow-providers-docker \
    apache-airflow-providers-http \
    apache-airflow-providers-slack \
    pandas \
    requests \
    pymongo \
    minio

# ----------

FROM ubuntu:noble-20250127

# Création de l’utilisateur airflow
RUN groupadd --gid 1000 airflow && \
    useradd --uid 1000 --gid airflow --home-dir /home/airflow airflow

# Variables d’environnement Airflow
ENV AIRFLOW_HOME=/opt/airflow
ENV PATH="/opt/airflow_venv/bin:$PATH"
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

# Variables d'env Vault & NGINX
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"airflow"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"airflow"}
ENV VAULT_ROLE=${VAULT_ROLE:-"your-role"}
ENV REPLSET_NAME=${REPLSET_NAME:-"rs0"}
ENV PORT=${PORT:-"9000"}
ENV GUI_PORT=${GUI_PORT:-"9001"}
ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
ENV TLS_MODE=${TLS_MODE:-"requireTLS"}
ENV AIRFLOW_ROOT_USER=${AIRFLOW_ROOT_USER:-"airflow-user"}
ENV AIRFLOW_ROOT_PASSWORD=${AIRFLOW_ROOT_PASSWORD:-"airflow-password"}
ENV AIRFLOW_ROOT_PASSWORD_PEM_PATH=${AIRFLOW_ROOT_PASSWORD_PEM_PATH:-"/etc/ssl/airflow/airflow.pem"}
ENV AIRFLOW_ROOT_CA_PATH=${AIRFLOW_ROOT_CA_PATH:-"/etc/ssl/airflow/airflow.ca"}
ENV AIRFLOW_ROOT_KEY_PATH=${AIRFLOW_ROOT_KEY_PATH:-"/etc/ssl/airflow/airflow.key"}
ENV AIRFLOW_ROOT_CERT_PATH=${AIRFLOW_ROOT_CERT_PATH:-"/etc/ssl/airflow/airflow.crt"}
ENV AIRFLOW_MINIO_PEM_PATH=${AIRFLOW_MINIO_PEM_PATH:-"/etc/ssl/airflow/airflow_airflow.pem"}
ENV AIRFLOW_MINIO_CA_PATH=${AIRFLOW_MINIO_CA_PATH:-"/etc/ssl/airflow/airflow_airflow.ca"}
ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV SERVICE_NAME=${SERVICE_NAME:-"minio"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"minio-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"minio.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/minio/minio.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Copie de l’environnement virtuel
COPY --from=builder /opt/airflow_venv /opt/airflow_venv

# Copie des DAGs et scripts
COPY dags/ /opt/airflow/dags/
COPY scripts/ /opt/airflow/scripts/

# Rendre les scripts exécutables
RUN chmod +x /opt/airflow/scripts/*.sh

# Création des dossiers nécessaires
RUN mkdir -p /opt/airflow/logs && chown -R airflow:airflow /opt/airflow

# Définir l’utilisateur
USER airflow

# Ports exposés (webserver)
EXPOSE 8080

# Point d’entrée
ENTRYPOINT ["/opt/airflow_venv/bin/airflow"]
CMD ["webserver"]