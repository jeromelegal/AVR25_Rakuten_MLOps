FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"api-gateway"}
ENV SERVICE_PORT=${SERVICE_PORT:-"9000"}

ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"$SERVICE_NAME"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"$SERVICE_NAME"}

ENV API_GATEWAY_PEM_PATH=${API_GATEWAY_PEM_PATH:-"/etc/ssl/api-gateway/api-gateway.pem"}
ENV API_GATEWAY_CA_PATH=${API_GATEWAY_CA_PATH:-"/etc/ssl/api-gateway/api-gateway.ca"}
ENV API_GATEWAY_KEY_PATH=${API_GATEWAY_KEY_PATH:-"/etc/ssl/api-gateway/api-gateway.key"}
ENV API_GATEWAY_CERT_PATH=${API_GATEWAY_CERT_PATH:-"/etc/ssl/api-gateway/api-gateway.crt"}

ENV API_GATEWAY_SECRET_KEY=""
ENV API_GATEWAY_INTERNAL_SECRET_KEY=""

ENV API_MONGODB_SERVICE_NAME=${API_MONGODB_SERVICE_NAME:-"api-mongodb"}
ENV API_MONGODB_SERVICE_PORT=${API_MONGODB_SERVICE_PORT:-"8000"}
ENV API_MONGODB_BASE_URL=${API_MONGODB_BASE_URL:-"https://$API_MONGODB_SERVICE_NAME:$API_MONGODB_SERVICE_PORT"}
ENV API_MONGODB_API_GATEWAY_PEM_PATH=${API_MONGODB_API_GATEWAY_PEM_PATH:-"/etc/ssl/api-gateway/mongodb_api-gateway.pem"}
ENV API_MONGODB_API_GATEWAY_CA_PATH=${API_MONGODB_API_GATEWAY_CA_PATH:-"/etc/ssl/api-gateway/mongodb_api-gateway.ca"}
ENV API_MONGODB_API_GATEWAY_KEY_PATH=${API_MONGODB_API_GATEWAY_KEY_PATH:-"/etc/ssl/api-gateway/mongodb_api-gateway.key"}
ENV API_MONGODB_API_GATEWAY_CERT_PATH=${API_MONGODB_API_GATEWAY_CERT_PATH:-"/etc/ssl/api-gateway/mongodb_api-gateway.crt"}

ENV API_POSTGRESQL_SERVICE_NAME=${API_POSTGRESQL_SERVICE_NAME:-"api-postgresql"}
ENV API_POSTGRESQL_SERVICE_PORT=${API_POSTGRESQL_SERVICE_PORT:-"8010"}
ENV API_POSTGRESQL_BASE_URL=${API_POSTGRESQL_BASE_URL:-"https://$API_POSTGRESQL_SERVICE_NAME:$API_POSTGRESQL_SERVICE_PORT"}
ENV API_POSTGRESQL_API_GATEWAY_PEM_PATH=${API_POSTGRESQL_API_GATEWAY_PEM_PATH:-"/etc/ssl/api-gateway/postgresql_api-gateway.pem"}
ENV API_POSTGRESQL_API_GATEWAY_CA_PATH=${API_POSTGRESQL_API_GATEWAY_CA_PATH:-"/etc/ssl/api-gateway/postgresql_api-gateway.ca"}
ENV API_POSTGRESQL_API_GATEWAY_KEY_PATH=${API_POSTGRESQL_API_GATEWAY_KEY_PATH:-"/etc/ssl/api-gateway/postgresql_api-gateway.key"}
ENV API_POSTGRESQL_API_GATEWAY_CERT_PATH=${API_POSTGRESQL_API_GATEWAY_CERT_PATH:-"/etc/ssl/api-gateway/postgresql_api-gateway.crt"}

ENV API_GATEWAY_HOST="https://$SERVICE_NAME"
ENV API_GATEWAY_INTERNAL_ENDPOINT_URL="/api/internal"
ENV API_GATEWAY_PROTECTED_ENDPOINT_URL="/api/protected"

ENV API_GATEWAY_ALGORITHM="HS256"
ENV API_GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES=30

ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe api-gateway
RUN groupadd --gid 999 --system api-gateway && \
    useradd --uid 999 --system --gid api-gateway --home-dir /home/api-gateway api-gateway && \
    mkdir -p /home/api-gateway && \
    chown -R api-gateway:api-gateway /home/api-gateway

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

RUN mv nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN apt install -y nginx fcgiwrap

RUN mv nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

RUN mv nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt requirements.txt

# Installer les dépendances en contournant la restriction
RUN pip install --break-system-packages -r requirements.txt

COPY . .

EXPOSE 9000

ENTRYPOINT ["entrypoint.sh"]
