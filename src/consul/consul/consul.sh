#!/bin/bash

# Variables
CA_FILE="/usr/local/share/ca-certificates/consul_ca.crt"

# Variable pour le token Vault
VAULT_TOKEN=""

# Fonction pour se connecter à Vault
vault_login() {
  vault login -method=userpass username=$VAULT_USERNAME password=$VAULT_PASSWORD > /dev/null
}

# Fonction pour créer la politique ACL pour Vault
create_vault_policy() {
  # Politique pour accorder l'accès à Vault
VAULT_POLICY=$(cat <<EOF
key_prefix "vault/" {
  policy = "write"
}
key "vault/core/migration" {
  policy = "read"
}
service "vault" {
  policy = "write"
}
session_prefix "" {
  policy = "write"
}
key_prefix "service/leader" {
  policy = "write"
}
EOF
)

  # Créer la politique si elle n'existe pas déjà
  if ! consul acl policy read -name "vault-policy" -token=$CONSUL_ACL_TOKEN > /dev/null 2>&1; then
    echo "Création de la politique vault-policy..."
    consul acl policy create -name "vault-policy" -rules "$VAULT_POLICY" -token=$CONSUL_ACL_TOKEN
  fi
}

# Fonction pour générer le token ACL pour Vault
generate_vault_token() {
  # Vérifier si le token Vault existe déjà
  if vault kv get -field=vault_token secret/consul/tokens > /dev/null 2>&1; then
    VAULT_TOKEN=$(vault kv get -field=vault_token secret/consul/tokens)
  else
    VAULT_TOKEN=$(consul acl token create -description "Vault Token" -policy-name "vault-policy" -token=$CONSUL_ACL_TOKEN -format=json | jq -r '.SecretID')
    vault kv put secret/consul/vault/tokens vault_token=$VAULT_TOKEN
  fi

}



# Fonction pour créer le fichier de configuration Consul avec ACL mais sans tokens
create_consul_config_file_with_acl_no_tokens() {
cat <<EOF > $CONSUL_CONFIG_FILE
server = true
bootstrap_expect = 1
datacenter = "dc1"
data_dir = "$CONSUL_DATA_DIR"
bind_addr = "{{ GetInterfaceIP \"eth0\" }}"
client_addr = "0.0.0.0"
ui = true
ports {
  http = 8500
  https = 8501
  grpc_tls = 8502
}
acl {
  enabled = true
  default_policy = "deny"
  down_policy = "extend-cache"
  enable_token_persistence = true
}
connect {
  enabled = true
}
tls {
  defaults {
    ca_file = "$CA_FILE"
    cert_file = "$CONSUL_CERT_FILE"
    key_file = "$CONSUL_KEY_FILE"
    verify_incoming = true
    verify_outgoing = true
  }
  internal_rpc {
    verify_server_hostname = true
  }
}
performance {
  raft_multiplier = 1
}
EOF
  echo "Consul configuration file created at $CONSUL_CONFIG_FILE with ACL but no tokens"
}


# Fonction pour vérifier si le cluster est déjà initialisé
is_cluster_initialized() {
  if vault kv get -field=status $CONSUL_VAULT_INIT_SECRET | grep -q "initialized"; then
    return 0
  else
    return 1
  fi
}

# Fonction pour marquer le cluster comme en cours d'initialisation
mark_cluster_initializing() {
  vault kv put $CONSUL_VAULT_INIT_SECRET status="initializing"
}

# Fonction pour marquer le cluster comme initialisé
mark_cluster_initialized() {
  vault kv put $CONSUL_VAULT_INIT_SECRET status="initialized"
}

# Fonction pour initialiser le cluster avec ACL mais sans tokens
initialize_cluster_with_acl_no_tokens() {
  echo "Initializing Consul cluster with ACL but no tokens..."
  consul agent -config-file=$CONSUL_CONFIG_FILE  &
  export CONSUL_PID=$!
  CONSUL_ADDR="https://$CONSUL_SERVER_HOST:$CONSUL_SERVER_PORT" 
  # until curl -s --cert $CONSUL_CERT_FILE --key $CONSUL_KEY_FILE  $CONSUL_ADDR/v1/status/leader > /dev/null; do
  until curl -s --cert $CONSUL_CERT_FILE --key $CONSUL_KEY_FILE  $CONSUL_ADDR/v1/status/leader; do
    echo "Waiting for Consul to be ready... "
    sleep 1
  done
  CONSUL_ACL_TOKEN=$(consul acl bootstrap -format=json | jq -r '.SecretID')
  echo "Consul cluster initialized with ACL but no tokens."
}

