FROM ubuntu:noble-20250127

ENV TF_LOG ${TF_LOG:-"DEBUG"}

# Variables
ENV VAULT_ADDR ${VAULT_ADDR:-"https://vault:8200"}
ENV VAULT_USERNAME ${VAULT_USERNAME:-"vault"}
ENV VAULT_PASSWORD ${VAULT_PASSWORD:-"vault"}

ENV VAULT_ROOT_CA_CN ${VAULT_ROOT_CA_CN:-"Root Server CA"}
ENV VAULT_ROOT_CA_CERT_FILE=${VAULT_ROOT_CA_CERT_FILE:-"$VAULT_TLS_DIR/root_ca.crt"}
ENV VAULT_ROOT_CA_KEY_FILE=${VAULT_ROOT_CA_KEY_FILE:-"$VAULT_TLS_DIR/root_ca.key"}

ENV VAULT_TLS_DIR ${VAULT_TLS_DIR:-"tls/vault/server"}
ENV VAULT_CA_CN ${VAULT_CA_CN:-"Vault Server CA"}
ENV VAULT_CA_CERT_FILE ${VAULT_CA_CERT_FILE:-"$VAULT_TLS_DIR/vault_ca.crt"}
ENV VAULT_CA_KEY_FILE ${VAULT_CA_KEY_FILE:-"$VAULT_TLS_DIR/vault_ca.key"}
ENV VAULT_CERT_CN ${VAULT_CERT_CN:-"vault.example.com"}
ENV VAULT_CERT_FILE ${VAULT_CERT_FILE:-"$VAULT_TLS_DIR/server.crt"}
ENV VAULT_REQ_FILE ${VAULT_REQ_FILE:-"$VAULT_TLS_DIR/server.csr"}
ENV VAULT_KEY_FILE ${VAULT_KEY_FILE:-"$VAULT_TLS_DIR/server.key"}
ENV VAULT_SKIP_VERIFY ${VAULT_SKIP_VERIFY:-"0"}
ENV VAULT_CONFIG_DIR ${VAULT_CONFIG_DIR:-"/config/vault/server"}
ENV VAULT_CONFIG_FILE ${VAULT_CONFIG_FILE:-"$VAULT_CONFIG_DIR/vault.hcl"}
ENV SECURED_SERVICES ${SECURED_SERVICES:-"vault,consul,mongodb,api-mongodb,postgresql,api-postgresql,api-gateway,frontend,reverse-proxy,zookeeper,kafka,minio,api-minio,mlflow,model-downloader,api-text-processing,api-image-processing,api-processing,prometheus,grafana,alertmanager"}

ENV VAULT_LOCAL_DATA ${VAULT_LOCAL_DATA:-"/vault/data"} 


ENV AUTO_UNSEAL_PID=0



ENV UNSEAL_KEYS ${UNSEAL_KEYS:-""}

#consul server
ENV CONSUL_BACKEND=${CONSUL_BACKEND:-"true"}
ENV CONSUL_SERVER_HOST=${CONSUL_SERVER_HOST:-"consul"}
ENV CONSUL_SERVER_PORT=${CONSUL_SERVER_PORT:-"8501"}

ENV SSL_CERT_FILE=${SSL_CERT_FILE:-"/etc/ssl/certs/ca-certificates.crt"}

ENV CONSUL_VAULT_INIT_SECRET ${CONSUL_VAULT_INIT_SECRET:-"secret/consul/vault/initialize"}

ENV INITIALIZED ${INITIALIZED:-"false"}


ENV NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
ENV HEALTH_CHECK_FILE="/usr/local/bin/health-check.sh"



WORKDIR /app

# Répertoire pour stocker les certificats TLS
RUN mkdir -p 'bin'
RUN mkdir -p $VAULT_TLS_DIR
RUN mkdir -p $VAULT_CONFIG_DIR

# Mettre à jour la liste des paquets et installer wget, gpg et lsb-release
RUN apt-get update && apt-get install -y wget gpg lsb-release curl iptables jq openssl libcap2-bin iproute2 ca-certificates nginx fcgiwrap

# Installez les dépendances nécessaires pour nfqueue
RUN apt install -y python3 python3-pip python3-dev libnetfilter-queue-dev build-essential
RUN python3 -m pip install --no-cache-dir --break-system-packages scapy NetfilterQueue requests

# Télécharger la clé GPG de HashiCorp et l'ajouter au keyring
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Ajouter le dépôt HashiCorp à la liste des sources
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

# Mettre à jour la liste des paquets et installer Vault
RUN apt-get update && apt-get install -y vault

RUN setcap -r /usr/bin/vault

COPY . .

COPY auto-unseal/auto-unseal.py /usr/local/bin/auto-unseal.py


RUN apt-get install -y tcpdump


COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY vault/init.sh /usr/local/bin/init.sh
RUN chmod +x /usr/local/bin/init.sh

COPY consul/consul.sh /usr/local/bin/consul.sh
RUN chmod +x /usr/local/bin/consul.sh

COPY vault/vault.sh /usr/local/bin/vault.sh
RUN chmod +x /usr/local/bin/vault.sh

COPY nginx/nginx-fcgiwrap.sh /usr/local/bin/nginx-fcgiwrap.sh
RUN chmod +x /usr/local/bin/nginx-fcgiwrap.sh
# sudo apt-get install fcgiwrap
# sudo systemctl enable fcgiwrap
# sudo systemctl start fcgiwrap




COPY nginx/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

COPY nginx/nginx-conf.sh /usr/local/bin/nginx-conf.sh
RUN chmod +x /usr/local/bin/nginx-conf.sh

# Exposer le port Vault
EXPOSE 8200 8201 8501 80 443

# Commande pour démarrer Vault
ENTRYPOINT  ["entrypoint.sh"]
