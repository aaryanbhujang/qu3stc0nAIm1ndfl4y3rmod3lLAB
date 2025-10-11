# Mind Flayer Model Lab - Docker Compose EC2 Deployment

## 🐳 **Super Simple Docker Deployment**

### **Prerequisites**
- EC2 instance (Ubuntu 20.04+ or Amazon Linux 2)
- Security group allowing HTTP (port 80) and SSH (port 22)

### **1. Upload Files to EC2**
```bash
# On your local machine
scp -i your-key.pem -r "Mind Flayer Model Lab" ubuntu@your-ec2-ip:/tmp/
```

### **2. SSH and Deploy with Docker**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
cd "/tmp/Mind Flayer Model Lab"

# Install Docker and Docker Compose
sudo chmod +x docker-setup-ec2.sh
sudo ./docker-setup-ec2.sh

# Deploy the CTF
sudo docker-compose up -d --build
```

### **3. Access Your CTF**
```
http://your-ec2-public-ip
```

## 🔧 **Docker Commands**

### **View Logs**
```bash
sudo docker-compose logs -f
sudo docker logs mindflayer-app
```

### **Restart Service**
```bash
sudo docker-compose restart
```

### **Stop Service**
```bash
sudo docker-compose down
```

### **Update and Restart**
```bash
sudo docker-compose down
sudo docker-compose up -d --build
```

### **Check Status**
```bash
sudo docker-compose ps
sudo docker stats
```

## 🛡️ **Security Features**

✅ **Container Security:**
- Runs as non-root user inside container
- Flag file is read-only and immutable
- Isolated environment
- Automatic restart on failure

✅ **Health Monitoring:**
- Built-in health checks
- Automatic container restart if unhealthy

## 🎯 **Port Mapping**

- **Container Port:** 8000 (internal)
- **Host Port:** 80 (external access)
- **Access URL:** `http://your-ec2-ip`

## 🚨 **Troubleshooting**

### **Container won't start:**
```bash
sudo docker-compose logs mindflayer
sudo docker ps -a
```

### **Port conflicts:**
```bash
sudo netstat -tlnp | grep :80
sudo docker-compose down
sudo docker-compose up -d
```

### **Permission issues:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## 🔥 **Quick Commands Summary**

```bash
# One-time setup
sudo ./docker-setup-ec2.sh

# Deploy
sudo docker-compose up -d --build

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f

# Access CTF
curl http://your-ec2-ip/health
```

**Much simpler than the systemd setup!** 🚀