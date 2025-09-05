FROM ubuntu:noble-20250127

WORKDIR /app

ARG ENVIRONMENT=${ENVIRONMENT:-"prod"}

ENV SERVICE_NAME=${SERVICE_NAME:-"api-minio"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8020"}
ENV SERVICE_VERSION=${SERVICE_VERSION:-"v0.0.1"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"api-minio"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"api-password"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV API_MINIO_PEM_PATH ${API_MINIO_PEM_PATH:-"/etc/ssl/api-minio/api-minio.pem"}
ENV API_MINIO_CA_PATH ${API_MINIO_CA_PATH:-"/etc/ssl/api-minio/api-minio.ca"}
ENV API_MINIO_KEY_PATH ${API_MINIO_KEY_PATH:-"/etc/ssl/api-minio/api-minio.key"}
ENV API_MINIO_CERT_PATH ${API_MINIO_CERT_PATH:-"/etc/ssl/api-minio/api-minio.crt"}



ENV API_MINIO_SECRET_KEY=""
ENV API_MINIO_INTERNAL_SECRET_KEY=""

ENV MINIO_SERVICE_NAME ${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT ${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_API_MINIO_USER ${MINIO_API_MINIO_USER:-"minio-user"}
ENV MINIO_API_MINIO_PASSWORD ${MINIO_API_MINIO_PASSWORD:-"minio-password"}
ENV MINIO_API_MINIO_DATABASE ${MINIO_API_MINIO_DATABASE:-"file_storage"}
ENV MINIO_API_MINIO_PEM_PATH ${MINIO_API_MINIO_PEM_PATH:-"/etc/ssl/api-minio/mongdb_api-minio.pem"}
ENV MINIO_API_MINIO_CA_PATH ${MINIO_API_MINIO_CA_PATH:-"/etc/ssl/api-minio/mongdb_api-minio.ca"}
ENV MINIO_API_MINIO_KEY_PATH ${MINIO_API_MINIO_KEY_PATH:-"/etc/ssl/api-minio/mongdb_api-minio.key"}
ENV MINIO_API_MINIO_CERT_PATH ${MINIO_API_MINIO_CERT_PATH:-"/etc/ssl/api-minio/mongdb_api-minio.crt"}

ENV API_MINIO_API_MINIO_PEM_PATH ${API_MINIO_API_MINIO_PEM_PATH:-"/etc/ssl/api-minio/api-minio_api-minio.pem"}
ENV API_MINIO_API_MINIO_CA_PATH ${API_MINIO_API_MINIO_CA_PATH:-"/etc/ssl/api-minio/api-minio_api-minio.ca"}
ENV API_MINIO_API_MINIO_KEY_PATH ${API_MINIO_API_MINIO_KEY_PATH:-"/etc/ssl/api-minio/api-minio_api-minio.key"}
ENV API_MINIO_API_MINIO_CERT_PATH ${API_MINIO_API_MINIO_CERT_PATH:-"/etc/ssl/api-minio/api-minio_api-minio.crt"}

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

# Ajouter l'utilisateur et le groupe api-minio
RUN groupadd --gid 999 --system api-minio && \
    useradd --uid 999 --system --gid api-minio --home-dir /home/api-minio api-minio && \
    mkdir -p /home/api-minio && \
    chown -R api-minio:api-minio /home/api-minio

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

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt
COPY requirements/ requirements/

# Installer les dépendances en contournant la restriction
RUN pip install --break-system-packages -r requirements.txt

COPY . .

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y curl jq unzip

# Script d'entrée pour obtenir les certificats depuis Vault et démarrer Uvicorn
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY vault/vault.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vault.sh

COPY test/test.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/test.sh

RUN mv nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN apt install -y nginx fcgiwrap

RUN mv nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

RUN mv nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh


EXPOSE 8000

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["entrypoint.sh"]