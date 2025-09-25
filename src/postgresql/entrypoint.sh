#!/bin/bash

# Appeler le script Vault
vault.sh

# Appeler le script d'initialisation de PostgreSQL
init-postgresql.sh

# Ajouter la tâche cron pour vérifier les nouveaux nœuds
#/usr/local/bin/add-cron-job.sh

set -m

# Démarrer PostgreSQL avec la configuration appropriée
#psql -D /var/lib/postgresql/data -c config_file=/etc/postgresql/postgresql.conf "$@" &
echo "/etc/postgresql/postgresql.conf DEBUT"
cat /etc/postgresql/postgresql.conf
echo "/etc/postgresql/postgresql.conf FIN"

su - postgresql -c "/usr/lib/postgresql/18/bin/postgres -D /var/lib/postgresql/data -c config_file=/etc/postgresql/postgresql.conf" &

# Démarrer le script fcgiwrap pour Nginx
nginx-fcgiwrap.sh

# Configurer Nginx
nginx-conf.sh

# Afficher les jobs en arrière-plan
jobs

# Ramener PostgreSQL au premier plan
fg %1
