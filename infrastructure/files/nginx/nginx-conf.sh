#!/bin/bash
source /etc/environment

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt -subj "/C=FR/ST=State/L=City/O=Company/CN=your_domain.com"


cat <<EOF > $NGINX_CONFIG_FILE
events {
    worker_connections 1024; # Nombre de connexions simultanées qu'un worker peut gérer
}

http {
    server {
        # TODO: Mise en place des certificats
        listen 443 ssl;
        server_name $SERVICE_NAME;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
        ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

        location /health {
            include fastcgi_params;
            fastcgi_pass unix:$SOCKET_PATH;
            fastcgi_param SCRIPT_FILENAME $HEALTH_CHECK_FILE;
            fastcgi_param DOCUMENT_ROOT /usr/local/bin;
            fastcgi_param SCRIPT_NAME health-check.sh;
            fastcgi_param QUERY_STRING "";
        }
        # Autres configurations de votre serveur
    }
}
EOF
