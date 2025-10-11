#!/bin/bash

# Quick setup script for EC2 deployment
# Run this after deploy-ec2.sh

echo "🔧 Configuring services..."

# Copy systemd service file
cp mindflayer.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mindflayer

# Configure nginx
cp nginx.conf /etc/nginx/sites-available/mindflayer
ln -sf /etc/nginx/sites-available/mindflayer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start services
systemctl start mindflayer
systemctl restart nginx

# Enable firewall (optional)
# ufw allow 22
# ufw allow 80
# ufw --force enable

echo "✅ Services configured and started!"
echo "🌐 Mind Flayer Model Lab is now running on port 80"
echo "📊 Check status with: systemctl status mindflayer"
echo "📝 View logs with: journalctl -fu mindflayer"