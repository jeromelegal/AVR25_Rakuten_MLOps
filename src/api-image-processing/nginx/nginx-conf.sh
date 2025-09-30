#!/bin/bash

cat <<EOF > $NGINX_CONFIG_FILE
events {
    worker_connections 1024; # Nombre de connexions simultanées qu'un worker peut gérer
}

http {
    server {
        listen 443 ssl;
        server_name $SERVICE_NAME;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_certificate $API_IMAGE_PROCESSING_CERT_PATH;
        ssl_certificate_key $API_IMAGE_PROCESSING_KEY_PATH;

        location /health {
            include fastcgi_params;
            fastcgi_pass unix:/var/run/fcgiwrap/fcgiwrap.socket;
            fastcgi_param SCRIPT_FILENAME $HEALTH_CHECK_FILE;
            fastcgi_param DOCUMENT_ROOT /usr/local/bin;
            fastcgi_param SCRIPT_NAME health-check.sh;
            fastcgi_param QUERY_STRING "";
        }

        # Autres configurations de votre serveur
        location / {
            proxy_pass https://$SERVICE_NAME:$SERVICE_PORT;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            proxy_ssl_certificate     $API_IMAGE_PROCESSING_CERT_PATH;
            proxy_ssl_certificate_key $API_IMAGE_PROCESSING_KEY_PATH;
            proxy_ssl_trusted_certificate $API_IMAGE_PROCESSING_CA_PATH;
            proxy_ssl_verify on;
            proxy_ssl_verify_depth 2;

        }
    }
}
EOF
