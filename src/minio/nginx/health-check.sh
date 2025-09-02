#!/bin/bash

echo "Script started" >> /var/log/health-check.log

check=0
if [ $check -eq 0 ]; then
    echo -e "Status: 200 OK\r"
    echo -e "Content-Type: text/plain\r\n\r"
    echo "Healthy"
else
    echo -e "Status: 500 Internal Server Error\r"
    echo -e "Content-Type: text/plain\r\n\r"
    echo "Unhealthy"
fi

echo "Script finished" >> /var/log/health-check.log
