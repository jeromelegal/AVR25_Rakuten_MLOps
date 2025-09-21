#!/bin/bash
# set -euo pipefail

# Fonction pour afficher un message d'erreur et quitter
error_exit() {
    echo "❌ ERREUR: $1" >&2
    # exit 1
}

# Fonction pour afficher un message d'information
info_msg() {
    echo "ℹ️ INFO: $1"
}

# Fonction pour afficher un message de succès
success_msg() {
    echo "✅ SUCCÈS: $1"
}

# Début du script
echo "🚀 Démarrage du script d'entrée Airflow..."

# Vérification des variables d'environnement requises
info_msg "Vérification des variables d'environnement requises..."
if [ -z "${POSTGRESQL_SERVICE_NAME}" ]; then
    error_exit "La variable POSTGRESQL_SERVICE_NAME doit être définie."
fi
info_msg "POSTGRESQL_SERVICE_NAME est défini à: ${POSTGRESQL_SERVICE_NAME}"
if [ -z "${AIRFLOW_INTERNAL_SECRET_KEY_PATH}" ]; then
    error_exit "La variable AIRFLOW_INTERNAL_SECRET_KEY_PATH doit être définie."
fi
info_msg "AIRFLOW_INTERNAL_SECRET_KEY_PATH est défini à: ${AIRFLOW_INTERNAL_SECRET_KEY_PATH}"

# Attente de la disponibilité de PostgreSQL
info_msg "Attente de la disponibilité de PostgreSQL..."

HTTP_CODE=0
until [ $HTTP_CODE -eq 200 ] ; do
    HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" "https://${POSTGRESQL_SERVICE_NAME}/health")
    info_msg "En attente que le service PostgreSQL soit disponible (code HTTP: $HTTP_CODE)..."
    sleep 1
    
done
if [ $HTTP_CODE -ne 200 ]; then
    error_exit "Le service PostgreSQL n'est pas devenu disponible après $MAX_ATTEMPTS tentatives (code HTTP: $HTTP_CODE)."
fi
success_msg "Le service PostgreSQL est disponible."

# Appel du script Vault
info_msg "Appel du script Vault pour récupérer les certificats et les clés..."
vault.sh
if [ $? -ne 0 ]; then
    error_exit "Le script Vault a échoué."
fi
success_msg "Le script Vault s'est exécuté avec succès."

# Configuration de la clé API Airflow
info_msg "Configuration de la clé API Airflow..."
if [ -n "${AIRFLOW__API__SECRET_KEY:-}" ]; then
    info_msg "Utilisation de la clé API Airflow à partir de la variable d'environnement."
else
    if [ -f "$AIRFLOW_INTERNAL_SECRET_KEY_PATH" ]; then
        info_msg "Utilisation de la clé Vault pour récupérer la clé API Airflow."
        export AIRFLOW__API__SECRET_KEY=$(cat "$AIRFLOW_INTERNAL_SECRET_KEY_PATH")
        if [ -z "$AIRFLOW__API__SECRET_KEY" ]; then
            error_exit "La clé API Airflow récupérée à partir de $AIRFLOW_INTERNAL_SECRET_KEY_PATH est vide."
        fi
        info_msg "Clé API Airflow configurée avec succès."
    else
        error_exit "Aucune clé API Airflow disponible."
    fi
fi

tail -f /dev/null

# Migration de la base de données Airflow
info_msg "Migration de la base de données Airflow..."
airflow db migrate
if [ $? -ne 0 ]; then
    error_exit "Échec de la migration de la base de données Airflow."
fi
success_msg "Migration de la base de données Airflow réussie."

# Démarrage d'Airflow en mode standalone
info_msg "Démarrage d'Airflow en mode standalone..."
airflow standalone &
if [ $? -ne 0 ]; then
    error_exit "Échec du démarrage d'Airflow en mode standalone."
fi
success_msg "Airflow a démarré en mode standalone."

# Attendre que le serveur Airflow soit disponible
info_msg "Attente de la disponibilité du serveur Airflow..."
sleep 20

# Création de l'utilisateur admin via SQL
info_msg "Création de l'utilisateur admin pour Airflow via SQL..."





#su - airflow -c "psql \"host=$POSTGRESQL_SERVICE_NAME port=5432 user=$POSTGRESQL_AIRFLOW_USER password=$POSTGRESQL_AIRFLOW_PASSWORD dbname=$POSTGRESQL_AIRFLOW_DATABASE sslmode=verify-full sslcert=$POSTGRESQL_AIRFLOW_CERT_PATH sslkey=$POSTGRESQL_AIRFLOW_KEY_PATH sslrootcert=$POSTGRESQL_AIRFLOW_CA_PATH\""

# su  psql -h $POSTGRESQL_SERVICE_NAME -p 5432 -U $POSTGRESQL_AIRFLOW_USER -d $POSTGRESQL_AIRFLOW_DATABASE --set=sslmode=verify-full --set=sslcert=$POSTGRESQL_AIRFLOW_CERT_PATH --set=sslkey=$POSTGRESQL_AIRFLOW_KEY_PATH --set=sslrootcert=$POSTGRESQL_AIRFLOW_CA_PATH -c "
#     INSERT INTO public.users (username, first_name, last_name, email, password, role)
#     VALUES ('admin', 'Admin', 'User', 'admin@example.com', 'pbkdf2_sha256\$120000\$v1\$2y\$12\$...hash...', 'Admin');
# "

if [ $? -ne 0 ]; then
    error_exit "Échec de la création de l'utilisateur admin via SQL."
fi
success_msg "Utilisateur admin créé avec succès via SQL."

# Garder le conteneur actif
tail -f /dev/null
