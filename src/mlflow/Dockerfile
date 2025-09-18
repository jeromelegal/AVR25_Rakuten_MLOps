FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"mlflow"}
ENV SERVICE_PORT=${SERVICE_PORT:-"5000"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"mlflow"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"mlflow"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV MLFLOW_PEM_PATH ${MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/mlflow.pem"}
ENV MLFLOW_CA_PATH ${MLFLOW_CA_PATH:-"/etc/ssl/mlflow/mlflow.ca"}
ENV MLFLOW_KEY_PATH ${MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/mlflow.key"}
ENV MLFLOW_CERT_PATH ${MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/mlflow.crt"}

ENV MLFLOW_SECRET_KEY=""
ENV MLFLOW_INTERNAL_SECRET_KEY=""

ENV POSTGRESQL_SERVICE_NAME ${POSTGRESQL_SERVICE_NAME:-"postgresql"}
ENV POSTGRESQL_SERVICE_PORT ${POSTGRESQL_SERVICE_PORT:-"5432"}
ENV POSTGRESQL_MLFLOW_USER ${POSTGRESQL_MLFLOW_USER:-"mlflow_user"}
ENV POSTGRESQL_MLFLOW_PASSWORD ${POSTGRESQL_MLFLOW_PASSWORD:-"mlflow_user_password"}
ENV POSTGRESQL_MLFLOW_DATABASE ${POSTGRESQL_MLFLOW_DATABASE:-"mlflow"}
ENV POSTGRESQL_MLFLOW_PEM_PATH ${POSTGRESQL_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/postgresql_mlflow.pem"}
ENV POSTGRESQL_MLFLOW_CA_PATH ${POSTGRESQL_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/postgresql_mlflow.ca"}
ENV POSTGRESQL_MLFLOW_KEY_PATH ${POSTGRESQL_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/postgresql_mlflow.key"}
ENV POSTGRESQL_MLFLOW_CERT_PATH ${POSTGRESQL_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/postgresql_mlflow.crt"}

ENV MINIO_SERVICE_NAME ${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT ${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_MLFLOW_USER ${MINIO_MLFLOW_USER:-"minio-user"}
ENV MINIO_DEFAULT_MLFLOW_ARTIFACT_BUCKET ${MINIO_DEFAULT_MLFLOW_ARTIFACT_BUCKET:-"models"}
ENV MINIO_MLFLOW_PASSWORD ${MINIO_MLFLOW_PASSWORD:-"minio-password"}
ENV MINIO_MLFLOW_PEM_PATH ${MINIO_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/minio_mlflow.pem"}
ENV MINIO_MLFLOW_CA_PATH ${MINIO_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/minio_mlflow.ca"}
ENV MINIO_MLFLOW_KEY_PATH ${MINIO_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/minio_mlflow.key"}
ENV MINIO_MLFLOW_CERT_PATH ${MINIO_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/minio_mlflow.crt"}
ENV MINIO_RAW_MODEL_BUCKET_NAME ${MINIO_RAW_MODEL_BUCKET_NAME:-"raw-models"}

ENV MLFLOW_HOST=https://$SERVICE_NAME
ENV MLFLOW_USERNAME=${MLFLOW_USERNAME:-"mlflow-user"}
ENV MLFLOW_PASSWORD=${MLFLOW_PASSWORD:-"mlflow-password"}
ENV MLFLOW_MLFLOW_PEM_PATH ${MLFLOW_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.pem"}
ENV MLFLOW_MLFLOW_CA_PATH ${MLFLOW_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.ca"}
ENV MLFLOW_MLFLOW_KEY_PATH ${MLFLOW_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.key"}
ENV MLFLOW_MLFLOW_CERT_PATH ${MLFLOW_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.crt"}

ENV MLFLOW_TRACKING_URI="https://${SERVICE_NAME}:${SERVICE_PORT}"
ENV MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME=${MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME:-"image_classifier_model"}
ENV MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_NAME=${MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_NAME:-"f1_score"}
ENV MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE=${MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE:-"0.59"}
ENV MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME=${MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME:-"Train image processing model"}
ENV MLFLOW_IMAGE_RUN_NAME=${MLFLOW_IMAGE_RUN_NAME:-"initial_run"}
ENV MLFLOW_TEXT_CLASSIFIER_MODEL_NAME=${MLFLOW_TEXT_CLASSIFIER_MODEL_NAME:-"text-classifier"}
ENV MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_NAME=${MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_NAME:-"f1_score"}
ENV MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE=${MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE:-"0.81"}
ENV MLFLOW_TEXT_TRANSLATOR_MODEL_NAME=${MLFLOW_TEXT_TRANSLATOR_MODEL_NAME:-"text-translator"}
ENV MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME=${MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME:-"text-language-detector"}
ENV MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME=${MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME:-"Train text processing model"}
ENV MLFLOW_TEXT_RUN_NAME=${MLFLOW_TEXT_RUN_NAME:-"initial_run"}
ENV MLFLOW_DELAY_BETWEEN_RETRIES_IN_SECONDS=${DELAY_BETWEEN_RETRIES_IN_SECONDS:-"10"}
ENV MLFLOW_DATA_DIRECTORY=${DATA_DIRECTORY:-"/app/data"}
ENV MLFLOW_IMAGE_MODEL_DATA_DIRECTORY=${IMAGE_MODEL_DATA_DIRECTORY:-"image_model"}
ENV MLFLOW_TEXT_CLASSIFIER_MODEL_DATA_DIRECTORY=${TEXT_CLASSIFIER_MODEL_DATA_DIRECTORY:-"text_classifier_model"}
ENV MLFLOW_TEXT_TRANSLATOR_MODEL_DATA_DIRECTORY=${TEXT_TRANSLATOR_MODEL_DATA_DIRECTORY:-"text_translator_model"}
ENV MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_DATA_DIRECTORY=${TEXT_LANGUAGE_DETECTOR_MODEL_DATA_DIRECTORY:-"text_language_detector_model"}

ENV MLFLOW_INTERNAL_SECRET_KEY=internal_secret_key
ENV MLFLOW_ALGORITHM=HS256
ENV MLFLOW_ACCESS_TOKEN_EXPIRE_MINUTES=30

ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe mlflow
RUN groupadd --gid 999 --system mlflow && \
    useradd --uid 999 --system --gid mlflow --home-dir /home/mlflow mlflow && \
    mkdir -p /home/mlflow && \
    chown -R mlflow:mlflow /home/mlflow

# Mettre à jour la liste des paquets et installer wget, gpg et lsb-release
RUN apt-get update && apt-get install -y wget gpg lsb-release curl iptables jq openssl libcap2-bin iproute2 ca-certificates dnsutils git

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

# Installer Python et pip
RUN apt update && apt install -y python3-full python3-pip


# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt

# Installer les dépendances en contournant la restriction
RUN pip install --break-system-packages -r requirements.txt

# Give rights to the mlruns directory that seems to be used by mlflow as a buffer
RUN mkdir mlruns && chown mlflow:mlflow mlruns

# Give rights to /app/data use to store files from Minio
RUN mkdir data && chown mlflow:mlflow data && chown mlflow:mlflow .


# Defining Minio related env. variables and certificates here to not mess with pip certificates
ENV MLFLOW_S3_ENDPOINT_URL=https://${MINIO_SERVICE_NAME}:${MINIO_SERVICE_PORT}
ENV AWS_ACCESS_KEY_ID=${MINIO_MLFLOW_USER}
ENV AWS_SECRET_ACCESS_KEY=${MINIO_MLFLOW_PASSWORD}
ENV AWS_CA_BUNDLE=${MINIO_MLFLOW_CA_PATH}
ENV REQUESTS_CA_BUNDLE=${MLFLOW_PEM_PATH}

COPY . .

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y curl jq unzip

# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY vault/vault.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vault.sh

RUN mv nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN apt install -y nginx fcgiwrap

RUN mv nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

RUN mv nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh


EXPOSE 5000 80 443

ENTRYPOINT ["entrypoint.sh"]