#!/bin/bash
# Installer Python et pip (si ce n'est pas déjà fait)
sudo apt install -y python3 python3-pip

# Installer FastAPI et Uvicorn (serveur ASGI)
pip install --break-system-packages fastapi[all] uvicorn libvirt-python pycloudlib PyYAML Jinja2
