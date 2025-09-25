FROM redis:7.2-bookworm

# Définir les variables d'environnement pour Redis et Vault
ENV SERVICE_NAME=${SERVICE_NAME:-"redis"}
ENV SERVICE_PORT=${SERVICE_PORT:-"6379"}
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"redis"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"redis"}
ENV VAULT_ROLE=${VAULT_ROLE:-"your-role"}
ENV REPLSET_NAME=${REPLSET_NAME:-"rs0"}
ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
ENV TLS_MODE=${TLS_MODE:-"requireTLS"}
ENV REDIS_ROOT_USER=${REDIS_ROOT_USER:-"redis-user"}
ENV REDIS_ROOT_PASSWORD=${REDIS_ROOT_PASSWORD:-"redis-password"}
ENV REDIS_PEM_PATH=${REDIS_PEM_PATH:-"/etc/ssl/redis/redis.pem"}
ENV REDIS_CA_PATH=${REDIS_CA_PATH:-"/etc/ssl/redis/redis.ca"}
ENV REDIS_KEY_PATH=${REDIS_KEY_PATH:-"/etc/ssl/redis/redis.key"}
ENV REDIS_CERT_PATH=${REDIS_CERT_PATH:-"/etc/ssl/redis/redis.crt"}
ENV REDIS_REDIS_PEM_PATH=${REDIS_REDIS_PEM_PATH:-"/etc/ssl/redis/redis_redis.pem"}
ENV REDIS_REDIS_CA_PATH=${REDIS_REDIS_CA_PATH:-"/etc/ssl/redis/redis_redis.ca"}
# ENV REDIS_MLFLOW_PEM_PATH=${REDIS_MLFLOW_PEM_PATH:-"/etc/ssl/redis/redis_mlflow.pem"}
# ENV REDIS_MLFLOW_CA_PATH=${REDIS_MLFLOW_CA_PATH:-"/etc/ssl/redis/redis_mlflow.ca"}
# ENV REDIS_AIRFLOW_PEM_PATH=${REDIS_AIRFLOW_PEM_PATH:-"/etc/ssl/redis/redis_airflow.pem"}
# ENV REDIS_AIRFLOW_CA_PATH=${REDIS_AIRFLOW_CA_PATH:-"/etc/ssl/redis/redis_airflow.ca"}
ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"redis-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"redis.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/redis/redis.log"}
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

# Ajouter le dépôt HashiCorp et installer Consul et Vault
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y consul vault && \
    rm -rf /var/lib/apt/lists/*

#Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault
# Vérifier les versions installées
RUN consul --version && vault --version

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY redis/init-redis.sh /usr/local/bin/init-redis.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
EXPOSE 6379 80 443

ENTRYPOINT ["entrypoint.sh"]