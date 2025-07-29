# CodeAnalysis MultiAgent MVP - Troubleshooting Guide

This guide covers all verified issues and solutions discovered during deployment testing.

## 🔍 Quick Diagnostics

### Run System Check
```bash
# Comprehensive system diagnostic
python deploy.py --platform auto --mode development --skip-verification
```

### Check Service Status
```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Frontend status
curl http://localhost:3000

# Database connectivity
docker ps | grep neo4j
```

## 🐛 Backend Issues

### Python Import Errors

#### Issue: `ModuleNotFoundError: No module named 'graphiti_core.entities'`
**Root Cause**: Graphiti Core API changed in version 0.17.0+

**Solution**: Already fixed in codebase
```python
# Old (broken) import:
from graphiti_core.entities import Entity

# New (working) import:
# Entity classes are now implemented as regular Python classes
# No specific Entity base class import needed
```

**Verification**:
```bash
cd backend
python -c "from app.services.graphiti_service import GraphitiService; print('✅ Import successful')"
```

#### Issue: `ImportError: cannot import name 'Embedder' from 'graphiti_core.embedder'`
**Root Cause**: Embedder class renamed to EmbedderClient

**Solution**: Already fixed in codebase
```python
# Old (broken) import:
from graphiti_core.embedder import Embedder

# New (working) import:
from graphiti_core.embedder import EmbedderClient
```

#### Issue: `ModuleNotFoundError: No module named 'torch'`
**Root Cause**: PyTorch not installed or wrong installation method

**Solution**:
```bash
# Install PyTorch with specific CPU index URL
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cpu

# For GPU support (if CUDA available):
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

**Verification**:
```bash
python -c "import torch; print('PyTorch version:', torch.__version__)"
```

### FastAPI Application Issues

#### Issue: `ModuleNotFoundError: No module named 'app'`
**Root Cause**: Python path not set correctly

**Solution**:
```bash
# From backend directory:
cd backend
python -c "import sys; sys.path.append('.')"
python -c "from main import app; print('✅ App loads successfully')"

# OR use the startup script which handles this automatically:
./start_backend.sh  # Linux/macOS
start_backend.bat   # Windows
```

#### Issue: `ValueError: uri must be provided when graph_driver is None`
**Root Cause**: Graphiti requires Neo4j URI configuration

**Solution**: Ensure `.env` file has correct Neo4j settings:
```bash
# In backend/.env:
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123
```

### Dependency Issues

#### Issue: Long pip installation time or failures
**Root Cause**: Large ML libraries and dependency conflicts

**Solution**:
```bash
# Install in specific order (already implemented in deploy.py):
pip install --upgrade pip setuptools wheel
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers>=4.35.0
pip install sentence-transformers>=2.2.2
pip install graphiti-core>=0.17.0
pip install -r requirements.txt
```

## 🎨 Frontend Issues

### Node.js/npm Issues

#### Issue: `npm install` fails with ERESOLVE errors
**Root Cause**: Dependency version conflicts in Node.js ecosystem

**Solution**: Use legacy peer deps (already implemented)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### Issue: `Error: Cannot find module 'ajv/dist/compile/codegen'`
**Root Cause**: AJV version incompatibility with webpack

**Solution**: Install specific AJV version (already implemented)
```bash
npm install ajv@8.12.0 --legacy-peer-deps
```

**Verification**:
```bash
npm run build  # Should complete without module errors
```

### TypeScript Compilation Issues

#### Issue: `TS2345: Argument of type ... is not assignable to parameter of type 'Options'`
**Root Cause**: vis-network TypeScript definitions mismatch

**Solution**: TypeScript ignore comments (already implemented)
```typescript
// @ts-ignore
import { Network } from 'vis-network';
// @ts-ignore  
import { DataSet } from 'vis-data';
```

#### Issue: `TS2367: This comparison appears to be unintentional`
**Root Cause**: JobStatus type definition incorrect

**Solution**: Union type instead of interface (already fixed)
```typescript
// Old (broken):
export interface JobStatus {
  PENDING: 'pending';
  // ...
}

