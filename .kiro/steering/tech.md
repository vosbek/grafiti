# Technology Stack & Build System

## Architecture Overview
Full-stack application with Python FastAPI backend, React TypeScript frontend, and Neo4j knowledge graph database.

## Backend Stack
- **Framework**: FastAPI with async processing
- **Language**: Python 3.11+ (exact version tested: 3.11.9)
- **AI/ML**: 
  - CodeBERT embeddings (microsoft/codebert-base)
  - Transformers 4.35.0+
  - Sentence-transformers 2.2.2+
  - PyTorch 2.1.0+ (CPU/CUDA support)
- **Knowledge Graph**: Graphiti-core 0.17.0+ with Neo4j 5.15
- **Database**: Neo4j (primary), Redis (caching)
- **LLM Integration**: AWS Bedrock ONLY via LiteLLM proxy (no OpenAI)
- **Code Analysis**: Custom Java AST parser, GitPython
- **Server**: Uvicorn (development), Gunicorn (production)

## Frontend Stack
- **Framework**: React 18.2.0 with TypeScript 5.3.3+
- **UI Library**: Material-UI 5.15.10+ (@mui/material, @mui/icons-material)
- **Data Grid**: @mui/x-data-grid 6.19.4+
- **Visualization**: Recharts 2.12.0+, vis-network 9.1.9+
- **HTTP Client**: Axios 1.6.7+
- **Routing**: React Router DOM 6.22.0+
- **Build Tool**: Create React App (react-scripts 5.0.1)

## Database & Storage
- **Primary DB**: Neo4j 5.15 with APOC plugins
- **Caching**: Redis 7-alpine
- **File Storage**: Local filesystem for repositories and analysis results

## Infrastructure & Deployment
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose, Kubernetes manifests available
- **Reverse Proxy**: Nginx (production)
- **Monitoring**: Prometheus + Grafana (optional)

## Common Commands

### Development Setup
```bash
# SINGLE COMMAND SETUP (recommended)
python setup.py

# Quick start (skip validation)
python setup.py --quick

# Teardown everything
python setup.py --teardown-only
```

### Running Services
```bash
# Backend (development)
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (development)  
cd frontend && npm start

# Database (Docker)
docker run -d --name neo4j-codeanalysis -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/codeanalysis123 neo4j:5.15
```

### Production Deployment
```bash
# Complete production deployment
python deploy.py --platform auto --mode production

# Docker Compose
docker-compose -f docker-compose.verified.yml up -d

# With AWS Bedrock
docker-compose -f docker-compose.verified.yml --profile bedrock up -d
```

### Testing & Validation
```bash
# Comprehensive system validation
python validate_deployment.py --comprehensive

# Fix issues automatically
python validate_deployment.py --fix-issues

# Backend health check
curl http://localhost:8000/api/v1/health

# Frontend build
cd frontend && npm run build
```

## Build System Notes

### Critical Installation Order
1. Install PyTorch first (prevents dependency conflicts)
2. Install core ML dependencies (transformers, sentence-transformers, graphiti-core)
3. Install remaining requirements
4. Frontend: Use `--legacy-peer-deps` flag for npm install

### Platform-Specific Considerations
- **Windows**: Use `.bat` scripts, PowerShell commands
- **Linux/macOS**: Use `.sh` scripts, bash commands  
- **GPU Support**: Automatic detection, CUDA 11.8 compatible
- **Memory**: 8GB minimum, 16GB+ recommended for large repositories

### Environment Variables
```bash
# Backend (.env) - BEDROCK ONLY CONFIGURATION
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123
REDIS_URL=redis://localhost:6379

# AWS Bedrock Configuration (REQUIRED)
AWS_BEDROCK_PROXY=true
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=bedrock-proxy

# Application Settings
DEBUG=false
WORKERS=4

# Frontend (.env.local)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
```

### Known Build Issues & Fixes
- **TypeScript**: vis-network requires `@ts-ignore` for type compatibility
- **npm**: Use `--legacy-peer-deps` to resolve ERESOLVE errors
- **Docker**: Multi-stage builds with verified dependency installation order
- **Import Paths**: Backend uses relative imports with sys.path modifications
- **AWS Credentials**: Must be configured before running setup (`aws configure`)
- **Bedrock Access**: Requires AWS account with Bedrock service enabled