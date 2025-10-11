#!/bin/bash

# Simple Docker Compose deployment for EC2
# Run this script as root or with sudo

set -e

echo "🕳️ Setting up Mind Flayer Model Lab with Docker Compose on EC2..."

# Update system
apt-get update

# Install Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker ubuntu || usermod -aG docker ec2-user || true
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Start Docker service
systemctl enable docker
systemctl start docker

echo "✅ Docker and Docker Compose installed!"
echo "🚀 Now run: sudo docker-compose up -d --build"
echo "🌐 The app will be available on port 80"