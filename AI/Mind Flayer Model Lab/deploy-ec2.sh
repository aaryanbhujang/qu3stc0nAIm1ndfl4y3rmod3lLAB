#!/bin/bash

# EC2 Deployment Script for Mind Flayer Model Lab
# Run this script as root or with sudo

set -e

echo "🕳️ Setting up Mind Flayer Model Lab on EC2..."

# Check if flag.txt exists in current directory
if [ ! -f flag.txt ]; then
    echo "❌ Error: flag.txt not found in current directory!"
    echo "Please make sure you're running this script from the 'Mind Flayer Model Lab' directory"
    exit 1
fi

echo "✅ Found flag.txt, proceeding with deployment..."

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    git \
    build-essential \
    libhdf5-dev \
    libjpeg-dev \
    curl \
    zlib1g-dev \
    e2fsprogs

# Create application user
useradd -m -s /bin/bash ctfuser || true

# Create application directory
mkdir -p /opt/mindflayer/app
chown ctfuser:ctfuser /opt/mindflayer

# Copy application files first
cp -r . /opt/mindflayer/app/
chown -R ctfuser:ctfuser /opt/mindflayer/app/

# Switch to ctfuser for app setup
sudo -u ctfuser bash << 'EOF'
cd /opt/mindflayer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install Flask==2.3.3 gunicorn==21.2.0 tensorflow==2.12.0 python-dotenv==1.0.1

# Create uploads directory
mkdir -p uploads
EOF

# Secure the flag file (only if it exists)
if [ -f /opt/mindflayer/app/flag.txt ]; then
    chown root:root /opt/mindflayer/app/flag.txt
    chmod 444 /opt/mindflayer/app/flag.txt
    chattr +i /opt/mindflayer/app/flag.txt 2>/dev/null || true
    echo "✅ Flag file secured"
else
    echo "⚠️ Warning: flag.txt not found. Please ensure it's in the source directory."
fi

echo "✅ Installation complete!"
echo "🚀 Run 'sudo systemctl start mindflayer' to start the service"
echo "🌐 The app will be available on port 80"