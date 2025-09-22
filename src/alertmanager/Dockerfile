FROM python:3.12-slim AS hash-generator

RUN pip install --no-cache-dir bcrypt

ENV ALERTMANAGER_ROOT_PASSWORD=${ALERTMANAGER_ROOT_PASSWORD:-"alertmanager-password"}

RUN python3 - <<'EOF'
import bcrypt, os
pw = os.environ["ALERTMANAGER_ROOT_PASSWORD"].encode()
hashed = bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode()
with open("/hashed_password.txt", "w") as f:
    f.write(hashed)
EOF

FROM ubuntu:noble-20250127

WORKDIR /app

# Définir les variables d'environnement pour Alertmanager et Vault
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"alertmanager"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"alertmanager"}
ENV SERVICE_NAME=${SERVICE_NAME:-"alertmanager"}
ENV SERVICE_PORT=${SERVICE_PORT:-"9093"}
ENV ALERTMANAGER_PASSWORD_HASH_FILE="hashed_password.txt"
ENV ALERTMANAGER_ROOT_USER=${ALERTMANAGER_ROOT_USER:-"alertmanager-user"}
ENV ALERTMANAGER_ROOT_PASSWORD=${ALERTMANAGER_ROOT_PASSWORD:-"alertmanager-password"}
# TODO: If the version is changed, the checksum must also be modified in the init script
ENV ALERTMANAGER_VERSION=${ALERTMANAGER_VERSION:-"0.28.1"}
ENV ALERTMANAGER_PEM_PATH=${ALERTMANAGER_PEM_PATH:-"/etc/ssl/alertmanager/alertmanager.pem"}
ENV ALERTMANAGER_CA_PATH=${ALERTMANAGER_CA_PATH:-"/etc/ssl/alertmanager/alertmanager.ca"}
ENV ALERTMANAGER_KEY_PATH=${ALERTMANAGER_KEY_PATH:-"/etc/ssl/alertmanager/alertmanager.key"}
ENV ALERTMANAGER_CERT_PATH=${ALERTMANAGER_CERT_PATH:-"/etc/ssl/alertmanager/alertmanager.crt"}
ENV ALERTMANAGER_RETENTION_TIME=${ALERTMANAGER_RETENTION_TIME:-"1w"}
ENV ALERTMANAGER_RETENTION_SIZE=${ALERTMANAGER_RETENTION_SIZE:-"1GB"}
ENV ALERTMANAGER_ALERTMANAGER_PEM_PATH=${ALERTMANAGER_ALERTMANAGER_PEM_PATH:-"/etc/ssl/alertmanager/alertmanager_alertmanager.pem"}
ENV ALERTMANAGER_ALERTMANAGER_CA_PATH=${ALERTMANAGER_ALERTMANAGER_CA_PATH:-"/etc/ssl/alertmanager/alertmanager_alertmanager.ca"}
ENV ALERTMANAGER_ALERTMANAGER_KEY_PATH=${ALERTMANAGER_ALERTMANAGER_KEY_PATH:-"/etc/ssl/alertmanager/alertmanager_alertmanager.key"}
ENV ALERTMANAGER_ALERTMANAGER_CERT_PATH=${ALERTMANAGER_ALERTMANAGER_CERT_PATH:-"/etc/ssl/alertmanager/alertmanager_alertmanager.crt"}

ENV PROMETHEUS_ALERTMANAGER_PEM_PATH=${PROMETHEUS_ALERTMANAGER_PEM_PATH:-"/etc/ssl/alertmanager/prometheus_alertmanager.pem"}
ENV PROMETHEUS_ALERTMANAGER_CA_PATH=${PROMETHEUS_ALERTMANAGER_CA_PATH:-"/etc/ssl/alertmanager/prometheus_alertmanager.ca"}
ENV PROMETHEUS_ALERTMANAGER_KEY_PATH=${PROMETHEUS_ALERTMANAGER_KEY_PATH:-"/etc/ssl/alertmanager/prometheus_alertmanager.key"}
ENV PROMETHEUS_ALERTMANAGER_CERT_PATH=${PROMETHEUS_ALERTMANAGER_CERT_PATH:-"/etc/ssl/alertmanager/prometheus_alertmanager.crt"}

ENV SLACK_API_URL=${SLACK_API_URL:-"https://hooks.slack.com/services/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"}
ENV SLACK_NOTIFICATION_CHANNEL=${SLACK_NOTIFICATION_CHANNEL:-"avr25-mle-rakuten-alert"}

ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"alertmanager-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"alertmanager.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/alertmanager/alertmanager.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe Alertmanager
RUN groupadd --gid 999 --system alertmanager && \
    useradd --uid 999 --system --gid alertmanager --home-dir /home/alertmanager alertmanager && \
    mkdir -p /home/alertmanager && \
    chown -R alertmanager:alertmanager /home/alertmanager

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
COPY alertmanager/web-config.template.yml web-config.template.yml
COPY alertmanager/alertmanager.template.yml alertmanager.template.yml

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY alertmanager/init-alertmanager.sh /usr/local/bin/init-alertmanager.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
EXPOSE 9093 80 443

# Copy password from other image
COPY --from=hash-generator /hashed_password.txt $ALERTMANAGER_PASSWORD_HASH_FILE
ENTRYPOINT ["entrypoint.sh"]