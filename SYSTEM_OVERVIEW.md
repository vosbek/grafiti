# CodeAnalysis MultiAgent MVP - System Overview

## 🚀 **Universal Deployment Commands**

```bash
# Complete setup with AWS Bedrock validation
python setup.py

# Quick start (skip validation for faster startup)
python setup.py --quick

# Aggressive cleanup (handles port conflicts)
python setup.py --force-kill-ports --kill-port-processes

# Complete teardown
python setup.py --teardown-only --clean-volumes
```

## 🏗️ **Production Architecture**

### **Service Topology**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   LiteLLM       │
│   React TS      │◄──►│   FastAPI       │◄──►│   Bedrock       │
│   Port: 3000    │    │   Port: 8000    │    │   Proxy: 8001   │
│   Material-UI   │    │   Async/Await   │    │   OpenAI API    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │     Neo4j       │    │  AWS Bedrock    │
         │              │   Port: 7687    │    │  Claude 3       │
         │              │   APOC Plugins  │    │  Sonnet         │
         │              └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         └─────────────►│     Redis       │
                        │   Port: 6379    │
                        │   Embeddings    │
                        │   Cache         │
                        └─────────────────┘
```

## 🔧 **Service Details**

### **Frontend Dashboard (React TypeScript)**
- **Purpose**: Enterprise web interface for code analysis
- **Port**: 3000 (configurable)
- **Technology**: React 18.2 + TypeScript 5.3 + Material-UI 5.15
- **Key Features**:
  - 📊 System health monitoring dashboard
  - 📁 Repository management with Git integration
  - 🔍 Semantic code search interface
  - 🤖 Multi-agent execution controls
  - 📈 Analysis results visualization
  - 🌐 Network graph relationships
  - ⚙️ Configuration management

### **Backend API (FastAPI)**
- **Purpose**: Core application logic and API services
- **Port**: 8000 (configurable)
- **Technology**: Python 3.11 + FastAPI + Async/Await
- **Key Services**:
  - 🔍 **Java Parser Service**: AST analysis with Struts/CORBA detection
  - 🧠 **CodeBERT Service**: Semantic embeddings with GPU optimization
  - 📊 **Graphiti Service**: Knowledge graph with temporal relationships
  - 📁 **Repository Service**: Git cloning and dependency discovery
  - 🏥 **Health Service**: Comprehensive system monitoring

### **LiteLLM Bedrock Proxy**
- **Purpose**: OpenAI-compatible API for AWS Bedrock
- **Port**: 8001 (configurable)
- **Technology**: LiteLLM proxy with AWS SDK
- **Features**:
  - 🔄 OpenAI API format translation
  - 🔐 AWS credential management
  - 📊 Request/response logging
  - ⚡ Connection pooling

### **Neo4j Knowledge Graph**
- **Purpose**: Temporal knowledge graph storage
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Technology**: Neo4j 5.15 with APOC plugins
- **Data Model**:
  - 📦 Java classes, methods, fields
  - 🔗 Inheritance and dependency relationships
  - 📋 Business rules and logic patterns
  - ⏰ Temporal relationship tracking

### **Redis Cache**
- **Purpose**: High-performance caching layer
- **Port**: 6379 (configurable)
- **Technology**: Redis 7-alpine
- **Cached Data**:
  - 🧠 CodeBERT embeddings
  - 📊 Analysis results
  - 🔍 Search query results
  - 📈 Performance metrics
  - Network graphs for code relationships
  - Real-time analysis progress tracking

### Backend (FastAPI Python)
- **Purpose**: Core analysis engine and API server
- **Port**: 8000
- **Key Services**:
  - **Java Parser Service**: AST parsing and code analysis
  - **CodeBERT Service**: Semantic embeddings generation
  - **Graphiti Service**: Knowledge graph management
  - **Repository Service**: Git repository management
  - **Multi-Agent System**: 8 specialized analysis agents

### AWS Bedrock Proxy (LiteLLM)
- **Purpose**: OpenAI-compatible proxy for AWS Bedrock
- **Port**: 8001
- **Models**: Claude 3 Sonnet (primary), Claude 3 Haiku (fallback)
- **Authentication**: AWS credentials + LiteLLM master key

### Neo4j Graph Database
- **Purpose**: Temporal knowledge graph storage
- **Ports**: 7687 (Bolt), 7474 (HTTP Browser)
- **Credentials**: neo4j / codeanalysis123
- **Key Entities**: JavaClass, JavaMethod, BusinessRule, StrutsAction, CORBAInterface

### Redis Cache
- **Purpose**: Caching for embeddings and analysis results
- **Port**: 6379
- **Configuration**: Persistent storage enabled

## 🔗 API Endpoints

### Health & Monitoring
- `GET /` - System information
- `GET /api/v1/health` - Health check
- `GET /system/info` - Detailed system information

### Repository Management
- `POST /api/v1/repositories/discover` - Discover repository dependencies
- `POST /api/v1/repositories/clone` - Clone repositories
- `GET /api/v1/repositories/list` - List managed repositories
- `DELETE /api/v1/repositories/{repo_id}` - Remove repository

### Code Analysis
- `POST /api/v1/analysis/comprehensive` - Full repository analysis
- `POST /api/v1/analysis/incremental` - Incremental analysis
- `GET /api/v1/analysis/results/{analysis_id}` - Get analysis results
- `GET /api/v1/analysis/status/{analysis_id}` - Get analysis status

### Semantic Search
- `POST /api/v1/search/semantic` - Natural language code search
- `POST /api/v1/search/similarity` - Code similarity search
- `GET /api/v1/search/entities/{entity_type}` - Search by entity type

### Multi-Agent System
- `GET /api/v1/agents/list` - List available agents
- `POST /api/v1/agents/{agent_name}/execute` - Execute specific agent
- `GET /api/v1/agents/{agent_name}/status` - Get agent execution status

## 🔐 Authentication & Security

### Default Credentials
- **Neo4j**: `neo4j` / `codeanalysis123`
- **LiteLLM Master Key**: `sk-bedrock-proxy-key`
- **AWS**: Uses your configured AWS credentials

### Security Features
- CORS middleware for cross-origin requests
- Request/response compression
- Structured logging with audit trails
- Container isolation
- Environment-based configuration

## 🎯 Multi-Agent Analysis System

### 8 Specialized Agents

1. **Architecture Analyzer**
   - System design patterns analysis
   - Layer violation detection
   - Dependency architecture mapping

2. **Security Analyzer**
   - Vulnerability detection
   - Security pattern analysis
   - Compliance checking

3. **Legacy Code Detector**
   - Technical debt identification
   - Modernization opportunity analysis
   - Framework migration planning

4. **Performance Analyzer**
   - Bottleneck identification
   - Performance pattern analysis
   - Optimization recommendations

5. **Dependency Analyzer**
   - Library usage analysis
   - Update recommendations
   - Dependency conflict detection

6. **Business Logic Extractor**
   - Business rule identification
   - Workflow analysis
   - Decision point mapping

7. **Struts Framework Analyzer**
   - Struts 1.x/2.x pattern analysis
   - Action mapping analysis
   - Migration path recommendations

8. **CORBA Interface Analyzer**
   - Distributed system analysis
   - Interface dependency mapping
   - Service interaction patterns

## 📊 Data Flow

### Repository Analysis Workflow
1. **Repository Discovery**: Scan for Maven/Gradle dependencies
2. **Code Parsing**: Generate Java AST for all files
3. **Semantic Analysis**: Create CodeBERT embeddings
4. **Knowledge Graph**: Store entities and relationships in Neo4j
5. **Multi-Agent Analysis**: Execute specialized analysis agents
6. **Result Aggregation**: Combine insights from all agents
7. **Visualization**: Present results in web dashboard

### Knowledge Graph Entities
- **JavaClass**: Classes, interfaces, enums with metadata
- **JavaMethod**: Methods with complexity metrics
- **BusinessRule**: Extracted business logic and rules
- **StrutsAction**: Struts action mappings and configurations
- **CORBAInterface**: CORBA interface definitions and operations

### Relationships
- **EXTENDS**: Class inheritance
- **IMPLEMENTS**: Interface implementation
- **CALLS**: Method invocation
- **CONTAINS**: Containment relationships
- **DEPENDS_ON**: Dependency relationships
- **EXTRACTED_FROM**: Business rule sources

## 🛠️ Development & Operations

### Container Management
```bash
# View running containers
docker ps  # or podman ps

