#!/bin/bash

source vault.sh


source consul.sh


jobs_output=$(jobs 2>&1)
# Vérifie si la sortie de jobs est vide
until [[ -z "$jobs_output" ]]; do
  # Aucun processus en cours, on sort de la boucle
  jobs_output=$(jobs 2>&1)
  jobs
  sleep 1
done

set -m

consul agent -config-file=$CONSUL_CONFIG_FILE  &


source nginx-conf.sh
source nginx-fcgiwrap.sh



fg %1




