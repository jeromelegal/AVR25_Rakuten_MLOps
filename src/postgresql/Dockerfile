FROM ubuntu:noble-20250127

# Ajouter l'utilisateur et le groupe PostgreSQL
RUN groupadd --gid 999 --system postgresql && \
    useradd --uid 999 --system --gid postgresql --home-dir /var/lib/postgresql postgresql && \
    mkdir -p /var/lib/postgresql/data && \
    chown -R postgresql:postgresql /var/lib/postgresql/data

# Définir les variables d'environnement pour PostgreSQL et Vault
ENV VAULT_ADDR=${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME=${VAULT_USERNAME:-"postgresql"}
ENV VAULT_PASSWORD=${VAULT_PASSWORD:-"postgresql"}
ENV VAULT_ROLE=${VAULT_ROLE:-"your-role"}
ENV DB_PATH=${DB_PATH:-"/data/postgresql"}
ENV PORT=${PORT:-"5432"}
ENV BIND_IP=${BIND_IP:-"0.0.0.0"}
ENV TLS_MODE=${TLS_MODE:-"require"}
ENV POSTGRESQL_PEM_PATH=${POSTGRESQL_PEM_PATH:-"/etc/ssl/postgresql/postgresql.pem"}
ENV POSTGRESQL_CA_PATH=${POSTGRESQL_CA_PATH:-"/etc/ssl/postgresql/postgresql_ca.crt"}
ENV POSTGRESQL_KEY_PATH=${POSTGRESQL_KEY_PATH:-"/etc/ssl/postgresql/postgresql.key"}
ENV POSTGRESQL_CERT_PATH=${POSTGRESQL_CERT_PATH:-"/etc/ssl/postgresql/postgresql.crt"}
ENV POSTGRESQL_POSTGRESQL_PEM_PATH=${POSTGRESQL_POSTGRESQL_PEM_PATH:-"/etc/ssl/postgresql/postgresql_postgresql.pem"}
ENV POSTGRESQL_POSTGRESQL_KEY_PATH=${POSTGRESQL_POSTGRESQL_KEY_PATH:-"/etc/ssl/postgresql/postgresql_postgresql.key"}
ENV POSTGRESQL_POSTGRESQL_CERT_PATH=${POSTGRESQL_POSTGRESQL_CERT_PATH:-"/etc/ssl/postgresql/postgresql_postgresql.crt"}
ENV POSTGRESQL_POSTGRESQL_CA_PATH=${POSTGRESQL_POSTGRESQL_CA_PATH:-"/etc/ssl/postgresql/postgresql_postgresql_ca.crt"}
ENV POSTGRESQL_API_POSTGRESQL_PEM_PATH=${POSTGRESQL_API_POSTGRESQL_PEM_PATH:-"/etc/ssl/postgresql/postgresql_api-postgresql.pem"}
ENV POSTGRESQL_API_POSTGRESQL_KEY_PATH=${POSTGRESQL_API_POSTGRESQL_KEY_PATH:-"/etc/ssl/postgresql/postgresql_api-postgresql.key"}
ENV POSTGRESQL_API_POSTGRESQL_CERT_PATH=${POSTGRESQL_API_POSTGRESQL_CERT_PATH:-"/etc/ssl/postgresql/postgresql_api-postgresql.crt"}
ENV POSTGRESQL_API_POSTGRESQL_CA_PATH=${POSTGRESQL_API_POSTGRESQL_CA_PATH:-"/etc/ssl/postgresql/postgresql_api-postgresql_ca.crt"}
ENV AUTHORIZATION=${AUTHORIZATION:-"enabled"}
ENV SERVICE_NAME=${SERVICE_NAME:-"postgresql"}
ENV VAULT_SERVICE_NAME=${VAULT_SERVICE_NAME:-"vault"}
ENV VAULT_CERT_FILE=${VAULT_CERT_FILE:-"postgresql-cert.crt"}
ENV VAULT_KEY_FILE=${VAULT_KEY_FILE:-"postgresql.key"}
ENV mTLS=${mTLS:-"false"}
ENV LOG_PATH=${LOG_PATH:-"/var/log/postgresql/postgresql.log"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

ENV MLFLOW_DATABASE=${MLFLOW_DATABASE:-"mlflow"}
ENV MLFLOW_USER=${MLFLOW_USER:-"mlflow_user"}
ENV MLFLOW_USER_PASSWORD=${MLFLOW_USER_PASSWORD:-"mlflow_user_password"}
ENV POSTGRESQL_MLFLOW_PEM_PATH=${POSTGRESQL_MLFLOW_PEM_PATH:-"/etc/ssl/postgresql/postgresql_mlflow.pem"}
ENV POSTGRESQL_MLFLOW_KEY_PATH=${POSTGRESQL_MLFLOW_KEY_PATH:-"/etc/ssl/postgresql/postgresql_mlflow.key"}
ENV POSTGRESQL_MLFLOW_CERT_PATH=${POSTGRESQL_MLFLOW_CERT_PATH:-"/etc/ssl/postgresql/postgresql_mlflow.crt"}
ENV POSTGRESQL_MLFLOW_CA_PATH=${POSTGRESQL_MLFLOW_CA_PATH:-"/etc/ssl/postgresql/postgresql_mlflow_ca.crt"}
ENV AIRFLOW_DATABASE=${AIRFLOW_DATABASE:-"airflow"}
ENV AIRFLOW_SCHEMA=${AIRFLOW_SCHEMA:-"airflow_schema"}
ENV AIRFLOW_USER=${AIRFLOW_USER:-"airflow_user"}
ENV AIRFLOW_USER_PASSWORD=${AIRFLOW_USER_PASSWORD:-"airflow_user_password"}

RUN mkdir -p $DB_PATH
RUN chown -R postgresql:postgresql $DB_PATH
RUN chmod 750 $DB_PATH

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


# Importer la clé de signature du dépôt PostgreSQL
RUN install -d /usr/share/postgresql-common/pgdg
RUN curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc

# Créer le fichier de configuration du dépôt
RUN . /etc/os-release && \
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $VERSION_CODENAME-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Mettre à jour les listes de paquets
RUN apt-get update

# Installer PostgreSQL
RUN apt-get install -y postgresql postgresql-client

# Ajouter le chemin de l'exécutable postgres à la variable PATH
ENV PATH="/usr/lib/postgresql/17/bin:${PATH}"

RUN postgres --version 

# Ajouter le dépôt HashiCorp et installer Consul et Vault
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y consul vault && \
    rm -rf /var/lib/apt/lists/*

# Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault

# Vérifier les versions installées
RUN consul --version && vault --version

# Copier les scripts et les fichiers de configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY postgresql/init-postgresql.sql /usr/local/bin/init-postgresql.sql
COPY postgresql/init-postgresql-mlflow.sql /usr/local/bin/init-postgresql-mlflow.sql
COPY postgresql/init-postgresql-airflow.sql /usr/local/bin/init-postgresql-airflow.sql
COPY postgresql/init-postgresql.sh /usr/local/bin/init-postgresql.sh
COPY postgresql/init-categories.sql /usr/local/bin/init-categories.sql
COPY postgresql/generate-config.sh /usr/local/bin/generate-config.sh
COPY nginx/health-check.sh /usr/local/bin/health-check.sh
COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
COPY vault/vault.sh /usr/local/bin/vault.sh

# Rendre les scripts exécutables
RUN chmod +x /usr/local/bin/*.sh

#USER postgresql
# Volume
VOLUME ["/data/postgresql"]

# Définir le point d'entrée et exposer le port
ENTRYPOINT ["entrypoint.sh"]
EXPOSE 5432
