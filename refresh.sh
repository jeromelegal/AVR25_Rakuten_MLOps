#!/bin/bash

docker compose down postgresql airflow
docker volume rm down postgresql avr25_rakuten_mlops_postgresql-volume
docker compose build postgresql airflow
docker compose up postgresql airflow --force-recreate