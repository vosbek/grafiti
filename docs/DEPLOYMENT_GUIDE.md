# CodeAnalysis MultiAgent MVP - Complete Deployment Guide

## 🚀 One-Command Deployment

For immediate deployment on any machine, use our verified deployment script:

```bash
# Clone repository
git clone <your-repo-url>
cd graphiti

# Run deployment script (handles all dependencies and configuration)
python deploy.py --platform auto --mode production

# For development mode
python deploy.py --platform auto --mode development --gpu-enabled

# For AWS Bedrock integration
python deploy.py --platform auto --mode production --bedrock
```

## 📋 Pre-Deployment Checklist

### System Requirements Verification

**Minimum Requirements (Verified Working):**
- ✅ **Python**: 3.11.9 (exact version tested)
- ✅ **Node.js**: 18.x or higher (24.2.0 verified)
- ✅ **Memory**: 8 GB RAM minimum (16 GB recommended)
- ✅ **Storage**: 50 GB free space (system uses ~15 GB)
- ✅ **OS**: Windows 11, Ubuntu 20.04+, macOS 12+

**Enterprise Scale (50-100 Repositories):**
- ✅ **CPU**: 16+ cores (tested on 8-core systems)
- ✅ **Memory**: 32-64 GB RAM
- ✅ **Storage**: 500+ GB SSD
- ✅ **GPU**: Optional but recommended for CodeBERT acceleration

### Network Requirements
- High-speed internet for repository cloning
- Access to PyPI and npm registries
- AWS Bedrock endpoint access (if using Bedrock)
- Internal GitHub enterprise access (if applicable)

## 🔧 Step-by-Step Manual Deployment

### Phase 1: Environment Setup

#### Windows 11 (Verified Process)

```powershell
# 1. Install Python 3.11 (exact version verified)
winget install Python.Python.3.11

# 2. Install Node.js 18+ 
winget install OpenJS.NodeJS

# 3. Verify installations
python --version  # Should show 3.11.x
node --version    # Should show 18.x or higher
npm --version     # Should show 9.x or higher

# 4. Install Git if not present
winget install Git.Git

# 5. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate
```

#### Linux/Ubuntu (Verified Process)

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y
sudo apt install build-essential git curl wget -y

# 3. Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 4. Verify installations
python3.11 --version
node --version
npm --version

# 5. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

#### macOS (Verified Process)

```bash
# 1. Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python 3.11 and Node.js
brew install python@3.11 node@18 git

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

### Phase 2: Backend Setup (Critical Fixes Applied)

```bash
# 1. Navigate to project directory
cd graphiti

# 2. Install backend dependencies (with verified fixes)
cd backend
pip install --upgrade pip setuptools wheel

# 3. Install core dependencies (order matters!)
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers>=4.35.0
pip install sentence-transformers>=2.2.2

# 4. Install Graphiti with compatibility fixes
pip install graphiti-core>=0.17.0

# 5. Install remaining dependencies
pip install -r requirements.txt

# 6. Verify critical imports (these were fixed during verification)
python -c "import torch; print('✓ PyTorch:', torch.__version__)"
python -c "import transformers; print('✓ Transformers installed')"
python -c "import graphiti_core; print('✓ Graphiti installed')"
python -c "import sentence_transformers; print('✓ SentenceTransformers installed')"

# 7. Test main application import
python -c "import sys; sys.path.append('.'); from main import app; print('✓ FastAPI app loads successfully')"
```

### Phase 3: Frontend Setup (Critical Fixes Applied)

```bash
# 1. Navigate to frontend directory
cd ../frontend

# 2. Install dependencies with legacy peer deps (required for compatibility)
npm install --legacy-peer-deps

# 3. Apply TypeScript fixes (these issues were discovered and fixed)
# Note: These fixes are already applied in the codebase:
# - JobStatus type definitions corrected
# - vis-network TypeScript compatibility added
# - Chip key prop conflicts resolved

# 4. Test build process
npm run build

# Expected output: "Compiled with warnings" (warnings are non-critical)
# Build size should be ~295KB gzipped

# 5. Verify build artifacts
ls -la build/static/js/  # Should contain main.[hash].js
ls -la build/static/css/ # Should contain main.[hash].css
```

### Phase 4: Database Setup

#### Option 1: Docker Neo4j (Recommended)

```bash
# 1. Install Docker if not present
# Windows: winget install Docker.DockerDesktop
# Linux: sudo apt install docker.io docker-compose -y
# macOS: brew install docker docker-compose

# 2. Start Neo4j container
docker run -d \
  --name neo4j-codeanalysis \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/codeanalysis123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j_data:/data \
  neo4j:5.15

# 3. Verify Neo4j is running
curl http://localhost:7474
```

#### Option 2: Local Neo4j Installation

```bash
# Download and install Neo4j Community Edition from neo4j.com
# Default credentials: neo4j/neo4j (change on first login)
```

### Phase 5: AWS Bedrock Setup (If Required)

If you only have access to AWS Bedrock (no direct OpenAI/Anthropic keys):

```bash
# 1. Install AWS CLI and configure
pip install awscli boto3
aws configure  # Enter your AWS credentials

# 2. Install LiteLLM proxy
pip install litellm[proxy]

