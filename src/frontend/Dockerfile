# frontend/Dockerfile
FROM ubuntu:noble-20250127


ENV SERVICE_NAME=${SERVICE_NAME:-"frontend"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"$SERVICE_NAME"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"$SERVICE_NAME"}

ENV FRONTEND_PEM_PATH ${FRONTEND_PEM_PATH:-"/etc/ssl/frontend/frontend.pem"}
ENV FRONTEND_CA_PATH ${FRONTEND_CA_PATH:-"/etc/ssl/frontend/frontend.ca"}
ENV FRONTEND_KEY_PATH ${FRONTEND_KEY_PATH:-"/etc/ssl/frontend/frontend.key"}
ENV FRONTEND_CERT_PATH ${FRONTEND_CERT_PATH:-"/etc/ssl/frontend/frontend.crt"}

ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_SERVICE_PORT ${API_GATEWAY_SERVICE_PORT:-"8000"}
ENV API_GATEWAY_BASE_URL ${API_GATEWAY_BASE_URL:-"https://$API_GATEWAY_SERVICE_NAME:$API_GATEWAY_SERVICE_PORT"}
ENV API_GATEWAY_FRONTEND_PEM_PATH ${API_GATEWAY_FRONTEND_PEM_PATH:-"/etc/ssl/frontend/api-gateway_frontend.pem"}
ENV API_GATEWAY_FRONTEND_CA_PATH ${API_GATEWAY_FRONTEND_CA_PATH:-"/etc/ssl/frontend/api-gateway_frontend.ca"}
ENV API_GATEWAY_FRONTEND_KEY_PATH ${API_GATEWAY_FRONTEND_KEY_PATH:-"/etc/ssl/frontend/api-gateway_frontend.key"}
ENV API_GATEWAY_FRONTEND_CERT_PATH ${API_GATEWAY_FRONTEND_CERT_PATH:-"/etc/ssl/frontend/api-gateway_frontend.crt"}


ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"


ENV NODE_CONFIG_FILE="server.js"

# Mettre à jour les paquets et installer les dépendances nécessaires
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs openssl

# Définir la variable d'environnement pour Node.js
ENV NODE_OPTIONS=--openssl-legacy-provider

WORKDIR /app


# Ajouter l'utilisateur et le groupe frontend
RUN groupadd --gid 999 --system frontend && \
    useradd --uid 999 --system --gid frontend --home-dir /home/frontend frontend && \
    mkdir -p /home/frontend && \
    chown -R frontend:frontend /home/frontend

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


COPY node/generate-config.sh /usr/local/bin/generate-config.sh
RUN chmod +x /usr/local/bin/generate-config.sh


COPY package*.json ./
RUN npm install

COPY . .

RUN npm install --save-dev @babel/core
RUN npm install papaparse

RUN npm run build

EXPOSE 3000

ENTRYPOINT ["entrypoint.sh"]