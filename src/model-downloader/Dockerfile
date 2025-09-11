FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"model-downloader"}
ENV SERVICE_VERSION=${SERVICE_VERSION:-"v0.0.1"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"model-downloader"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"model-downloader"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV MODEL_DOWNLOADER_PEM_PATH ${MODEL_DOWNLOADER_PEM_PATH:-"/etc/ssl/model-downloader/model-downloader.pem"}
ENV MODEL_DOWNLOADER_CA_PATH ${MODEL_DOWNLOADER_CA_PATH:-"/etc/ssl/model-downloader/model-downloader.ca"}
ENV MODEL_DOWNLOADER_KEY_PATH ${MODEL_DOWNLOADER_KEY_PATH:-"/etc/ssl/model-downloader/model-downloader.key"}
ENV MODEL_DOWNLOADER_CERT_PATH ${MODEL_DOWNLOADER_CERT_PATH:-"/etc/ssl/model-downloader/model-downloader.crt"}

ENV MODEL_DOWNLOADER_SECRET_KEY=""
ENV MODEL_DOWNLOADER_INTERNAL_SECRET_KEY=""

ENV MINIO_SERVICE_NAME ${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT ${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_MODEL_DOWNLOADER_USER ${MINIO_MODEL_DOWNLOADER_USER:-"minio-user"}
ENV MINIO_MODEL_DOWNLOADER_PASSWORD ${MINIO_MODEL_DOWNLOADER_PASSWORD:-"minio-password"}
ENV MINIO_MODEL_DOWNLOADER_PEM_PATH ${MINIO_MODEL_DOWNLOADER_PEM_PATH:-"/etc/ssl/model-downloader/api-minio.pem"}
ENV MINIO_MODEL_DOWNLOADER_CA_PATH ${MINIO_MODEL_DOWNLOADER_CA_PATH:-"/etc/ssl/model-downloader/api-minio.ca"}
ENV MINIO_MODEL_DOWNLOADER_KEY_PATH ${MINIO_MODEL_DOWNLOADER_KEY_PATH:-"/etc/ssl/model-downloader/api-minio.key"}
ENV MINIO_MODEL_DOWNLOADER_CERT_PATH ${MINIO_MODEL_DOWNLOADER_CERT_PATH:-"/etc/ssl/model-downloader/api-minio.crt"}
ENV MINIO_MODEL_BUCKET_NAME ${MINIO_MODEL_BUCKET_NAME:-"models"}
ENV LOCAL_MODEL_DIRECTORY_PATH ${LOCAL_MODEL_DIRECTORY_PATH:-"/app/data"}

ENV API_MINIO_HOST=https://$SERVICE_NAME
ENV API_MINIO_INTERNAL_ENDPOINT_URL=/api/internal/
ENV API_MINIO_PROTECTED_ENDPOINT_URL=/api/protected/

ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_HOST=https://$API_GATEWAY_SERVICE_NAME

ENV API_MINIO_INTERNAL_SECRET_KEY=internal_secret_key
ENV API_MINIO_ALGORITHM=HS256
ENV API_MINIO_ACCESS_TOKEN_EXPIRE_MINUTES=30

ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe model-downloader
RUN groupadd --gid 999 --system model-downloader && \
    useradd --uid 999 --system --gid model-downloader --home-dir /home/model-downloader model-downloader && \
    mkdir -p /home/model-downloader && \
    chown -R model-downloader:model-downloader /home/model-downloader

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

# Installer Python et pip
RUN apt update && apt install -y python3-full python3-pip

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y curl jq unzip

# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY vault/vault.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vault.sh

COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN apt install -y nginx fcgiwrap

COPY nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt
COPY requirements/ requirements/

# Installer les dépendances en contournant la restriction
RUN pip install --break-system-packages -r requirements.txt

COPY . .

ENTRYPOINT ["entrypoint.sh"]