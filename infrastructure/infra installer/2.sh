#!/bin/bash
# Installer Node.js (version LTS recommandée)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Installer Vue CLI
sudo npm install -g @vue/cli
