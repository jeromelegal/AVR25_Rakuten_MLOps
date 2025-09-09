#!/bin/bash


vault.sh


# Appeler le script d'initialisation
init-mongodb.sh

# Ajouter la tâche cron pour vérifier les nouveaux nœuds
#/usr/local/bin/add-cron-job.sh
#exec mongod --config /etc/mongod.conf "$@"

set -m


mongod --config /etc/mongod.conf "$@" &

nginx-fcgiwrap.sh

nginx-conf.sh


jobs 

fg %1