# View logs
docker logs codeanalysis-backend
docker logs bedrock-proxy
docker logs neo4j-codeanalysis

# Restart specific service
docker restart codeanalysis-backend

# Access container shell
docker exec -it codeanalysis-backend bash
```

### Database Management
```bash
# Access Neo4j browser
open http://localhost:7474

# Connect with credentials: neo4j / codeanalysis123

# Sample Cypher queries
MATCH (n:JavaClass) RETURN count(n)
MATCH (n:BusinessRule) RETURN n.name, n.priority
MATCH (c:JavaClass)-[:CALLS]->(m:JavaMethod) RETURN c.name, m.name
```

### Monitoring & Debugging
```bash
# Check service health
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health

# Test Bedrock integration
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-proxy-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'

# View system information
curl http://localhost:8000/system/info
```

## 🚨 Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   ```bash
   aws configure
   # or set environment variables:
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   ```

2. **Bedrock Access Denied**
   - Ensure your AWS account has Bedrock access
   - Check IAM permissions for Bedrock service
   - Verify model access in AWS console

3. **Container Startup Failures**
   ```bash
   # Check container logs
   docker logs <container-name>
   
   # Restart with fresh state
   python setup.py --teardown-only
   python setup.py
   ```

4. **Port Conflicts**
   - Default ports: 3000, 7474, 7687, 6379, 8000, 8001
   - Modify ports in configuration files if needed

5. **Memory Issues**
   - Minimum 8GB RAM recommended
   - Adjust Neo4j memory settings in docker-compose
   - Reduce CodeBERT batch size in environment

### Performance Optimization

1. **For Large Repositories (1M+ lines)**
   - Increase Neo4j heap size
   - Enable GPU acceleration for CodeBERT
   - Adjust concurrent processing limits

2. **For Multiple Repositories**
   - Use Redis caching effectively
   - Implement incremental analysis
   - Monitor disk space usage

## 📈 Scaling Considerations

### Horizontal Scaling
- Backend can be scaled with multiple instances
- Neo4j clustering for high availability
- Redis clustering for cache distribution

### Performance Tuning
- CodeBERT batch size optimization
- Neo4j memory configuration
- Concurrent repository processing limits

### Enterprise Deployment
- Kubernetes manifests available
- Prometheus monitoring integration
- Grafana dashboards for visualization

## 🎉 Success Metrics

After successful setup, you should see:
- ✅ All 5 services running and healthy
- ✅ Frontend accessible at http://localhost:3000
- ✅ Backend API responding at http://localhost:8000
- ✅ Neo4j browser accessible at http://localhost:7474
- ✅ Bedrock proxy responding at http://localhost:8001
- ✅ AWS Bedrock integration test passing

**Ready to analyze enterprise Java codebases with AI-powered insights!**