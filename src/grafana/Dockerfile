FROM ubuntu:noble-20250127

WORKDIR /app

# Définir les variables d'environnement pour Grafana et Vault
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"grafana"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"grafana"}
ENV SERVICE_NAME=${SERVICE_NAME:-"grafana"}
ENV SERVICE_PORT=${SERVICE_PORT:-"3030"}
ENV GRAFANA_ROOT_USER=${GRAFANA_ROOT_USER:-"grafana-user"}
ENV GRAFANA_ROOT_PASSWORD=${GRAFANA_ROOT_PASSWORD:-"grafana-password"}
ENV GF_DEFAULT_INSTANCE_NAME=${SERVICE_NAME}
ENV GF_SECURITY_ADMIN_USER=${GRAFANA_ROOT_USER}
ENV GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ROOT_PASSWORD}
ENV GRAFANA_PEM_PATH=${GRAFANA_PEM_PATH:-"/etc/ssl/grafana/grafana.pem"}
ENV GRAFANA_CA_PATH=${GRAFANA_CA_PATH:-"/etc/ssl/grafana/grafana.ca"}
ENV GRAFANA_KEY_PATH=${GRAFANA_KEY_PATH:-"/etc/ssl/grafana/grafana.key"}
ENV GRAFANA_CERT_PATH=${GRAFANA_CERT_PATH:-"/etc/ssl/grafana/grafana.crt"}
ENV GRAFANA_RETENTION_TIME=${GRAFANA_RETENTION_TIME:-"1w"}
ENV GRAFANA_RETENTION_SIZE=${GRAFANA_RETENTION_SIZE:-"1GB"}
ENV GRAFANA_GRAFANA_PEM_PATH=${GRAFANA_GRAFANA_PEM_PATH:-"/etc/ssl/grafana/grafana_grafana.pem"}
ENV GRAFANA_GRAFANA_CA_PATH=${GRAFANA_GRAFANA_CA_PATH:-"/etc/ssl/grafana/grafana_grafana.ca"}
ENV GRAFANA_GRAFANA_KEY_PATH=${GRAFANA_GRAFANA_KEY_PATH:-"/etc/ssl/grafana/grafana_grafana.key"}
ENV GRAFANA_GRAFANA_CERT_PATH=${GRAFANA_GRAFANA_CERT_PATH:-"/etc/ssl/grafana/grafana_grafana.crt"}
ENV PROMETHEUS_GRAFANA_PEM_PATH=${PROMETHEUS_GRAFANA_PEM_PATH:-"/etc/ssl/grafana/prometheus_grafana.pem"}
ENV PROMETHEUS_GRAFANA_CA_PATH=${PROMETHEUS_GRAFANA_CA_PATH:-"/etc/ssl/grafana/prometheus_grafana.ca"}
ENV PROMETHEUS_GRAFANA_KEY_PATH=${PROMETHEUS_GRAFANA_KEY_PATH:-"/etc/ssl/grafana/prometheus_grafana.key"}
ENV PROMETHEUS_GRAFANA_CERT_PATH=${PROMETHEUS_GRAFANA_CERT_PATH:-"/etc/ssl/grafana/prometheus_grafana.crt"}

ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"grafana-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"grafana.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/grafana/grafana.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

# Ajouter l'utilisateur et le groupe Grafana
RUN groupadd --gid 999 --system grafana && \
    useradd --uid 999 --system --gid grafana --home-dir /home/grafana grafana && \
    mkdir -p /home/grafana && \
    chown -R grafana:grafana /home/grafana

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
coreutils \
nginx && \
rm -rf /var/lib/apt/lists/*

# Ajouter le dépôt HashiCorp et installer Consul et Vault
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
apt-get update && apt-get install -y consul vault && \
rm -rf /var/lib/apt/lists/*

# Install Grafana (see https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/)
RUN apt-get update && apt-get install -y apt-transport-https software-properties-common wget && \
    mkdir -p /etc/apt/keyrings/ && \
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null && \
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee -a /etc/apt/sources.list.d/grafana.list && \
    apt-get update && \
    apt-get install -y grafana

#Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault
# Vérifier les versions installées
RUN consul --version && vault --version

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY grafana/init-grafana.sh /usr/local/bin/init-grafana.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
EXPOSE 3030 80 443

ENTRYPOINT ["entrypoint.sh"]