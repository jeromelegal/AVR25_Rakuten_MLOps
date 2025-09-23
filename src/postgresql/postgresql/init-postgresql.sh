#!/bin/bash

SAVE_AUTHORIZATION=$AUTHORIZATION
AUTHORIZATION=disabled
mkdir -p $(dirname $LOG_PATH) $DB_PATH
generate-config.sh

# Démarrer PostgreSQL en arrière-plan sans authentification
su - postgresql -c "/usr/lib/postgresql/17/bin/initdb -D /data/postgresql"

chown postgresql:postgresql /etc/postgresql/postgresql.conf
chown postgresql:postgresql /data/postgresql 
chown postgresql:postgresql $POSTGRESQL_KEY_PATH
chmod 0600 $POSTGRESQL_KEY_PATH
chmod 750 /data/postgresql

chown postgresql:postgresql /var/run/postgresql/
chmod 755 /var/run/postgresql/

chown postgresql:postgresql /etc/postgresql/pg_hba.conf
chmod 640 /etc/postgresql/pg_hba.conf

chown postgresql:postgresql /etc/postgresql/pg_ident.conf
chmod 640 /etc/postgresql/pg_ident.conf

su - postgresql -c "/usr/lib/postgresql/17/bin/postgres -D /data/postgresql -c config_file=/etc/postgresql/postgresql.conf" &
PID_POSTGRESQL=$!

echo "Waiting for PostgreSQL to be ready..."
# Attendre que PostgreSQL soit prêt
until pg_isready -h $SERVICE_NAME -p 5432 -U postgres; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

chown postgresql:postgresql $POSTGRESQL_POSTGRESQL_KEY_PATH
chmod 600 $POSTGRESQL_POSTGRESQL_KEY_PATH

chown postgresql:postgresql $POSTGRESQL_API_POSTGRESQL_KEY_PATH
chmod 600 $POSTGRESQL_API_POSTGRESQL_KEY_PATH

chown postgresql:postgresql $POSTGRESQL_MLFLOW_KEY_PATH
chmod 600 $POSTGRESQL_MLFLOW_KEY_PATH

echo "Initialization of the database START"
# Exécuter le script d'initialisation de la base de données
su - postgresql -c "psql \"host=$SERVICE_NAME port=5432 user=postgresql dbname=postgres sslmode=verify-full sslcert=$POSTGRESQL_POSTGRESQL_CERT_PATH sslkey=$POSTGRESQL_POSTGRESQL_KEY_PATH sslrootcert=$POSTGRESQL_POSTGRESQL_CA_PATH\" -f /usr/local/bin/init-postgresql.sql"
echo "Initialization of the database END"

# TODO variables d'environnement à réaliser : port, user et dbname 
# Insert basics categories in database
echo "Insert categories in the database START"
su - postgresql -c "psql \"host=$SERVICE_NAME port=5432 user=postgresql dbname=postgres sslmode=verify-full sslcert=$POSTGRESQL_POSTGRESQL_CERT_PATH sslkey=$POSTGRESQL_POSTGRESQL_KEY_PATH sslrootcert=$POSTGRESQL_POSTGRESQL_CA_PATH\" -f /usr/local/bin/init-categories.sql"
echo "Insertion in database END"

# Create MLFlow database and user
echo "Setting up MLFlow table and user..."
su - postgresql -c "psql \"host=$SERVICE_NAME port=5432 user=postgresql dbname=postgres sslmode=verify-full sslcert=$POSTGRESQL_POSTGRESQL_CERT_PATH sslkey=$POSTGRESQL_POSTGRESQL_KEY_PATH sslrootcert=$POSTGRESQL_POSTGRESQL_CA_PATH\" \
                          --set=mlflow_db='$MLFLOW_DATABASE' \
                          --set=mlflow_user='$MLFLOW_USER' \
                          --set=mlflow_user_password='$MLFLOW_USER_PASSWORD' \
                          -f /usr/local/bin/init-postgresql-mlflow.sql"
su - postgresql -c "psql \"host=$SERVICE_NAME port=5432 user=$MLFLOW_USER password=$MLFLOW_USER_PASSWORD dbname=$MLFLOW_DATABASE sslmode=verify-full sslcert=$POSTGRESQL_MLFLOW_CERT_PATH sslkey=$POSTGRESQL_MLFLOW_KEY_PATH sslrootcert=$POSTGRESQL_MLFLOW_CA_PATH\""
echo "MLFlow table and user created."

# List users
su - postgresql -c "psql \"host=$SERVICE_NAME port=5432 user=db_manager_user password=db_manager_user_password dbname=file_storage sslmode=verify-full sslcert=$POSTGRESQL_API_POSTGRESQL_CERT_PATH sslkey=$POSTGRESQL_API_POSTGRESQL_KEY_PATH sslrootcert=$POSTGRESQL_API_POSTGRESQL_CA_PATH\" -c \" SELECT * FROM users;\""

# Arrêter PostgreSQL
su - postgresql -c "/usr/lib/postgresql/17/bin/pg_ctl -D /data/postgresql -l /data/postgresql/pg_log/logfile stop"

# Boucle jusqu'à ce que PostgreSQL soit arrêté
until ! pgrep -x "postgres" > /dev/null ; do
    echo "PostgreSQL is still running ($PID_POSTGRESQL). Waiting for it to stop..."
    sleep 1
done
echo "PostgreSQL is stopped."

AUTHORIZATION=$SAVE_AUTHORIZATION
generate-config.sh
