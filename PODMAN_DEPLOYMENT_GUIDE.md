# CodeAnalysis MultiAgent MVP - Podman Deployment Guide

## 🚨 Critical Alert: Podman Compatibility Required

**IMMEDIATE ACTION REQUIRED**: The CodeAnalysis application is currently **Docker-specific** and requires modifications for podman compatibility. This guide provides the necessary changes for successful deployment.

## ⚠️ Breaking Changes Identified

### 1. Hardcoded Docker Commands in Core Scripts

**Files with Docker Dependencies:**
- `deploy.py` (lines 285, 290, 293, 298)
- `validate_deployment.py` (lines 367, 375, 405)
- `verify_complete_deployment.py` (docker checks)

**Issue**: All automation scripts use `docker` commands directly:
```python
self._run_command(['docker', '--version'])
self._run_command(['docker', 'ps', '-a', '--format', '{{.Names}}'])
self._run_command(['docker', 'run', '-d', '--name', 'neo4j-codeanalysis', ...])
```

### 2. Docker Compose Configurations

**Files Requiring Changes:**
- `docker-compose.verified.yml` (uses Docker Compose v3.8 features)
- All compose files use Docker-specific networking and volume syntax

## 🔧 Quick Fix for Tomorrow's Deployment

### Option 1: Script Aliasing (Fastest - 5 minutes)

```bash
# Create podman aliases before running deployment
alias docker=podman
alias docker-compose=podman-compose

# Install podman-compose if not available
pip3 install podman-compose

# Run deployment with aliases
python deploy.py --platform auto --mode production
```

### Option 2: Modified Scripts (Recommended - 15 minutes)

Create podman-specific versions of the deployment scripts:

```bash
# Copy and modify deploy.py
cp deploy.py deploy_podman.py

# Edit deploy_podman.py - replace all 'docker' with 'podman'
sed -i 's/docker/podman/g' deploy_podman.py

# Similarly for validation
cp validate_deployment.py validate_deployment_podman.py
sed -i 's/docker/podman/g' validate_deployment_podman.py
```

### Option 3: Environment Variable Override (Most Flexible)

Modify the deployment scripts to use environment variables:

```python
# In deploy.py, replace:
# self._run_command(['docker', '--version'])
# With:
CONTAINER_RUNTIME = os.getenv('CONTAINER_RUNTIME', 'docker')
self._run_command([CONTAINER_RUNTIME, '--version'])
```

Then run:
```bash
export CONTAINER_RUNTIME=podman
python deploy.py --platform auto --mode production
```

## 📋 Pre-Deployment Verification Checklist

### System Requirements Check
```bash
# 1. Verify podman installation
podman --version
# Expected: podman version 4.0+

# 2. Install podman-compose
pip3 install podman-compose
podman-compose --version

# 3. Check Python version (CRITICAL)
python3 --version
# MUST be 3.11+ (verified requirement)

# 4. Check Node.js version (CRITICAL)
node --version
# MUST be 18.0+ (verified requirement)

# 5. Check available ports
netstat -tulpn | grep -E ':(8000|3000|7474|7687|6379)'
# Should return empty (ports available)

# 6. Check memory (CRITICAL)
free -h
# MUST have at least 8GB total RAM

# 7. Check disk space (CRITICAL)
df -h
# MUST have at least 50GB free space
```

### Podman-Specific Configuration

```bash
# 1. Enable podman socket (if needed for compatibility)
systemctl --user enable --now podman.socket

# 2. Create podman-compose alias
echo 'alias docker-compose=podman-compose' >> ~/.bashrc
source ~/.bashrc

# 3. Set up rootless podman (recommended)
podman system service --time=0 &

# 4. Test basic podman functionality
podman run --rm hello-world
```

## 🔄 Modified Deployment Process

### Step 1: Environment Setup
```bash
# Set container runtime
export CONTAINER_RUNTIME=podman

# Create aliases
alias docker=podman
alias docker-compose=podman-compose
```

### Step 2: Deploy with Manual Container Management
```bash
# Start Neo4j manually with podman
podman run -d \
  --name neo4j-codeanalysis \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/codeanalysis123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j_data:/data \
  neo4j:5.15

# Start Redis
podman run -d \
  --name redis-codeanalysis \
  -p 6379:6379 \
  redis:7-alpine

# Wait for services to be ready
sleep 30
```

### Step 3: Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies in verified order
pip install --upgrade pip setuptools wheel
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers>=4.35.0
pip install sentence-transformers>=2.2.2
pip install graphiti-core>=0.17.0
pip install -r backend/requirements.txt
```

### Step 4: Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm install ajv@8.12.0 --legacy-peer-deps
npm run build
cd ..
```