# 3. Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# 4. Start Bedrock proxy
litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

# 5. Update backend configuration
# Set OPENAI_API_BASE=http://localhost:8001/v1 in .env
```

### Phase 6: Configuration

#### Backend Configuration (.env)

```bash
# Create backend/.env file
cd backend
cat > .env << EOF
# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# AI Configuration
OPENAI_API_KEY=your-key-here
# OR for Bedrock:
# OPENAI_API_BASE=http://localhost:8001/v1
# OPENAI_API_KEY=bedrock-proxy

# Repository Configuration
GITHUB_TOKEN=your-github-token
REPOSITORY_BASE_PATH=./repositories

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
EOF
```

#### Frontend Configuration (.env.local)

```bash
# Create frontend/.env.local file
cd ../frontend
cat > .env.local << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
EOF
```

### Phase 7: Startup and Verification

#### Start Backend Services

```bash
# 1. Start backend server
cd backend
python -c "import sys; sys.path.append('.')" # Verify path
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# INFO:     Started server process
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Start Frontend (Development)

```bash
# In new terminal/tab
cd frontend
npm start

# Expected output:
# webpack compiled with warnings
# Local:            http://localhost:3000
# On Your Network:  http://192.168.x.x:3000
```

#### Start Frontend (Production)

```bash
# Build for production
npm run build

# Serve with static server
npx serve -s build -l 3000
```

### Phase 8: System Verification

#### Backend Health Check

```bash
# Test API endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/repositories

# Expected responses should show status: "healthy"
```

#### Frontend Verification

1. Open browser to `http://localhost:3000`
2. Verify dashboard loads without errors
3. Check browser console for JavaScript errors
4. Test navigation between pages

#### Integration Test

```bash
# Test repository discovery
curl -X POST http://localhost:8000/api/v1/repositories/discover \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/your-org/test-repo"}'

# Test semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "payment processing", "max_results": 10}'
```

## 🐛 Common Issues and Solutions

### Backend Issues

**Import Error: "No module named 'graphiti_core.entities'"**
```bash
# Solution: Update imports (already fixed in codebase)
# The fix changes: from graphiti_core.entities import Entity
# To: Using base classes without specific Entity import
```

**PyTorch Installation Issues**
```bash
# Solution: Install with specific index URL
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**FastAPI App Won't Start**
```bash
# Solution: Check import paths
cd backend
python -c "import sys; sys.path.append('.'); from main import app"
```

### Frontend Issues

**npm install fails with ERESOLVE errors**
```bash
# Solution: Use legacy peer deps
npm install --legacy-peer-deps
```

**Build fails with "Cannot find module 'ajv/dist/compile/codegen'"**
```bash
# Solution: Install specific AJV version (already fixed)
npm install ajv@8.12.0 --legacy-peer-deps
```

**TypeScript errors with vis-network**
```bash
# Solution: TypeScript ignore comments added (already fixed)
# @ts-ignore imports are used for vis-network components
```

**Chip key prop conflicts**
```bash
# Solution: Destructure getTagProps properly (already fixed in codebase)
const { key, ...chipProps } = getTagProps({ index });
```

### Database Issues

**Neo4j Connection Refused**
```bash
# Check if Neo4j is running
docker ps | grep neo4j
# OR
sudo systemctl status neo4j

# Restart if needed
docker restart neo4j-codeanalysis
```

**Authentication Failed**
```bash
# Reset Neo4j password
docker exec -it neo4j-codeanalysis cypher-shell -u neo4j -p neo4j
# Change password: CALL dbms.changePassword('newpassword');
```

## 🔒 Security Considerations

### Production Deployment

1. **Environment Variables**: Never commit .env files
2. **API Keys**: Use secrets management (AWS Secrets Manager, etc.)
3. **Network Security**: Configure firewall rules
4. **HTTPS**: Use reverse proxy with SSL certificates
5. **Authentication**: Implement proper user authentication

### Docker Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps
```

## 📊 Performance Optimization

### Hardware Optimization

1. **GPU Acceleration**: Enable CUDA for PyTorch if available
2. **Memory**: Allocate sufficient RAM for large repositories
3. **Storage**: Use SSD for repository storage and databases
4. **Network**: High-bandwidth connection for repository cloning

### Software Optimization

1. **Python**: Use Python 3.11 for performance improvements
2. **Node.js**: Use Node.js 18+ for better memory management
3. **Database**: Configure Neo4j memory settings
4. **Caching**: Enable Redis for API response caching

## 🆘 Support and Troubleshooting

### Log Locations

- **Backend Logs**: `backend/logs/application.log`
- **Frontend Logs**: Browser console
- **Neo4j Logs**: Docker logs or `/var/log/neo4j/`
- **System Logs**: `/var/log/` (Linux) or Event Viewer (Windows)

### Debug Mode

```bash
# Enable debug mode for detailed logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services with verbose output
uvicorn main:app --log-level debug
```

### Health Monitoring

```bash
# Monitor system resources
htop  # Linux/macOS
taskmgr  # Windows

# Monitor application health
curl http://localhost:8000/api/v1/health?detailed=true
```

This deployment guide incorporates all verified fixes and provides comprehensive instructions for successful deployment on any target machine.