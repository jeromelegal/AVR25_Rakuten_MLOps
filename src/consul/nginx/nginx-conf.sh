#/bin/bash
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
        ssl_certificate $CONSUL_CERT_FILE;
        ssl_certificate_key $CONSUL_KEY_FILE;

        location /health {
            include fastcgi_params;
            fastcgi_pass unix:/var/run/fcgiwrap/fcgiwrap.socket;
            fastcgi_param SCRIPT_FILENAME $HEALTH_CHECK_FILE;
            fastcgi_param DOCUMENT_ROOT /usr/local/bin;
            fastcgi_param SCRIPT_NAME health-check.sh;
            fastcgi_param QUERY_STRING "";
        }

        # Autres configurations de votre serveur
    }
}
EOF
