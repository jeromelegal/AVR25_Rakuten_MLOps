FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"api-text-processing"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8030"}
ENV SERVICE_VERSION=${SERVICE_VERSION:-"v0.0.1"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"api-text-processing"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"api-password"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV API_TEXT_PROCESSING_PEM_PATH ${API_TEXT_PROCESSING_PEM_PATH:-"/etc/ssl/api-text-processing/api-text-processing.pem"}
ENV API_TEXT_PROCESSING_CA_PATH ${API_TEXT_PROCESSING_CA_PATH:-"/etc/ssl/api-text-processing/api-text-processing.ca"}
ENV API_TEXT_PROCESSING_KEY_PATH ${API_TEXT_PROCESSING_KEY_PATH:-"/etc/ssl/api-text-processing/api-text-processing.key"}
ENV API_TEXT_PROCESSING_CERT_PATH ${API_TEXT_PROCESSING_CERT_PATH:-"/etc/ssl/api-text-processing/api-text-processing.crt"}

ENV MLFLOW_ADDR ${VMLFLOW_ADDR:-"https://mlflow:5000"}
ENV MLFLOW_USERNAME=${VMLFLOW_USERNAME:-"mlflow-user"}
ENV MLFLOW_PASSWORD=${VMLFLOW_PASSWORD:-"mlflow-password"}
ENV MLFLOW_SERVICE_NAME ${VMLFLOW_SERVICE_NAME:-"mlflow"}
ENV API_TEXT_PROCESSING_MLFLOW_PEM_PATH ${TEXT_PROCESSING_API_MINIO_PEM_PATH:-"/etc/ssl/api-text-processing/mlflow.pem"}
ENV API_TEXT_PROCESSING_MLFLOW_CA_PATH ${TEXT_PROCESSING_API_MINIO_CA_PATH:-"/etc/ssl/api-text-processing/mlflow.ca"}
ENV API_TEXT_PROCESSING_MLFLOW_KEY_PATH ${TEXT_PROCESSING_API_MINIO_KEY_PATH:-"/etc/ssl/api-text-processing/mlflow.key"}
ENV API_TEXT_PROCESSING_MLFLOW_CERT_PATH ${TEXT_PROCESSING_API_MINIO_CERT_PATH:-"/etc/ssl/api-text-processing/mlflow.crt"}
ENV MLFLOW_TEXT_CLASSIFIER_MODEL_NAME ${MLFLOW_TEXT_CLASSIFIER_MODEL_NAME:-"text-classifier"}
ENV MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION ${MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION:-"1"}
ENV MLFLOW_TEXT_TRANSLATOR_MODEL_NAME ${MLFLOW_TEXT_TRANSLATOR_MODEL_NAME:-"text-translator"}
ENV MLFLOW_TEXT_TRANSLATOR_MODEL_VERSION ${MLFLOW_TEXT_TRANSLATOR_MODEL_VERSION:-"1"}
ENV MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME ${MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME:-"text-language-detector"}
ENV MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION ${MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION:-"1"}

ENV API_TEXT_PROCESSING_SECRET_KEY=""
ENV API_TEXT_PROCESSING_INTERNAL_SECRET_KEY=""

ENV API_TEXT_PROCESSING_HOST=https://$SERVICE_NAME
ENV API_TEXT_PROCESSING_INTERNAL_ENDPOINT_URL=/api/internal/
ENV API_TEXT_PROCESSING_PROTECTED_ENDPOINT_URL=/api/protected/


ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_HOST=https://$API_GATEWAY_SERVICE_NAME

ENV API_TEXT_PROCESSING_INTERNAL_SECRET_KEY=internal_secret_key
ENV API_TEXT_PROCESSING_ALGORITHM=HS256
ENV API_TEXT_PROCESSING_ACCESS_TOKEN_EXPIRE_MINUTES=30

ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe api-text-processing
RUN groupadd --gid 999 --system api-text-processing && \
    useradd --uid 999 --system --gid api-text-processing --home-dir /home/api-text-processing api-text-processing && \
    mkdir -p /home/api-text-processing && \
    chown -R api-text-processing:api-text-processing /home/api-text-processing

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

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y curl jq unzip

# miniconda
ENV CONDA_DIR=/opt/conda
RUN apt-get update && apt-get install -y wget bzip2 && \
    wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh && \
    $CONDA_DIR/bin/conda clean -afy

# conda in PATH
ENV PATH=$CONDA_DIR/bin:$PATH

# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY vault/vault.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vault.sh

COPY test/test.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/test.sh

COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN apt install -y nginx fcgiwrap

COPY nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh

# Copier le fichier d'environnement conda dans le conteneur
COPY environment.yml .

# create env conda
RUN conda config --set channel_priority strict && \
    conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --set always_yes yes && \
    conda tos accept --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --channel https://repo.anaconda.com/pkgs/r
RUN apt-get update && apt-get install -y build-essential g++ cmake && apt-get clean
RUN conda env create -f environment.yml && conda clean -afy

# activate env
SHELL ["/bin/bash", "--login", "-c"]
RUN echo "conda activate distilbert_docker" >> ~/.bashrc

ENV PATH=/opt/conda/envs/distilbert_docker/bin:$PATH
ENV PYTHONPATH=/app

COPY . .

EXPOSE 8030

ENTRYPOINT ["entrypoint.sh"]