### Step 5: Application Startup
```bash
# Start backend
cd backend
export PYTHONPATH=/app/backend:$PYTHONPATH
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend (in new terminal)
cd frontend
npx serve -s build -l 3000 &
```

## 🧪 Comprehensive Testing Protocol

### Container Verification
```bash
# Check all containers are running
podman ps

# Expected output:
# CONTAINER ID  IMAGE                    COMMAND               CREATED        STATUS        PORTS                                           NAMES
# abc123def456  neo4j:5.15              "/sbin/tini -g -- ..." 2 minutes ago  Up 2 minutes  0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp neo4j-codeanalysis
# def456ghi789  redis:7-alpine          "docker-entrypoint..." 2 minutes ago  Up 2 minutes  0.0.0.0:6379->6379/tcp                        redis-codeanalysis
```

### Service Health Checks
```bash
# 1. Test Neo4j
curl http://localhost:7474
# Expected: Neo4j browser interface

# 2. Test Redis
redis-cli ping
# Expected: PONG

# 3. Test Backend API
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", ...}

# 4. Test Frontend
curl http://localhost:3000
# Expected: HTML response with React app
```

### Application Functionality Tests
```bash
# 1. Test API endpoints
curl http://localhost:8000/docs
curl http://localhost:8000/api/v1/repositories
curl http://localhost:8000/api/v1/agents

# 2. Test database connectivity
curl -X POST http://localhost:8000/api/v1/test-db-connection

# 3. Test ML models loading
curl -X POST http://localhost:8000/api/v1/test-codebert

# 4. Test frontend-backend integration
# Open browser: http://localhost:3000
# Check browser console for errors
```

## 🚨 Known Podman-Specific Issues & Solutions

### Issue 1: Permission Denied in Rootless Mode
```bash
# Symptom: Volume mount permission errors
# Solution: Run with proper user mapping
podman run --user $(id -u):$(id -g) ...

# OR run as root (less secure)
sudo podman run ...
```

### Issue 2: Port Binding Issues
```bash
# Symptom: Cannot bind to privileged ports (<1024)
# Solution: Use non-privileged ports or run as root
podman run -p 8080:8000 ...  # Instead of port 80
```

### Issue 3: Network Connectivity Between Containers
```bash
# Symptom: Containers cannot reach each other
# Solution: Create podman network
podman network create codeanalysis-network
podman run --network codeanalysis-network ...
```

### Issue 4: SELinux Context Issues
```bash
# Symptom: File access denied in containers
# Solution: Set proper SELinux context
podman run -v /path/to/data:/data:Z ...  # Note the :Z flag
```

## 🔄 Rollback Plan

If podman deployment fails, fallback options:

### Option 1: Install Docker
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# CentOS/RHEL
sudo dnf install docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again

# Run original deployment
python deploy.py --platform auto --mode production
```

### Option 2: Manual Native Installation
```bash
# Install services natively without containers
# Neo4j
sudo apt install neo4j

# Redis  
sudo apt install redis-server

# Configure and start services
sudo systemctl start neo4j redis-server

# Run application natively
python backend/main.py
```

## 📊 Success Criteria

### Deployment Successful If:
- ✅ All containers running: `podman ps` shows 2+ containers
- ✅ Neo4j accessible: `curl http://localhost:7474` returns 200
- ✅ Backend healthy: `curl http://localhost:8000/api/v1/health` returns healthy status
- ✅ Frontend accessible: `curl http://localhost:3000` returns HTML
- ✅ No critical errors in logs: `podman logs <container-name>`

### Performance Benchmarks:
- Backend startup: < 2 minutes
- Frontend build: < 5 minutes  
- API response time: < 500ms
- Memory usage: < 4GB total

## 🆘 Emergency Contact Protocol

If deployment fails tomorrow:

1. **Immediate Debug Steps:**
   ```bash
   # Check system resources
   free -h && df -h
   
   # Check container logs
   podman logs neo4j-codeanalysis
   podman logs redis-codeanalysis
   
   # Check application logs
   tail -f backend/logs/application.log
   ```

2. **Collect Debug Information:**
   ```bash
   # System info
   podman --version > debug_info.txt
   python3 --version >> debug_info.txt
   node --version >> debug_info.txt
   free -h >> debug_info.txt
   
   # Container status
   podman ps -a >> debug_info.txt
   podman logs neo4j-codeanalysis >> debug_info.txt
   ```

3. **Fallback to Docker:** See rollback plan above

This guide provides comprehensive podman compatibility for the CodeAnalysis application. The key is proper preparation and testing of the container runtime differences.