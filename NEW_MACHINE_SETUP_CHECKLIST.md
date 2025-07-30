# 🚀 CodeAnalysis MultiAgent MVP - New Machine Setup Checklist

## 📋 **CRITICAL ISSUES FOUND & FIXES NEEDED**

### 🔴 **HIGH PRIORITY - MUST FIX BEFORE DEPLOYMENT**

#### 1. **Backend Environment Configuration Mismatch**
**Issue**: Backend `.env` is configured for demo mode, not Bedrock
**Current**: `AWS_BEDROCK_PROXY=false`, missing Bedrock config
**Fix Required**: Update `backend/.env` for Bedrock integration

#### 2. **Frontend API URL Mismatch** 
**Issue**: Frontend points to port 8001, backend runs on 8000
**Current**: `REACT_APP_API_URL=http://localhost:8001`
**Fix Required**: Should be `http://localhost:8000`

#### 3. **AWS Environment Variables Missing**
**Issue**: Setup script expects AWS credentials in environment
**Fix Required**: Export AWS credentials or modify script

#### 4. **Container Engine Detection**
**Issue**: Script detects Podman but validation expects Docker
**Fix Required**: Ensure consistent container engine usage

### 🟡 **MEDIUM PRIORITY - SHOULD FIX**

#### 5. **AWS Region Mismatch**
**Issue**: AWS CLI configured for us-east-2, app expects us-east-1
**Fix Required**: Align regions or make configurable

#### 6. **Missing Error Handling**
**Issue**: Some services may fail gracefully but not provide clear feedback
**Fix Required**: Enhanced error messages

## 🛠️ **IMMEDIATE FIXES TO APPLY**

### Fix 1: Update Backend Environment for Bedrock
```bash
# Update backend/.env
AWS_BEDROCK_PROXY=true
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=bedrock-proxy
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=gpt-4
```

### Fix 2: Update Frontend API URL
```bash
# Update frontend/.env.local
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
```

### Fix 3: Create Pre-Setup Script
```bash
# Create setup_environment.bat for Windows
set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID%
set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY%
set AWS_DEFAULT_REGION=us-east-1
```

## 📝 **NEW MACHINE SETUP PROCEDURE**

### **Phase 1: Prerequisites (5-10 minutes)**
1. **Install Python 3.11+**
   - Download from python.org
   - Add to PATH
   - Verify: `python --version`

2. **Install Node.js 18+**
   - Download from nodejs.org
   - Verify: `node --version` and `npm --version`

3. **Install Docker Desktop**
   - Download from docker.com
   - Start Docker Desktop
   - Verify: `docker --version`

4. **Install AWS CLI**
   - Download from AWS documentation
   - Verify: `aws --version`

5. **Install Git**
   - Download from git-scm.com
   - Verify: `git --version`

### **Phase 2: AWS Configuration (2-3 minutes)**
```bash
# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, us-east-1, json

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### **Phase 3: Project Setup (1-2 minutes)**
```bash
# Clone repository
git clone <your-repo-url>
cd codeanalysis-multiagent-mvp

# Apply critical fixes (see fixes above)
# Edit backend/.env and frontend/.env.local
```

### **Phase 4: Validation (1 minute)**
```bash
# Run Bedrock validation
python validate_bedrock_startup.py

# Should show all green checkmarks
```

### **Phase 5: Full Startup (5-10 minutes)**
```bash
# Run complete setup
python setup.py

# Or quick start if validation passed
python setup.py --quick
```

## 🔍 **VALIDATION CHECKLIST**

### **Before Running Setup:**
- [ ] Python 3.11+ installed and in PATH
- [ ] Node.js 18+ installed and in PATH  
- [ ] Docker Desktop running
- [ ] AWS CLI configured with valid credentials
- [ ] AWS Bedrock access confirmed (can list models)
- [ ] Git installed
- [ ] Repository cloned
- [ ] Backend `.env` updated for Bedrock
- [ ] Frontend `.env.local` updated with correct API URL

### **After Running Setup:**
- [ ] All containers started successfully
- [ ] Backend health check passes: http://localhost:8000/api/v1/health
- [ ] Frontend accessible: http://localhost:3000
- [ ] Neo4j browser accessible: http://localhost:7474
- [ ] Bedrock proxy accessible: http://localhost:8001/health
- [ ] No port conflicts reported

## 🚨 **COMMON FAILURE POINTS & SOLUTIONS**

### **Port Conflicts**
**Symptoms**: "Port already in use" errors
**Solution**: 
```bash
# Check what's using ports
netstat -ano | findstr ":8000\|:3000\|:7474\|:8001"

# Use aggressive cleanup
python setup.py --force-kill-ports --kill-port-processes
```

### **AWS Credentials Not Found**
**Symptoms**: "AWS credentials not configured"
**Solution**:
```bash
# Set environment variables
set AWS_ACCESS_KEY_ID=your-key-here
set AWS_SECRET_ACCESS_KEY=your-secret-here
set AWS_DEFAULT_REGION=us-east-1

# Or run aws configure again
```

### **Docker Not Running**
**Symptoms**: "Cannot connect to Docker daemon"
**Solution**: Start Docker Desktop and wait for it to be ready

### **Node Dependencies Fail**
**Symptoms**: ERESOLVE errors during npm install
**Solution**: 
```bash
cd frontend
npm install --legacy-peer-deps --force
```

### **Python Dependencies Fail**
**Symptoms**: PyTorch or transformers installation errors
**Solution**:
```bash
# Install PyTorch first
pip install torch --index-url https://download.pytorch.org/whl/cpu
# Then run setup
```

## 🎯 **SUCCESS INDICATORS**

### **Setup Complete When:**
1. **All containers running**: `docker ps` shows 5 containers
2. **Backend healthy**: GET http://localhost:8000/api/v1/health returns 200
3. **Frontend loads**: http://localhost:3000 shows dashboard
4. **Bedrock proxy works**: Can make test API call
5. **No error messages** in setup script output

### **Ready for Use When:**
- Dashboard shows system status as "Healthy"
- Can navigate between all frontend pages
- API documentation accessible at http://localhost:8000/docs
- Neo4j browser shows connected database

## 📞 **TROUBLESHOOTING CONTACTS**

If issues persist:
1. **Check logs**: `docker logs <container-name>`
2. **Run validation**: `python validate_bedrock_startup.py --verbose`
3. **Clean restart**: `python setup.py --teardown-only` then `python setup.py`
4. **Nuclear option**: `python setup.py --force-kill-ports --kill-port-processes --clean-volumes`

## ⏱️ **ESTIMATED TIMELINE**

- **Fresh Windows Machine**: 20-30 minutes total
- **Machine with Prerequisites**: 10-15 minutes total
- **Experienced User**: 5-10 minutes total

## 🎉 **POST-SETUP VERIFICATION**

Run this final check:
```bash
# Quick system test
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
curl http://localhost:8001/health

# All should return 200 OK
```

**SUCCESS**: You're ready to analyze Java code with AI! 🚀