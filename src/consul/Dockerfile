# Utiliser la dernière image Consul comme base
FROM ubuntu:noble-20250127

ENV TF_LOG ${TF_LOG:-"DEBUG"}

# Variables
ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME ${VAULT_USERNAME:-"consul"}
ENV VAULT_PASSWORD ${VAULT_PASSWORD:-"consul"}

ENV VAULT_TLS_DIR ${VAULT_TLS_DIR:-"tls/vault/server"}
ENV VAULT_CA_CERT_FILE ${VAULT_CA_CERT_FILE:-"$VAULT_TLS_DIR/vault_ca.crt"}
ENV VAULT_CERT_FILE ${VAULT_CERT_FILE:-"$VAULT_TLS_DIR/server.crt"}
ENV VAULT_SKIP_VERIFY ${VAULT_SKIP_VERIFY:-"0"}
ENV VAULT_CONFIG_DIR ${VAULT_CONFIG_DIR:-"/config/vault/server"}
ENV VAULT_CONFIG_FILE ${VAULT_CONFIG_FILE:-"$VAULT_CONFIG_DIR/vault.hcl"}

#consul server
ENV CONSUL_BACKEND=${CONSUL_BACKEND:-"true"}
ENV CONSUL_SERVER_HOST=${CONSUL_SERVER_HOST:-"consul"}
ENV CONSUL_SERVER_PORT=${CONSUL_SERVER_PORT:-"8501"}
ENV CONSUL_CONFIG_DIR="/consul/server/config"
ENV CONSUL_CONFIG_FILE="$CONSUL_CONFIG_DIR/consul.hcl"

ENV CONSUL_TLS_DIR ${CONSUL_TLS_DIR:-"/etc/ssl/consul/server"}
ENV CONSUL_CA_CN ${CONSUL_CA_CN:-"Consul Server CA"}
ENV CONSUL_CA_CERT_FILE ${CONSUL_CA_CERT_FILE:-"$CONSUL_TLS_DIR/consul_ca.crt"}
ENV CONSUL_CA_KEY_FILE ${CONSUL_CA_KEY_FILE:-"$CONSUL_TLS_DIR/consul_ca.key"}
ENV CONSUL_CERT_CN ${CONSUL_CERT_CN:-"vault.example.com"}
ENV CONSUL_CERT_FILE ${CONSUL_CERT_FILE:-"$CONSUL_TLS_DIR/server.crt"}
ENV CONSUL_REQ_FILE ${CONSUL_REQ_FILE:-"$CONSUL_TLS_DIR/server.csr"}
ENV CONSUL_KEY_FILE ${CONSUL_KEY_FILE:-"$CONSUL_TLS_DIR/server.key"}
ENV CONSUL_SKIP_VERIFY ${CONSUL_SKIP_VERIFY:-"0"}
ENV CONSUL_DATA_DIR ${CONSUL_DATA_DIR:-"/var/consul"}
ENV CONSUL_VAULT_INIT_SECRET ${CONSUL_VAULT_INIT_SECRET:-"secret/consul/vault/initialize"}


ENV SERVICE_NAME ${SERVICE_NAME:-"consul"}
ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV NGINX_STATUS_FILE="/var/log/status"
ENV NGINX_CONTENT_FILE="/var/log/content"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"

ENV INITIALIZED ${INITIALIZED:-"false"}



# Répertoire pour stocker les certificats TLS
RUN mkdir -p $VAULT_TLS_DIR
RUN mkdir -p $VAULT_CONFIG_DIR
RUN mkdir -p $CONSUL_TLS_DIR



# Mettre à jour la liste des paquets et installer wget, gpg 
RUN apt-get update && apt-get install -y wget gpg lsb-release curl jq iproute2 nginx fcgiwrap

# Télécharger la clé GPG de HashiCorp et l'ajouter au keyring
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Ajouter le dépôt HashiCorp à la liste des sources
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

# Mettre à jour la liste des paquets et installer Consul
RUN apt update && apt install -y consul

RUN consul --version

# Mettre à jour la liste des paquets et installer Vault
RUN apt-get update && apt-get install -y vault

#Retirer le verrouillage de la mémoire
RUN setcap -r /usr/bin/vault

RUN vault --version


COPY . . 


RUN mv vault/vault.sh /usr/local/bin/vault.sh
RUN chmod +x /usr/local/bin/vault.sh

RUN mv consul/consul.sh /usr/local/bin/consul.sh 
RUN chmod +x /usr/local/bin/consul.sh

RUN mv entrypoint.sh /usr/local/bin/entrypoint.sh 
RUN chmod +x /usr/local/bin/entrypoint.sh


RUN mv nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh

RUN mv nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

RUN mv nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh



EXPOSE 8600/udp 8501 80 443

ENTRYPOINT ["entrypoint.sh"]

# Définir la commande pour démarrer Consul
#CMD ["consul" "agent "]


