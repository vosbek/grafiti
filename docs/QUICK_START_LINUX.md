# Linux Quick Start Guide

## 🚀 5-Minute Setup for Ubuntu/Debian

This guide gets you running on Linux with verified, tested steps.

### Prerequisites (2 minutes)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install all required packages in one command
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nodejs \
    npm \
    git \
    curl \
    wget \
    build-essential \
    docker.io \
    docker-compose

# Add user to docker group (logout/login required after this)
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### For CentOS/RHEL/Fedora

```bash
# CentOS/RHEL 8+
sudo dnf install -y python3.11 python3.11-devel nodejs npm git curl wget gcc docker

# Fedora
sudo dnf install -y python3.11 python3.11-devel nodejs npm git curl wget gcc docker docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Verify Installation

```bash
# Check versions (should match these or newer)
python3.11 --version  # Python 3.11.9
node --version         # v18.x or newer
npm --version          # 9.x or newer  
git --version          # Any recent version
docker --version       # 20.x or newer

# Test Docker (may require logout/login first)
docker run hello-world
```

### Deploy Application (3 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd graphiti

# Run automated deployment
python3.11 deploy.py --platform linux --mode production

# Expected output: "✅ Deployment completed successfully!"
```

### Start Services

The deployment creates shell scripts for easy startup:

```bash
# Start backend API server
./start_backend.sh

# In new terminal, start frontend
./start_frontend.sh

# If using AWS Bedrock, also start proxy
./start_bedrock_proxy.sh  # Only if --bedrock was used
```

### Verify Everything Works

```bash
# Test backend
curl http://localhost:8000/api/v1/health

# Test frontend (should return HTML)
curl http://localhost:3000

# Check database container
docker ps | grep neo4j
```

Open browser to:
- **Backend API**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000

## 🐛 Linux-Specific Troubleshooting

### Permission Issues

```bash
# Fix common permission issues
sudo chown -R $USER:$USER ~/graphiti
chmod +x start_backend.sh start_frontend.sh

# If Docker permission denied
sudo usermod -aG docker $USER
# Then logout and login again
```

### Python Version Issues

```bash
# If python3.11 not available, install from deadsnakes PPA (Ubuntu)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create symbolic link if needed
sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python
```

### Node.js Version Issues

```bash
# Install specific Node.js version via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or use snap (Ubuntu)
sudo snap install node --classic
```

### Port Conflicts

```bash
# Check what's using ports
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000

# Kill process if needed
sudo fuser -k 8000/tcp
sudo fuser -k 3000/tcp
```

### Firewall Configuration

```bash
# Ubuntu/Debian UFW
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw enable

# CentOS/RHEL firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload

# Or disable firewall for development
sudo ufw disable  # Ubuntu
sudo systemctl stop firewalld  # CentOS
```

### Memory Issues

```bash
# Check memory usage
free -h
htop

# Increase swap if needed (careful with SSD)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 🔧 Linux Optimization Tips

### Performance Optimization

```bash
# Increase file descriptor limits
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Increase file watcher limits for development
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Optimize for development workload
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=15' | sudo tee -a /etc/sysctl.conf
```

### Development Environment

```bash
# Install useful development tools
sudo apt install -y \
    vim \
    htop \
    tree \
    jq \
    curl \
    httpie \
    tmux \
    screen

# Optional: Install VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code
```

### Docker Optimization

```bash
# Configure Docker for development
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

sudo systemctl restart docker
```

## 📊 System Monitoring

### Resource Monitoring

```bash
# Monitor system resources
htop           # Interactive process viewer
iotop          # Disk I/O monitoring  
nethogs        # Network usage by process
df -h          # Disk usage
free -h        # Memory usage
```

### Application Monitoring

```bash
# Monitor application logs
tail -f backend/logs/application.log
docker logs -f neo4j-codeanalysis

# Monitor ports
sudo netstat -tulpn | grep -E ':(8000|3000|7474|7687)'

# Check service health
curl -s http://localhost:8000/api/v1/health | jq .
```

### Database Monitoring

```bash
# Neo4j container logs
docker logs neo4j-codeanalysis

# Neo4j web interface
curl http://localhost:7474

# Database connection test
echo "MATCH (n) RETURN count(n);" | docker exec -i neo4j-codeanalysis cypher-shell -u neo4j -p codeanalysis123
```

## 🔒 Security Considerations

### Basic Security Setup

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Configure automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# Basic fail2ban setup
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### Development Security

```bash
# Don't expose services to external networks in development
# Services are bound to localhost by default

# Use environment files for secrets (never commit .env files)
chmod 600 backend/.env frontend/.env.local

# Secure Docker socket (if needed)
sudo chmod 660 /var/run/docker.sock
```

## 🆘 Getting Help

### Debug Information Collection

```bash
# System information
uname -a > debug_info.txt
lsb_release -a >> debug_info.txt 2>/dev/null
python3.11 --version >> debug_info.txt
node --version >> debug_info.txt
docker --version >> debug_info.txt
free -h >> debug_info.txt
df -h >> debug_info.txt

# Service status
systemctl status docker >> debug_info.txt
docker ps >> debug_info.txt
```

### Common Linux Issues

1. **"Permission denied"** - Check file permissions and user groups
2. **"Address already in use"** - Another process is using the port
3. **"Docker daemon not running"** - Start Docker with `sudo systemctl start docker`  
4. **"python3.11: command not found"** - Install from deadsnakes PPA
5. **"npm install fails"** - Check disk space and network connectivity

### Enterprise Environment

```bash
# Configure for enterprise proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,*.company.com

# Configure npm for proxy
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080

# Configure pip for proxy
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
proxy = http://proxy.company.com:8080
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
```

### Systemd Service Setup (Production)

```bash
# Create systemd service for backend
sudo tee /etc/systemd/system/codeanalysis-backend.service << EOF
[Unit]
Description=CodeAnalysis Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/graphiti/backend
ExecStart=/home/$USER/graphiti/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable codeanalysis-backend
sudo systemctl start codeanalysis-backend
```

This Linux guide provides the fastest path to a working CodeAnalysis system with all verified fixes and optimizations included.