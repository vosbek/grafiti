# 🚀 CodeAnalysis MultiAgent MVP - New Machine Quick Start

## ⚡ **TL;DR - 5 Minute Setup**

```bash
# 1. Prerequisites (install if missing)
# - Python 3.11+, Node.js 18+, Docker Desktop, AWS CLI, Git

# 2. Configure AWS
aws configure
# Enter: Access Key, Secret Key, us-east-1, json

# 3. Clone and setup
git clone <your-repo-url>
cd codeanalysis-multiagent-mvp

# 4. Pre-flight check (recommended)
python preflight_check.py --fix-issues

# 5. Run setup
python setup.py

# 6. Access your app
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📋 **Detailed Setup Process**

### **Step 1: Install Prerequisites (10-15 minutes)**

#### Windows:
```powershell
# Install via Chocolatey (recommended)
choco install python nodejs docker-desktop awscli git

# Or download manually:
# Python 3.11+: https://python.org
# Node.js 18+: https://nodejs.org  
# Docker Desktop: https://docker.com
# AWS CLI: https://docs.aws.amazon.com/cli/
# Git: https://git-scm.com
```

#### macOS:
```bash
# Install via Homebrew
brew install python@3.11 node awscli git
brew install --cask docker

# Start Docker Desktop
open -a Docker
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 nodejs npm docker.io awscli git

# Start Docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### **Step 2: Configure AWS (2-3 minutes)**

```bash
# Configure AWS credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]  
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### **Step 3: Clone Repository (1 minute)**

```bash
git clone <your-repository-url>
cd codeanalysis-multiagent-mvp
```

### **Step 4: Pre-flight Check (1-2 minutes)**

```bash
# Check system readiness
python preflight_check.py

# Auto-fix common issues
python preflight_check.py --fix-issues
```

### **Step 5: Run Setup (5-10 minutes)**

```bash
# Full setup with validation
python setup.py

# Or quick setup (skip some validation)
python setup.py --quick

# Or if you have port conflicts
python setup.py --force-kill-ports
```

### **Step 6: Verify Installation (1 minute)**

```bash
# Check all services are running
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
curl http://localhost:8001/health

# All should return 200 OK
```

## 🔧 **Alternative Setup Methods**

### **Method A: Environment Script First**
```bash
# Windows
setup_environment.bat
python setup.py

# Linux/Mac
source setup_environment.sh
python setup.py
```

### **Method B: Custom Ports (if conflicts)**
```bash
# Run on different ports
python start_custom_ports.py --frontend-port 3001 --backend-port 8080
```

### **Method C: Docker Compose Only**
```bash
# Just the containers
docker-compose -f docker-compose.verified.yml --profile bedrock up -d
```

## 🚨 **Troubleshooting Common Issues**

### **Issue: Port Conflicts**
```bash
# Check what's using ports
netstat -ano | findstr ":8000\|:3000\|:7474"

# Force kill conflicting services
python setup.py --force-kill-ports --kill-port-processes
```

### **Issue: AWS Credentials Not Found**
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID=your-key-here
export AWS_SECRET_ACCESS_KEY=your-secret-here
export AWS_DEFAULT_REGION=us-east-1

# Or run environment setup
./setup_environment.sh  # Linux/Mac
setup_environment.bat   # Windows
```

### **Issue: Docker Not Running**
```bash
# Windows: Start Docker Desktop
# Linux: sudo systemctl start docker
# Mac: open -a Docker

# Verify Docker is running
docker ps
```

### **Issue: Node Dependencies Fail**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps --force
```

### **Issue: Python Dependencies Fail**
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install PyTorch first
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Then run setup
python setup.py
```

### **Issue: Bedrock Access Denied**
```bash
# Check AWS permissions - you need:
# - bedrock:ListFoundationModels
# - bedrock:InvokeModel
# - bedrock:GetFoundationModel

# Test access
aws bedrock list-foundation-models --region us-east-1
```

## ✅ **Success Indicators**

### **Setup Complete When You See:**
- ✅ All containers running: `docker ps` shows 5 containers
- ✅ Backend healthy: http://localhost:8000/api/v1/health returns 200
- ✅ Frontend loads: http://localhost:3000 shows dashboard
- ✅ Bedrock proxy works: http://localhost:8001/health returns 200
- ✅ Neo4j accessible: http://localhost:7474 shows database

### **Ready to Use When:**
- Dashboard shows "System Status: Healthy"
- All navigation links work in frontend
- API documentation loads at http://localhost:8000/docs
- No error messages in browser console

## 🎯 **What You Get**

### **Frontend Dashboard (http://localhost:3000)**
- 📊 System overview and health monitoring
- 📁 Repository management interface
- 🔍 Semantic code search powered by CodeBERT
- 🤖 Multi-agent system controls
- 📈 Analysis results visualization
- ⚙️ Configuration management

### **Backend API (http://localhost:8000)**
- 🔗 RESTful API for all operations
- 📚 Interactive API documentation at `/docs`
- 🧠 CodeBERT semantic embeddings
- 📊 Neo4j knowledge graph integration
- 🤖 Multi-agent orchestration
- ☁️ AWS Bedrock LLM integration

### **Infrastructure Services**
- 🗄️ Neo4j graph database (port 7474/7687)
- 🚀 Redis caching (port 6379)
- 🔗 LiteLLM Bedrock proxy (port 8001)

## 📞 **Getting Help**

### **If Setup Fails:**
1. **Run diagnostics**: `python preflight_check.py --fix-issues`
2. **Check logs**: `docker logs <container-name>`
3. **Clean restart**: `python setup.py --teardown-only` then `python setup.py`
4. **Nuclear option**: `python setup.py --force-kill-ports --kill-port-processes --clean-volumes`

### **For Development:**
- **Backend logs**: `docker logs codeanalysis-backend`
- **Frontend logs**: `docker logs codeanalysis-frontend`
- **Database logs**: `docker logs neo4j-codeanalysis`

## ⏱️ **Expected Timeline**

- **Fresh machine**: 20-30 minutes
- **With prerequisites**: 10-15 minutes  
- **Experienced user**: 5-10 minutes
- **Just the app**: 2-3 minutes

## 🎉 **You're Ready!**

Once setup completes successfully, you have a full enterprise-grade Java code analysis system with:

- **AI-powered semantic search** using CodeBERT
- **Multi-agent analysis** for architecture, security, and migration planning
- **Temporal knowledge graph** for relationship tracking
- **AWS Bedrock integration** for enterprise LLM access
- **Modern React dashboard** for intuitive interaction

**Start analyzing Java code with AI! 🚀**