# Fonction pour initialiser le cluster avec ACL et tokens
stop_cluster() {
   if [ -z "$CONSUL_PID" ]; then
    echo "Aucun processus Consul trouvé avec la configuration actuelle."
  else
    # Arrêter le processus Consul
    kill $CONSUL_PID
    # Vérifier si le processus a été arrêté correctement
    until ! ps -p $CONSUL_PID > /dev/null; do
      echo "Le processus Consul est en cours d'arrêt."
      sleep 1
    done
    echo "Le processus Consul a été arrêté avec succès."
  fi

  echo "Consul cluster initialized with ACL and tokens."
}

# Vérifier si le répertoire de données existe
if [ ! -d "$CONSUL_CONFIG_DIR" ]; then
  mkdir -p $CONSUL_CONFIG_DIR
fi

vault_login
# Vérifier si le cluster est déjà initialisé
if ! is_cluster_initialized; then
  mark_cluster_initializing
fi
create_consul_config_file_with_acl_no_tokens
initialize_cluster_with_acl_no_tokens




# Définir la politique pour le nœud maître
MASTER_NODE_POLICY=$(cat <<EOF
key "" {
  policy = "write"
}
service "" {
  policy = "write"
}
node "" {
  policy = "write"
}
node_prefix "" {
  policy = "write"
}
operator = "write"
EOF
)

# Créer la politique si elle n'existe pas déjà
if ! consul acl policy read -name "master-node-policy" -token=$CONSUL_ACL_TOKEN  > /dev/null 2>&1; then
  echo "Création de la politique master-node-policy..."
  consul acl policy create -name "master-node-policy" -rules "$MASTER_NODE_POLICY" -token=$CONSUL_ACL_TOKEN 
  if [ $? -ne 0 ]; then
    echo "Échec de la création de la politique master-node-policy"
    exit 1
  fi
else
  echo "La politique master-node-policy existe déjà."
fi


# Vérifier si le token maître existe déjà
if consul acl token read -name "master-node-token" -token=$CONSUL_ACL_TOKEN  > /dev/null 2>&1; then
  MASTER_NODE_TOKEN=$(consul acl token read -name "master-node-token" -field "SecretID" -token=$CONSUL_ACL_TOKEN )
else
  # Créer un nouveau token avec la politique master-node-policy
  MASTER_NODE_TOKEN=$(consul acl token create -description "Master Node Token" -policy-name "master-node-policy" -token=$CONSUL_ACL_TOKEN  -format=json | jq -r '.SecretID')
  if [ $? -ne 0 ]; then
    echo "Échec de la création du token master-node-token"
    exit 1
  fi
fi


cat <<EOF > $CONSUL_CONFIG_FILE
server = true
bootstrap_expect = 1
datacenter = "dc1"
data_dir = "$CONSUL_DATA_DIR"
bind_addr = "{{ GetInterfaceIP \"eth0\" }}"
client_addr = "0.0.0.0"
ui = true
ports {
  http = 8500
  https = 8501
  grpc_tls = 8502
}
acl {
  enabled = true
  default_policy = "deny"
  down_policy = "extend-cache"
  enable_token_persistence = true
  tokens {
    agent = "$MASTER_NODE_TOKEN"
  }
}
connect {
  enabled = true
}
tls {
  defaults {
    ca_file = "$CA_FILE"
    cert_file = "$CONSUL_CERT_FILE"
    key_file = "$CONSUL_KEY_FILE"
    verify_incoming = true
    verify_outgoing = true
  }
  internal_rpc {
    verify_server_hostname = true
  }
}
performance {
  raft_multiplier = 1
}
EOF

echo "Consul configuration file created at $CONSUL_CONFIG_FILE with ACL token"


create_vault_policy
generate_vault_token
stop_cluster
mark_cluster_initialized