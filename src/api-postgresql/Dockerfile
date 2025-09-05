FROM ubuntu:noble-20250127

WORKDIR /app

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"api-postgresql"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"api-postgresql"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV API_POSTGRESQL_PEM_PATH ${API_POSTGRESQL_PEM_PATH:-"/etc/ssl/api-postgresql/api-postgresql.pem"}
ENV API_POSTGRESQL_CA_PATH ${API_POSTGRESQL_CA_PATH:-"/etc/ssl/api-postgresql/api-postgresql_ca.crt"}
ENV API_POSTGRESQL_KEY_PATH ${API_POSTGRESQL_KEY_PATH:-"/etc/ssl/api-postgresql/api-postgresql.key"}
ENV API_POSTGRESQL_CERT_PATH ${API_POSTGRESQL_CERT_PATH:-"/etc/ssl/api-postgresql/api-postgresql.crt"}

ENV SERVICE_NAME=${SERVICE_NAME:-"api-postgresql"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8010"}

ENV API_POSTGRESQL_SECRET_KEY=""
ENV API_POSTGRESQL_INTERNAL_SECRET_KEY=""

ENV POSTGRESQL_SERVICE_NAME ${POSTGRESQL_SERVICE_NAME:-"postgresql"}
ENV POSTGRESQL_SERVICE_PORT ${POSTGRESQL_SERVICE_PORT:-"5432"}
ENV POSTGRESQL_API_POSTGRESQL_USER ${POSTGRESQL_API_POSTGRESQL_USER:-"db_manager_user"}
ENV POSTGRESQL_API_POSTGRESQL_PASSWORD ${POSTGRESQL_API_POSTGRESQL_PASSWORD:-"db_manager_user_password"}
ENV POSTGRESQL_API_POSTGRESQL_DATABASE ${POSTGRESQL_API_POSTGRESQL_DATABASE:-"file_storage"}
ENV POSTGRESQL_API_POSTGRESQL_PEM_PATH ${POSTGRESQL_API_POSTGRESQL_PEM_PATH:-"/etc/ssl/api-postgresql/postgresql_api-postgresql.pem"}
ENV POSTGRESQL_API_POSTGRESQL_CA_PATH ${POSTGRESQL_API_POSTGRESQL_CA_PATH:-"/etc/ssl/api-postgresql/postgresql_api-postgresql_ca.crt"}
ENV POSTGRESQL_API_POSTGRESQL_KEY_PATH ${POSTGRESQL_API_POSTGRESQL_KEY_PATH:-"/etc/ssl/api-postgresql/postgresql_api-postgresql.key"}
ENV POSTGRESQL_API_POSTGRESQL_CERT_PATH ${POSTGRESQL_API_POSTGRESQL_CERT_PATH:-"/etc/ssl/api-postgresql/postgresql_api-postgresql.crt"}

ENV API_POSTGRESQL_API_POSTGRESQL_PEM_PATH ${API_POSTGRESQL_API_POSTGRESQL_PEM_PATH:-"/etc/ssl/api-postgresql/api-postgresql_api-postgresql.pem"}
ENV API_POSTGRESQL_API_POSTGRESQL_CA_PATH ${API_POSTGRESQL_API_POSTGRESQL_CA_PATH:-"/etc/ssl/api-postgresql/api-postgresql_api-postgresql_ca.crt"}
ENV API_POSTGRESQL_API_POSTGRESQL_KEY_PATH ${API_POSTGRESQL_API_POSTGRESQL_KEY_PATH:-"/etc/ssl/api-postgresql/api-postgresql_api-postgresql.key"}
ENV API_POSTGRESQL_API_POSTGRESQL_CERT_PATH ${API_POSTGRESQL_API_POSTGRESQL_CERT_PATH:-"/etc/ssl/api-postgresql/api-postgresql_api-postgresql.crt"}

ENV API_POSTGRESQL_HOST=https://$SERVICE_NAME
ENV API_POSTGRESQL_INTERNAL_ENDPOINT_URL=/api/internal/
ENV API_POSTGRESQL_PROTECTED_ENDPOINT_URL=/api/protected/

ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_HOST=https://$API_GATEWAY_SERVICE_NAME

ENV API_POSTGRESQL_INTERNAL_SECRET_KEY=internal_secret_key
ENV API_POSTGRESQL_ALGORITHM=HS256
ENV API_POSTGRESQL_ACCESS_TOKEN_EXPIRE_MINUTES=30

ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe api-postgresql
RUN groupadd --gid 999 --system api-postgresql && \
    useradd --uid 999 --system --gid api-postgresql --home-dir /home/api-postgresql api-postgresql && \
    mkdir -p /home/api-postgresql && \
    chown -R api-postgresql:api-postgresql /home/api-postgresql

# Mettre à jour la liste des paquets et installer wget, gpg et lsb-release
RUN apt-get update && apt-get install -y wget gpg lsb-release curl iptables jq openssl libcap2-bin iproute2 ca-certificates dnsutils

RUN apt install -y nginx fcgiwrap

# Télécharger la clé GPG de HashiCorp et l'ajouter au keyring
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Ajouter le dépôt HashiCorp à la liste des sources
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

# Mettre à jour la liste des paquets et installer Vault
RUN apt-get update && apt-get install -y vault

# Retirer le verrouillage de la mémoire
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

EXPOSE 8010

ENTRYPOINT ["entrypoint.sh"]