// New (working):
export type JobStatus = 'pending' | 'started' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
```

#### Issue: `TS2783: 'key' is specified more than once`
**Root Cause**: MUI Autocomplete getTagProps returns key that conflicts with React key

**Solution**: Destructure properly (already fixed)
```typescript
// Old (broken):
<Chip key={index} {...getTagProps({ index })} />

// New (working):
const { key, ...chipProps } = getTagProps({ index });
return <Chip key={key} {...chipProps} />;
```

### Build Issues

#### Issue: Build succeeds but with warnings
**Status**: Normal behavior - warnings are non-critical

**Warnings you can ignore**:
- `'isMobile' is assigned a value but never used`
- `React Hook useEffect has a missing dependency`
- Various unused imports

**Critical errors that need fixing**:
- Module not found errors
- TypeScript compilation errors
- Syntax errors

## 🗄️ Database Issues

### Neo4j Connection Issues

#### Issue: Connection refused to Neo4j
**Root Cause**: Neo4j not running or wrong connection parameters

**Solution**:
```bash
# Check if Neo4j container is running
docker ps | grep neo4j

# Start existing container
docker start neo4j-codeanalysis

# Create new container if needed
docker run -d \
  --name neo4j-codeanalysis \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/codeanalysis123 \
  neo4j:5.15

# Test connection
curl http://localhost:7474
```

#### Issue: Authentication failed
**Root Cause**: Wrong Neo4j credentials

**Solution**:
```bash
# Reset password using cypher-shell
docker exec -it neo4j-codeanalysis cypher-shell
# At prompt: CALL dbms.changePassword('newpassword');

# Or recreate container with known password
docker rm -f neo4j-codeanalysis
# Then run the docker create command above
```

### Neo4j Memory Issues

#### Issue: Neo4j out of memory errors
**Root Cause**: Default memory settings too low for large datasets

**Solution**:
```bash
# Create Neo4j with custom memory settings
docker run -d \
  --name neo4j-codeanalysis \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/codeanalysis123 \
  -e NEO4J_dbms_memory_heap_initial__size=2G \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  neo4j:5.15
```

## ☁️ AWS Bedrock Issues

### Bedrock Authentication

#### Issue: `NoCredentialsError: Unable to locate credentials`
**Root Cause**: AWS credentials not configured

**Solution**:
```bash
# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret, Region, and output format

# Test credentials
aws sts get-caller-identity
```

#### Issue: `AccessDeniedException` when calling Bedrock
**Root Cause**: IAM permissions insufficient

**Solution**: Ensure your AWS user/role has these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

### LiteLLM Proxy Issues

#### Issue: `ModuleNotFoundError: No module named 'litellm'`
**Root Cause**: LiteLLM not installed

**Solution**:
```bash
pip install litellm[proxy] boto3
```

#### Issue: LiteLLM proxy connection refused
**Root Cause**: Proxy not started or wrong port

**Solution**:
```bash
# Start proxy on correct port
python -m litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

# Update backend/.env
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=bedrock-proxy
```

## 🖥️ System Resource Issues

### Memory Issues

#### Issue: System runs out of memory during analysis
**Root Cause**: Large repositories + ML models exceed available RAM

**Solution**:
```bash
# Monitor memory usage
htop  # Linux/macOS
taskmgr  # Windows

# Reduce batch sizes in configuration
# Edit backend/.env:
CODEBERT_BATCH_SIZE=8  # Reduce from default 32
MAX_CONCURRENT_REPOS=2  # Reduce from default 5
```

### Storage Issues

#### Issue: Disk space full during repository cloning
**Root Cause**: Large repositories consume significant space

**Solution**:
```bash
# Check disk usage
df -h  # Linux/macOS
dir  # Windows

