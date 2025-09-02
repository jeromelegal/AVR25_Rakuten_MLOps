# reverse-proxy/Dockerfile
FROM ubuntu:noble-20250127


ENV SERVICE_NAME=${SERVICE_NAME:-"reverse-proxy"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"$SERVICE_NAME"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"$SERVICE_NAME"}

ENV REVERSE_PROXY_PEM_PATH ${REVERSE_PROXY_PEM_PATH:-"/etc/ssl/reverse-proxy/reverse-proxy.pem"}
ENV REVERSE_PROXY_CA_PATH ${REVERSE_PROXY_CA_PATH:-"/etc/ssl/reverse-proxy/reverse-proxy.ca"}
ENV REVERSE_PROXY_KEY_PATH ${REVERSE_PROXY_KEY_PATH:-"/etc/ssl/reverse-proxy/reverse-proxy.key"}
ENV REVERSE_PROXY_CERT_PATH ${REVERSE_PROXY_CERT_PATH:-"/etc/ssl/reverse-proxy/reverse-proxy.crt"}

ENV FRONTEND_SERVICE_NAME ${FRONTEND_SERVICE_NAME:-"frontend"}
ENV FRONTEND_SERVICE_PORT ${FRONTEND_SERVICE_PORT:-"3000"}
ENV FRONTEND_BASE_URL ${FRONTEND_BASE_URL:-"https://$FRONTEND_SERVICE_NAME:$FRONTEND_SERVICE_PORT"}
ENV FRONTEND_REVERSE_PROXY_PEM_PATH ${FRONTEND_REVERSE_PROXY_PEM_PATH:-"/etc/ssl/reverse-proxy/frontend_reverse-proxy.pem"}
ENV FRONTEND_REVERSE_PROXY_CA_PATH ${FRONTEND_REVERSE_PROXY_CA_PATH:-"/etc/ssl/reverse-proxy/frontend_reverse-proxy.ca"}
ENV FRONTEND_REVERSE_PROXY_KEY_PATH ${FRONTEND_REVERSE_PROXY_KEY_PATH:-"/etc/ssl/reverse-proxy/frontend_reverse-proxy.key"}
ENV FRONTEND_REVERSE_PROXY_CERT_PATH ${FRONTEND_REVERSE_PROXY_CERT_PATH:-"/etc/ssl/reverse-proxy/frontend_reverse-proxy.crt"}


ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_SERVICE_PORT ${API_GATEWAY_SERVICE_PORT:-"9000"}
ENV API_GATEWAY_BASE_URL ${API_GATEWAY_BASE_URL:-"https://$API_GATEWAY_SERVICE_NAME:$API_GATEWAY_SERVICE_PORT"}
ENV API_GATEWAY_REVERSE_PROXY_PEM_PATH ${API_GATEWAY_REVERSE_PROXY_PEM_PATH:-"/etc/ssl/reverse-proxy/api-gateway_reverse-proxy.pem"}
ENV API_GATEWAY_REVERSE_PROXY_CA_PATH ${API_GATEWAY_REVERSE_PROXY_CA_PATH:-"/etc/ssl/reverse-proxy/api-gateway_reverse-proxy.ca"}
ENV API_GATEWAY_REVERSE_PROXY_KEY_PATH ${API_GATEWAY_REVERSE_PROXY_KEY_PATH:-"/etc/ssl/reverse-proxy/api-gateway_reverse-proxy.key"}
ENV API_GATEWAY_REVERSE_PROXY_CERT_PATH ${API_GATEWAY_REVERSE_PROXY_CERT_PATH:-"/etc/ssl/reverse-proxy/api-gateway_reverse-proxy.crt"}


ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"


WORKDIR /app

# Ajouter l'utilisateur et le groupe reverse-proxy
RUN groupadd --gid 999 --system reverse-proxy && \
    useradd --uid 999 --system --gid reverse-proxy --home-dir /home/reverse-proxy reverse-proxy && \
    mkdir -p /home/reverse-proxy && \
    chown -R reverse-proxy:reverse-proxy /home/reverse-proxy

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



EXPOSE 443
ENTRYPOINT ["entrypoint.sh"]


