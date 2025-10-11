#!/bin/bash

# Deployment verification script

echo "🔍 Verifying Mind Flayer Model Lab deployment..."

# Check if app directory exists
if [ -d "/opt/mindflayer/app" ]; then
    echo "✅ App directory exists"
else
    echo "❌ App directory missing"
    exit 1
fi

# Check if flag.txt exists and is secured
if [ -f "/opt/mindflayer/app/flag.txt" ]; then
    echo "✅ Flag file exists"
    
    # Check permissions
    PERMS=$(stat -c "%a" /opt/mindflayer/app/flag.txt)
    if [ "$PERMS" = "444" ]; then
        echo "✅ Flag file has correct permissions (444)"
    else
        echo "⚠️ Flag file permissions: $PERMS (expected 444)"
    fi
    
    # Check ownership
    OWNER=$(stat -c "%U:%G" /opt/mindflayer/app/flag.txt)
    if [ "$OWNER" = "root:root" ]; then
        echo "✅ Flag file has correct ownership (root:root)"
    else
        echo "⚠️ Flag file ownership: $OWNER (expected root:root)"
    fi
    
    # Check if immutable
    if lsattr /opt/mindflayer/app/flag.txt 2>/dev/null | grep -q "i"; then
        echo "✅ Flag file is immutable"
    else
        echo "⚠️ Flag file is not immutable"
    fi
else
    echo "❌ Flag file missing"
fi

# Check virtual environment
if [ -d "/opt/mindflayer/venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment missing"
fi

# Check service file
if [ -f "/etc/systemd/system/mindflayer.service" ]; then
    echo "✅ Systemd service file exists"
else
    echo "❌ Systemd service file missing"
fi

# Check nginx configuration
if [ -f "/etc/nginx/sites-available/mindflayer" ]; then
    echo "✅ Nginx configuration exists"
else
    echo "❌ Nginx configuration missing"
fi

# Check if services are running
if systemctl is-active --quiet mindflayer; then
    echo "✅ Mind Flayer service is running"
else
    echo "⚠️ Mind Flayer service is not running"
    echo "   Try: sudo systemctl start mindflayer"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "⚠️ Nginx service is not running"
    echo "   Try: sudo systemctl start nginx"
fi

# Check if ports are listening
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "✅ Port 80 is listening"
else
    echo "⚠️ Port 80 is not listening"
fi

if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "✅ Port 8000 is listening"
else
    echo "⚠️ Port 8000 is not listening"
fi

echo ""
echo "🌐 If all checks pass, the CTF should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "🔧 Check logs with: sudo journalctl -fu mindflayer"