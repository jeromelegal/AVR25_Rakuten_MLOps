#!/bin/bash
# Générer le fichier de configuration PostgreSQL

cat <<EOF > /etc/postgresql/postgresql.conf
# postgresql.conf

# Options de stockage
data_directory = '${DB_PATH}'
hba_file = '/etc/postgresql/pg_hba.conf'
ident_file = '/etc/postgresql/pg_ident.conf'

# Options de journalisation
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_truncate_on_rotation = on
log_rotation_age = 1d
log_rotation_size = 10MB

# Options de connexion
listen_addresses = '${BIND_IP}'
port = ${PORT}

# Options de réplication
# (Ajoutez ici les configurations spécifiques à la réplication si nécessaire)
EOF

# Ajouter les options SSL si activées
if [ "${TLS_MODE}" = "require" ]; then
  cat <<EOF >> /etc/postgresql/postgresql.conf
ssl = on
ssl_cert_file = '${POSTGRESQL_CERT_PATH}'
ssl_key_file = '${POSTGRESQL_KEY_PATH}'
ssl_ca_file = '${POSTGRESQL_CA_PATH}'
EOF
fi

# Ajouter les options de sécurité
if [ "${AUTHORIZATION}" = "enabled" ]; then
  cat <<EOF >> /etc/postgresql/postgresql.conf
# Options de sécurité
password_encryption = scram-sha-256
EOF
fi

echo "Fichier de configuration PostgreSQL généré avec succès."

# echo "Affichage du fichier de configuration PostgreSQL"
# cat /etc/postgresql/postgresql.conf

# Générer le fichier d'initialisation du cluster PostgreSQL
# cat <<EOF > /usr/local/bin/init-postgres.sql
# CREATE USER postgres WITH PASSWORD 'postgres';
# CREATE DATABASE mydb;
# GRANT ALL PRIVILEGES ON DATABASE mydb TO postgres;
# EOF

# echo "Affichage du fichier /usr/local/bin/init-postgres.sql de PostgreSQL"
# cat /usr/local/bin/init-postgres.sql



ips=$(ip -o -4 addr list | awk '{print $4}' | cut -d/ -f1)


echo -e "# TYPE\tDATABASE\tUSER\t\tADDRESS\t\t\tMETHOD" > /etc/postgresql/pg_hba.conf
for ip in $ips; do
    echo -e "hostssl\tall\t\tall\t\t0.0.0.0/0\t\tcert clientcert=verify-full" >> /etc/postgresql/pg_hba.conf
    echo -e "hostssl\tall\t\tdb_manager_user\t$ip/16\t\tcert clientcert=verify-full" >> /etc/postgresql/pg_hba.conf
    echo -e "hostssl\tall\t\t$MLFLOW_USER\t$ip/16\t\tcert clientcert=verify-full" >> /etc/postgresql/pg_hba.conf
done
echo -e "local\tall\t\tpostgresql\t\t\t\tscram-sha-256" >> /etc/postgresql/pg_hba.conf


echo "cat /etc/postgresql/pg_hba.conf"
cat /etc/postgresql/pg_hba.conf



cat <<EOF > /etc/postgresql/pg_ident.conf
# MAPNAME  IDENT-USERNAME  PG-USERNAME
EOF