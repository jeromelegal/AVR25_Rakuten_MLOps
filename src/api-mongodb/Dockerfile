FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"api-mongodb"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8000"}

ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"api-mongodb"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"api-mongodb"}
ENV VAULT_SERVICE_NAME ${VAULT_SERVICE_NAME:-"vault"}

ENV API_MONGODB_PEM_PATH ${API_MONGODB_PEM_PATH:-"/etc/ssl/api-mongodb/api-mongodb.pem"}
ENV API_MONGODB_CA_PATH ${API_MONGODB_CA_PATH:-"/etc/ssl/api-mongodb/api-mongodb.ca"}
ENV API_MONGODB_KEY_PATH ${API_MONGODB_KEY_PATH:-"/etc/ssl/api-mongodb/api-mongodb.key"}
ENV API_MONGODB_CERT_PATH ${API_MONGODB_CERT_PATH:-"/etc/ssl/api-mongodb/api-mongodb.crt"}



ENV API_MONGODB_SECRET_KEY=""
ENV API_MONGODB_INTERNAL_SECRET_KEY=""

ENV MONGODB_SERVICE_NAME ${MONGODB_SERVICE_NAME:-"mongodb"}
ENV MONGODB_SERVICE_PORT ${MONGODB_SERVICE_PORT:-"27017"}
ENV MONGODB_API_MONGODB_USER ${MONGODB_API_MONGODB_USER:-"db_manager_user"}
ENV MONGODB_API_MONGODB_PASSWORD ${MONGODB_API_MONGODB_PASSWORD:-"db_manager_user_password"}
ENV MONGODB_API_MONGODB_DATABASE ${MONGODB_API_MONGODB_DATABASE:-"file_storage"}
ENV MONGODB_API_MONGODB_PEM_PATH ${MONGODB_API_MONGODB_PEM_PATH:-"/etc/ssl/api-mongodb/mongdb_api-mongodb.pem"}
ENV MONGODB_API_MONGODB_CA_PATH ${MONGODB_API_MONGODB_CA_PATH:-"/etc/ssl/api-mongodb/mongdb_api-mongodb.ca"}
ENV MONGODB_API_MONGODB_KEY_PATH ${MONGODB_API_MONGODB_KEY_PATH:-"/etc/ssl/api-mongodb/mongdb_api-mongodb.key"}
ENV MONGODB_API_MONGODB_CERT_PATH ${MONGODB_API_MONGODB_CERT_PATH:-"/etc/ssl/api-mongodb/mongdb_api-mongodb.crt"}

ENV API_MONGODB_API_MONGODB_PEM_PATH ${API_MONGODB_API_MONGODB_PEM_PATH:-"/etc/ssl/api-mongodb/api-mongodb_api-mongodb.pem"}
ENV API_MONGODB_API_MONGODB_CA_PATH ${API_MONGODB_API_MONGODB_CA_PATH:-"/etc/ssl/api-mongodb/api-mongodb_api-mongodb.ca"}
ENV API_MONGODB_API_MONGODB_KEY_PATH ${API_MONGODB_API_MONGODB_KEY_PATH:-"/etc/ssl/api-mongodb/api-mongodb_api-mongodb.key"}
ENV API_MONGODB_API_MONGODB_CERT_PATH ${API_MONGODB_API_MONGODB_CERT_PATH:-"/etc/ssl/api-mongodb/api-mongodb_api-mongodb.crt"}

ENV API_MONGODB_HOST=https://$SERVICE_NAME
ENV API_MONGODB_INTERNAL_ENDPOINT_URL=/api/internal/
ENV API_MONGODB_PROTECTED_ENDPOINT_URL=/api/protected/


ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
ENV API_GATEWAY_HOST=https://$API_GATEWAY_SERVICE_NAME

ENV API_MONGODB_INTERNAL_SECRET_KEY=internal_secret_key
ENV API_MONGODB_ALGORITHM=HS256
ENV API_MONGODB_ACCESS_TOKEN_EXPIRE_MINUTES=30



ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe api-mongodb
RUN groupadd --gid 999 --system api-mongodb && \
    useradd --uid 999 --system --gid api-mongodb --home-dir /home/api-mongodb api-mongodb && \
    mkdir -p /home/api-mongodb && \
    chown -R api-mongodb:api-mongodb /home/api-mongodb

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