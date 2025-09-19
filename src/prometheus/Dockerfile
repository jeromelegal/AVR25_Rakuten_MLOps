FROM python:3.12-slim AS hash-generator

RUN pip install --no-cache-dir bcrypt

ENV PROMETHEUS_ROOT_PASSWORD=${PROMETHEUS_ROOT_PASSWORD:-"prometheus-password"}

RUN python3 - <<'EOF'
import bcrypt, os
pw = os.environ["PROMETHEUS_ROOT_PASSWORD"].encode()
hashed = bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode()
with open("/hashed_password.txt", "w") as f:
    f.write(hashed)
EOF

FROM ubuntu:noble-20250127

WORKDIR /app

# Définir les variables d'environnement pour Prometheus et Vault
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"prometheus"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"prometheus"}
ENV SERVICE_NAME=${SERVICE_NAME:-"prometheus"}
ENV SERVICE_PORT=${SERVICE_PORT:-"9090"}
ENV PROMETHEUS_PASSWORD_HASH_FILE="hashed_password.txt"
ENV PROMETHEUS_ROOT_USER=${PROMETHEUS_ROOT_USER:-"prometheus-user"}
ENV PROMETHEUS_ROOT_PASSWORD=${PROMETHEUS_ROOT_PASSWORD:-"prometheus-password"}
# TODO: If the version is changed, the checksum must also be modified in the init script
ENV PROMETHEUS_VERSION=${PROMETHEUS_VERSION:-"3.5.0"}
ENV PROMETHEUS_PEM_PATH=${PROMETHEUS_PEM_PATH:-"/etc/ssl/prometheus/prometheus.pem"}
ENV PROMETHEUS_CA_PATH=${PROMETHEUS_CA_PATH:-"/etc/ssl/prometheus/prometheus.ca"}
ENV PROMETHEUS_KEY_PATH=${PROMETHEUS_KEY_PATH:-"/etc/ssl/prometheus/prometheus.key"}
ENV PROMETHEUS_CERT_PATH=${PROMETHEUS_CERT_PATH:-"/etc/ssl/prometheus/prometheus.crt"}
ENV PROMETHEUS_RETENTION_TIME=${PROMETHEUS_RETENTION_TIME:-"1w"}
ENV PROMETHEUS_RETENTION_SIZE=${PROMETHEUS_RETENTION_SIZE:-"1GB"}
ENV PROMETHEUS_PROMETHEUS_PEM_PATH=${PROMETHEUS_PROMETHEUS_PEM_PATH:-"/etc/ssl/prometheus/prometheus_prometheus.pem"}
ENV PROMETHEUS_PROMETHEUS_CA_PATH=${PROMETHEUS_PROMETHEUS_CA_PATH:-"/etc/ssl/prometheus/prometheus_prometheus.ca"}
ENV PROMETHEUS_PROMETHEUS_KEY_PATH=${PROMETHEUS_PROMETHEUS_KEY_PATH:-"/etc/ssl/prometheus/prometheus_prometheus.key"}
ENV PROMETHEUS_PROMETHEUS_CERT_PATH=${PROMETHEUS_PROMETHEUS_CERT_PATH:-"/etc/ssl/prometheus/prometheus_prometheus.crt"}

ENV MINIO_SERVICE_NAME=${MINIO_SERVICE_NAME:-"minio"}
ENV MINIO_SERVICE_PORT=${MINIO_SERVICE_PORT:-"9010"}
ENV MINIO_PROMETHEUS_PEM_PATH=${MINIO_PROMETHEUS_PEM_PATH:-"/etc/ssl/prometheus/minio_prometheus.pem"}
ENV MINIO_PROMETHEUS_CA_PATH=${MINIO_PROMETHEUS_CA_PATH:-"/etc/ssl/prometheus/minio_prometheus.ca"}
ENV MINIO_PROMETHEUS_KEY_PATH=${MINIO_PROMETHEUS_KEY_PATH:-"/etc/ssl/prometheus/minio_prometheus.key"}
ENV MINIO_PROMETHEUS_CERT_PATH=${MINIO_PROMETHEUS_CERT_PATH:-"/etc/ssl/prometheus/minio_prometheus.crt"}

ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"prometheus-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"prometheus.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/prometheus/prometheus.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe Prometheus
RUN groupadd --gid 999 --system prometheus && \
    useradd --uid 999 --system --gid prometheus --home-dir /home/prometheus prometheus && \
    mkdir -p /home/prometheus && \
    chown -R prometheus:prometheus /home/prometheus

# Mettre à jour les paquets et installer les dépendances
RUN apt-get update && apt-get install -y \
gcc \
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

# Copy configuration template
COPY prometheus/web-config.template.yml web-config.template.yml
COPY prometheus/prometheus.template.yml prometheus.template.yml

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY prometheus/init-prometheus.sh /usr/local/bin/init-prometheus.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
EXPOSE 9090 80 443

# Copy password from other image
COPY --from=hash-generator /hashed_password.txt $PROMETHEUS_PASSWORD_HASH_FILE
ENTRYPOINT ["entrypoint.sh"]