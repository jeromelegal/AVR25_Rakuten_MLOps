FROM ubuntu:noble-20250127

WORKDIR /app

ENV SERVICE_NAME=${SERVICE_NAME:-"mlflow"}
ENV SERVICE_PORT=${SERVICE_PORT:-"8000"}

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

ENV MONGODB_SERVICE_NAME ${MONGODB_SERVICE_NAME:-"mongodb"}
ENV MONGODB_SERVICE_PORT ${MONGODB_SERVICE_PORT:-"27017"}
ENV MONGODB_MLFLOW_USER ${MONGODB_MLFLOW_USER:-"db_manager_user"}
ENV MONGODB_MLFLOW_PASSWORD ${MONGODB_MLFLOW_PASSWORD:-"db_manager_user_password"}
ENV MONGODB_MLFLOW_DATABASE ${MONGODB_MLFLOW_DATABASE:-"file_storage"}
ENV MONGODB_MLFLOW_PEM_PATH ${MONGODB_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/mongodb_mlflow.pem"}
ENV MONGODB_MLFLOW_CA_PATH ${MONGODB_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/mongodb_mlflow.ca"}
ENV MONGODB_MLFLOW_KEY_PATH ${MONGODB_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/mongodb_mlflow.key"}
ENV MONGODB_MLFLOW_CERT_PATH ${MONGODB_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/mongodb_mlflow.crt"}


ENV MINIO_SERVICE_NAME ${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT ${MINIO_SERVICE_PORT:-"9010"}
# ENV MINIO_MLFLOW_USER ${MINIO_MLFLOW_USER:-"db_manager_user"}
# ENV MINIO_MLFLOW_PASSWORD ${MINIO_MLFLOW_PASSWORD:-"db_manager_user_password"}
# ENV MINIO_MLFLOW_DATABASE ${MINIO_MLFLOW_DATABASE:-"file_storage"}
ENV MINIO_MLFLOW_PEM_PATH ${MINIO_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/minio_mlflow.pem"}
ENV MINIO_MLFLOW_CA_PATH ${MINIO_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/minio_mlflow.ca"}
ENV MINIO_MLFLOW_KEY_PATH ${MINIO_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/minio_mlflow.key"}
ENV MINIO_MLFLOW_CERT_PATH ${MINIO_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/minio_mlflow.crt"}

ENV MLFLOW_MLFLOW_PEM_PATH ${MLFLOW_MLFLOW_PEM_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.pem"}
ENV MLFLOW_MLFLOW_CA_PATH ${MLFLOW_MLFLOW_CA_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.ca"}
ENV MLFLOW_MLFLOW_KEY_PATH ${MLFLOW_MLFLOW_KEY_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.key"}
ENV MLFLOW_MLFLOW_CERT_PATH ${MLFLOW_MLFLOW_CERT_PATH:-"/etc/ssl/mlflow/mlflow_mlflow.crt"}

ENV MLFLOW_HOST=https://$SERVICE_NAME
ENV MLFLOW_USERNAME=${VMLFLOW_USERNAME:-"mlflow-user"}
ENV MLFLOW_PASSWORD=${VMLFLOW_PASSWORD:-"mlflow-password"}

# ENV MLFLOW_INTERNAL_ENDPOINT_URL=/api/internal/
# ENV MLFLOW_PROTECTED_ENDPOINT_URL=/api/protected/


# ENV API_GATEWAY_SERVICE_NAME ${API_GATEWAY_SERVICE_NAME:-"api-gateway"}
# ENV API_GATEWAY_HOST=https://$API_GATEWAY_SERVICE_NAME

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