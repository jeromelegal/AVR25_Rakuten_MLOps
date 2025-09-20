#!/bin/bash
set -euo pipefail

echo "Configuring grafana..."
sed -i \
  -e "s|;http_port = 3000|http_port = ${SERVICE_PORT}|g" \
  /etc/grafana/grafana.ini
chown grafana:grafana /etc/grafana/grafana.ini

chown grafana:grafana /usr/share/grafana

echo "Starting Grafana..."
su grafana -c "grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana" &
echo "Grafana started successfully!"
