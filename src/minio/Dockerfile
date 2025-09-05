FROM ubuntu:noble-20250127 AS builder

ARG CPU_ARCH=${CPU_ARCH:-"amd64"}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git make gcc wget ca-certificates golang-go && \
    apt install --reinstall -y build-essential && \
    rm -rf /var/lib/apt/lists/*

ENV GOPATH=/go
ENV PATH=$GOPATH/bin:/usr/local/go/bin:$PATH
WORKDIR $GOPATH/src/minio

# Compile Minio server
RUN go install github.com/minio/minio@latest && \
    cp $GOPATH/bin/minio /usr/local/bin

# Compile Minio client
RUN go install github.com/minio/mc@latest && \
    cp $GOPATH/bin/mc /usr/local/bin

# ----------

FROM ubuntu:noble-20250127

# Ajouter l'utilisateur et le groupe Minio
RUN groupadd --gid 999 --system minio && \
    useradd --uid 999 --system --gid minio --home-dir /home/minio minio

# Définir les variables d'environnement pour Minio et Vault
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"minio"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"minio"}
ENV VAULT_ROLE=${VAULT_ROLE:-"your-role"}
ENV REPLSET_NAME=${REPLSET_NAME:-"rs0"}
ENV PORT=${PORT:-"9010"}
ENV GUI_PORT=${GUI_PORT:-"9011"}
ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
ENV TLS_MODE=${TLS_MODE:-"requireTLS"}
ENV MINIO_ROOT_USER=${MINIO_ROOT_USER:-"minio-user"}
ENV MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-"minio-password"}
ENV MINIO_PEM_PATH=${MINIO_PEM_PATH:-"/etc/ssl/minio/minio.pem"}
ENV MINIO_CA_PATH=${MINIO_CA_PATH:-"/etc/ssl/minio/minio.ca"}
ENV MINIO_KEY_PATH=${MINIO_KEY_PATH:-"/etc/ssl/minio/minio.key"}
ENV MINIO_CERT_PATH=${MINIO_CERT_PATH:-"/etc/ssl/minio/minio.crt"}
ENV MINIO_MINIO_PEM_PATH=${MINIO_MINIO_PEM_PATH:-"/etc/ssl/minio/minio_minio.pem"}
ENV MINIO_MINIO_CA_PATH=${MINIO_MINIO_CA_PATH:-"/etc/ssl/minio/minio_minio.ca"}
ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV SERVICE_NAME=${SERVICE_NAME:-"minio"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"minio-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"minio.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/minio/minio.log"}
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

# Copy binary of Minio from builder image
COPY --from=builder /usr/local/bin/minio /usr/local/bin/minio
COPY --from=builder /usr/local/bin/mc /usr/local/bin/mc

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
COPY minio/init-minio.sh /usr/local/bin/init-minio.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

# Définir le point d'entrée et exposer le port
EXPOSE 9010 9011

ENTRYPOINT ["entrypoint.sh"]