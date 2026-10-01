#!/bin/bash
# Run ON a fresh Ubuntu EC2 instance (after ssh). Security group must allow inbound TCP 8501.
set -e
sudo apt-get update -y && sudo apt-get install -y docker.io git
sudo systemctl enable --now docker
git clone https://github.com/Ak-arsha/retailpulse.git && cd retailpulse
sudo docker build -t retailpulse .
# add  -e GEMINI_API_KEY=xxxx  to enable the GenAI tab
sudo docker run -d --restart unless-stopped -p 8501:8080 --name retailpulse retailpulse
echo "Open http://<EC2-PUBLIC-IP>:8501"
