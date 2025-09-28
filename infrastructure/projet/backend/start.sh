#!/bin/bash
cd ~/projet/backend
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
uvicorn main:app --reload --host 0.0.0.0 --port 8000
