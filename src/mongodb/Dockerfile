FROM ubuntu:noble-20250127

# Ajouter l'utilisateur et le groupe MongoDB
RUN groupadd --gid 999 --system mongodb && \
    useradd --uid 999 --system --gid mongodb --home-dir /data/db mongodb && \
    mkdir -p /data/db /data/configdb && \
    chown -R mongodb:mongodb /data/db /data/configdb

# Définir les arguments et variables d'environnement
ARG MONGO_PACKAGE=mongodb-org
ARG MONGO_REPO=repo.mongodb.org
ENV MONGO_PACKAGE=${MONGO_PACKAGE}
ENV MONGO_REPO=${MONGO_REPO}
ENV MONGO_MAJOR=8.0
ENV MONGO_VERSION=8.0.8

# Définir les variables d'environnement pour MongoDB et Vault
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"mongodb"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"mongodb"}
ENV VAULT_ROLE=${VAULT_ROLE:-"your-role"}
ENV DB_PATH=${DB_PATH:-"/data/db"}
ENV REPLSET_NAME=${REPLSET_NAME:-"rs0"}
ENV PORT=${PORT:-"27017"}
ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
ENV TLS_MODE=${TLS_MODE:-"requireTLS"}
ENV MONGODB_PEM_PATH=${MONGODB_PEM_PATH:-"/etc/ssl/mongodb/mongodb.pem"}
ENV MONGODB_CA_PATH=${MONGODB_CA_PATH:-"/etc/ssl/mongodb/mongodb.ca"}
ENV MONGODB_KEY_PATH=${MONGODB_KEY_PATH:-"/etc/ssl/mongodb/mongodb.key"}
ENV MONGODB_CERT_PATH=${MONGODB_CERT_PATH:-"/etc/ssl/mongodb/mongodb.crt"}
ENV MONGODB_MONGODB_PEM_PATH=${MONGODB_MONGODB_PEM_PATH:-"/etc/ssl/mongodb/mongodb_mongodb.pem"}
ENV MONGODB_MONGODB_CA_PATH=${MONGODB_MONGODB_CA_PATH:-"/etc/ssl/mongodb/mongodb_mongodb.ca"}
ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV SERVICE_NAME=${SERVICE_NAME:-"mongodb"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"mongodb-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"mongodb.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/mongodb/mongod.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Mettre à jour les paquets et installer les dépendances
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    lsb-release \
    curl \
    jq \
    cron \
    ca-certificates \
    fcgiwrap \
	libcap2-bin \
    nginx && \
    rm -rf /var/lib/apt/lists/*

# Importer la clé publique et ajouter le dépôt MongoDB
RUN wget -qO - https://www.mongodb.org/static/pgp/server-8.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/8.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list

# Installer MongoDB
RUN set -x && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y \
        ${MONGO_PACKAGE}=$MONGO_VERSION \
        ${MONGO_PACKAGE}-server=$MONGO_VERSION \
        ${MONGO_PACKAGE}-shell=$MONGO_VERSION \
        ${MONGO_PACKAGE}-mongos=$MONGO_VERSION \
        ${MONGO_PACKAGE}-tools=$MONGO_VERSION \
        ${MONGO_PACKAGE}-database=$MONGO_VERSION \
        ${MONGO_PACKAGE}-database-tools-extra=$MONGO_VERSION && \
    rm -rf /var/lib/apt/lists/* /var/lib/mongodb && \
    mv /etc/mongod.conf /etc/mongod.conf.orig

# Ajouter le dépôt HashiCorp et installer Consul et Vault
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y consul vault && \
    rm -rf /var/lib/apt/lists/*

#Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault
# Vérifier les versions installées
RUN consul --version && vault --version

RUN ls -lah

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY mongodb/init-mongodb.sh /usr/local/bin/init-mongodb.sh
#COPY mongodb/init-mongo-replicatset.js /usr/local/bin/init-mongo-replicatset.js
COPY mongodb/init-mongodb.js /usr/local/bin/init-mongodb.js
COPY mongodb/generate-config.sh /usr/local/bin/generate-config.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh


# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
ENTRYPOINT ["entrypoint.sh"]
EXPOSE 27017
#CMD ["mongod"]
VOLUME ["/data/db"]