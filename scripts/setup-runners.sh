#!/bin/bash

sudo apt-get update

# Install yq
sudo rm -f /usr/bin/yq /usr/local/bin/yq
wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O yq
chmod +x yq
sudo mv yq /usr/bin/yq
yq --version

# Install docker
## Add Docker's official GPG key:
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
## Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Setup runner
## Create a folder
mkdir actions-runner && cd actions-runner
## Download the latest runner package
curl -o actions-runner-linux-arm64-2.328.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.328.0/actions-runner-linux-arm64-2.328.0.tar.gz
## Optional: Validate the hash
echo "b801b9809c4d9301932bccadf57ca13533073b2aa9fa9b8e625a8db905b5d8eb  actions-runner-linux-arm64-2.328.0.tar.gz" | shasum -a 256 -c
## Extract the installer
tar xzf ./actions-runner-linux-arm64-2.328.0.tar.gz
rm ./actions-runner-linux-arm64-2.328.0.tar.gz
## Configure runner
RUNNER_ALLOW_RUNASROOT=1 && \
sudo ./config.sh \
    --url https://github.com/AVR25-Rakuten/AVR25_Rakuten_MLOps \
    --token AGEFIUGEL7K7BUPPVNLCO3DIYHSW4 \
    --name jfp-runner \
    --labels "self-hosted,Linux,arm64,phil-host"
# Start runner
./run.sh