# Clean up old repositories
rm -rf backend/repositories/*  # WARNING: Removes all cloned repos

# Set up disk monitoring
# Add to backend/.env:
MAX_REPO_SIZE_GB=5
CLEANUP_OLD_REPOS=true
```

### CPU Performance Issues

#### Issue: Analysis takes extremely long time
**Root Cause**: CPU-intensive ML operations on limited hardware

**Solution**:
```bash
# Enable GPU acceleration if available
# Install GPU version of PyTorch:
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability:
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Optimize CPU usage in backend/.env:
WORKERS=4  # Set to number of CPU cores
TORCH_NUM_THREADS=4
```

## 🌐 Network Issues

### GitHub Access Issues

#### Issue: Repository cloning fails with authentication errors
**Root Cause**: GitHub token not configured or insufficient permissions

**Solution**:
```bash
# Generate GitHub personal access token with repo permissions
# Add to backend/.env:
GITHUB_TOKEN=ghp_your_token_here

# For enterprise GitHub:
GITHUB_BASE_URL=https://github.company.com/api/v3
```

#### Issue: Rate limiting when cloning multiple repositories
**Root Cause**: GitHub API rate limits

**Solution**:
```bash
# Add delays between requests in backend/.env:
GITHUB_REQUEST_DELAY=1  # Seconds between requests
MAX_CONCURRENT_CLONES=3  # Reduce concurrent operations
```

### Firewall Issues

#### Issue: Services can't communicate (frontend can't reach backend)
**Root Cause**: Firewall blocking local ports

**Solution**:
```bash
# Windows Firewall
netsh advfirewall firewall add rule name="CodeAnalysis Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="CodeAnalysis Frontend" dir=in action=allow protocol=TCP localport=3000

# Linux iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT

# macOS
# Usually no action needed, check System Preferences > Security & Privacy > Firewall
```

## 🔧 Development vs Production Issues

### Development Mode Issues

#### Issue: Hot reload not working
**Root Cause**: File system monitoring issues

**Solution**:
```bash
# Increase file watcher limit (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Restart development servers
npm start  # Frontend
python -m uvicorn main:app --reload  # Backend
```

### Production Mode Issues

#### Issue: Static files not served correctly
**Root Cause**: Build output not configured properly

**Solution**:
```bash
# Verify frontend build
cd frontend
npm run build
ls -la build/  # Should contain static/ directory

# Serve with proper static server
npx serve -s build -l 3000
```

#### Issue: API calls fail in production
**Root Cause**: Environment variables not set correctly

**Solution**:
```bash
# Check frontend/.env.local
REACT_APP_API_URL=http://your-backend-domain:8000

# For same-host deployment:
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Performance Monitoring

### System Monitoring

```bash
# Monitor system resources
htop  # Linux/macOS
taskmgr  # Windows

# Monitor disk I/O
iotop  # Linux
iostat  # Linux/macOS

# Monitor network
netstat -an | grep :8000  # Check backend port
netstat -an | grep :3000  # Check frontend port
```

### Application Monitoring

```bash
# Backend health with details
curl "http://localhost:8000/api/v1/health?detailed=true"

# Check logs
tail -f backend/logs/application.log

# Monitor database
docker logs neo4j-codeanalysis
```

## 🆘 Getting Help

### Debug Mode

Enable verbose logging:
```bash
# Backend debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Frontend debug mode
REACT_APP_DEBUG=true npm start
```

### Log Collection

```bash
# Collect all relevant logs
mkdir debug_logs
cp backend/logs/* debug_logs/
docker logs neo4j-codeanalysis > debug_logs/neo4j.log
npm run build 2>&1 | tee debug_logs/frontend_build.log
```

### System Information

```bash
# Collect system information
python --version > debug_logs/system_info.txt
node --version >> debug_logs/system_info.txt
docker --version >> debug_logs/system_info.txt
pip list > debug_logs/pip_packages.txt
npm list > debug_logs/npm_packages.txt
```

This troubleshooting guide covers all verified issues encountered during deployment testing. Most issues have been preemptively fixed in the codebase and deployment scripts.