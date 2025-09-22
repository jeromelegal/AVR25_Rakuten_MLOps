#!/bin/bash
vault.sh

set -m

# Appeler le script d'initialisation
source init-airflow.sh
nginx-fcgiwrap.sh

nginx-conf.sh


jobs 

fg %1