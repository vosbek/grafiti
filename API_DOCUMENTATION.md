# 📚 CodeAnalysis MultiAgent MVP - API Documentation

## 🚀 **Quick Start**

**Base URL**: `http://localhost:8000`
**API Version**: v1
**Authentication**: None (MVP version)

**Interactive Documentation**: http://localhost:8000/docs

## 🏥 **Health & System Endpoints**

### **GET /api/v1/health**
Basic health check for all system components.

```bash
curl http://localhost:8000/api/v1/health
```

**Response**:
```json
{
  "success": true,
  "status": "healthy",
  "services": {
    "graphiti": "healthy",
    "codebert": "healthy", 
    "repository": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **GET /api/v1/health/detailed**
Detailed health check with system metrics.

```bash
curl http://localhost:8000/api/v1/health/detailed
```

**Response**:
```json
{
  "success": true,
  "status": "healthy",
  "services": {...},
  "system": {
    "cpu": {"cpu_count": 8, "cpu_percent": 25.5},
    "memory": {"total": 17179869184, "percent": 45.2},
    "gpu": {"available": true, "device_count": 1}
  },
  "metrics": {
    "codebert": {"embeddings_generated": 1247, "cache_hit_rate": 0.85},
    "repositories": {"total_cloned": 5}
  }
}
```

## 📁 **Repository Management**

### **GET /api/v1/repositories**
List all managed repositories with filtering.

```bash
# List all repositories
curl http://localhost:8000/api/v1/repositories

# Filter by status and framework
curl "http://localhost:8000/api/v1/repositories?status=analyzed&framework=struts&limit=10"
```

**Query Parameters**:
- `status`: `cloned`, `analyzing`, `analyzed`, `error`
- `framework`: `struts`, `spring`, `corba`, `ejb`
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
  "success": true,
  "repositories": [
    {
      "id": "repo_1234",
      "name": "legacy-banking-app",
      "url": "https://github.com/company/legacy-banking-app.git",
      "status": "analyzed",
      "framework": "struts",
      "last_analyzed": "2024-01-15T09:15:00Z",
      "metrics": {
        "total_classes": 245,
        "total_methods": 1832,
        "struts_actions": 23,
        "business_rules": 45
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### **POST /api/v1/repositories/discover**
Discover repository dependencies from a starting repository.

```bash
curl -X POST http://localhost:8000/api/v1/repositories/discover \
  -H "Content-Type: application/json" \
  -d '{
    "starting_repository": "https://github.com/company/main-app.git",
    "max_depth": 3,
    "include_external": false
  }'
```

**Request Body**:
```json
{
  "starting_repository": "https://github.com/company/main-app.git",
  "max_depth": 3,
  "include_external": false,
  "frameworks": ["struts", "spring"]
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "discover_abc123",
  "status_url": "/api/v1/repositories/jobs/discover_abc123/status",
  "discovered_repositories": [
    "https://github.com/company/auth-service.git",
    "https://github.com/company/payment-service.git"
  ],
  "total_discovered": 15
}
```

### **POST /api/v1/repositories/clone**
Clone multiple repositories for analysis.

```bash
curl -X POST http://localhost:8000/api/v1/repositories/clone \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": [
      "https://github.com/company/app1.git",
      "https://github.com/company/app2.git"
    ],
    "analyze_immediately": true
  }'
```

**Request Body**:
```json
{
  "repositories": ["https://github.com/company/app1.git"],
  "analyze_immediately": true,
  "clone_depth": 1,
  "include_submodules": false
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "clone_def456",
  "status_url": "/api/v1/repositories/jobs/clone_def456/status",
  "cloned_repositories": [
    {
      "url": "https://github.com/company/app1.git",
      "status": "cloning",
      "local_path": "/workspace/app1"
    }
  ]
}
```

## 🔍 **Semantic Search**

### **POST /api/v1/search/semantic**
Perform semantic code search using natural language.

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "payment processing logic with validation",
    "repositories": ["legacy-banking-app"],
    "max_results": 10,
    "similarity_threshold": 0.7
  }'
```

**Request Body**:
```json
{
  "query": "payment processing logic with validation",
  "repositories": ["legacy-banking-app"],
  "max_results": 10,
  "similarity_threshold": 0.7,
  "filters": {
    "code_type": ["method", "class"],
    "framework": ["struts"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "query": "payment processing logic with validation",
  "results": [
    {
      "id": "method_payment_validate_123",
      "type": "method",
      "identifier": "com.bank.payment.PaymentProcessor.validatePayment",
      "similarity_score": 0.89,
      "source_code": "public boolean validatePayment(Payment payment) { ... }",
      "repository": "legacy-banking-app",
      "file_path": "src/main/java/com/bank/payment/PaymentProcessor.java",
      "line_number": 45,
      "metadata": {
        "is_struts_action": false,
        "complexity_score": 7.2,
        "business_rule": true
      }
    }
  ],
  "total_results": 8,
  "execution_time_ms": 234
}
```

### **GET /api/v1/search/suggestions**
Get search query suggestions based on analyzed code.

```bash
curl "http://localhost:8000/api/v1/search/suggestions?query=payment&limit=5"
```

**Response**:
```json
{
  "suggestions": [
    "payment processing logic",
    "payment validation methods",
    "payment gateway integration",
    "payment transaction handling",
    "payment security checks"
  ]
}
```

### **GET /api/v1/search/statistics**
Get search and analysis statistics.

```bash
curl http://localhost:8000/api/v1/search/statistics
```

**Response**:
```json
{
  "success": true,
  "statistics": {
    "total_repositories": 5,
    "total_classes": 1247,
    "total_methods": 8934,
    "total_embeddings": 10181,
    "struts_actions": 89,
    "corba_interfaces": 23,
    "business_rules": 156
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## 🤖 **Multi-Agent System**

### **GET /api/v1/agents**
List available analysis agents.

```bash
curl http://localhost:8000/api/v1/agents
```

**Response**:
```json
{
  "success": true,
  "agents": [
    {
      "name": "architecture-analyzer",
      "description": "Analyzes system architecture and design patterns",
      "capabilities": ["dependency_analysis", "pattern_detection"],
      "supported_frameworks": ["struts", "spring", "ejb"],
      "status": "available",
      "performance": {
        "success_rate": 0.94,
        "average_execution_time": 45.2
      }
    },
    {
      "name": "security-analyzer", 
      "description": "Identifies security vulnerabilities and risks",
      "capabilities": ["vulnerability_scan", "security_patterns"],
      "supported_frameworks": ["all"],
      "status": "available"
    }
  ]
}
```

### **POST /api/v1/agents/{agent_name}/execute**
Execute a specific analysis agent on repositories.

```bash
curl -X POST http://localhost:8000/api/v1/agents/architecture-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": ["legacy-banking-app"],
    "parameters": {
      "analysis_depth": "comprehensive",
      "include_dependencies": true
    }
  }'
```

**Request Body**:
```json
{
  "repositories": ["legacy-banking-app"],
  "parameters": {
    "analysis_depth": "comprehensive",
    "include_dependencies": true,
    "timeout": 300
  }
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "agent_exec_789",
  "agent_name": "architecture-analyzer",
  "status": "running",
  "status_url": "/api/v1/agents/jobs/agent_exec_789/status",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### **GET /api/v1/agents/jobs/{job_id}/status**
Check agent execution status and results.

```bash
curl http://localhost:8000/api/v1/agents/jobs/agent_exec_789/status
```

**Response**:
```json
{
  "success": true,
  "job_id": "agent_exec_789",
  "status": "completed",
  "agent_name": "architecture-analyzer",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:34:30Z",
  "results": {
    "architecture_patterns": [
      {
        "pattern": "MVC",
        "confidence": 0.92,
        "locations": ["com.bank.web.controller"]
      }
    ],
    "dependencies": [
      {
        "from": "PaymentController",
        "to": "PaymentService", 
        "type": "uses"
      }
    ],
    "recommendations": [
      "Consider refactoring large controller classes",
      "Implement dependency injection for better testability"
    ]
  }
}
```

## 📊 **Comprehensive Analysis**

### **POST /api/v1/analysis/comprehensive**
Start comprehensive analysis of repositories with all agents.

```bash
curl -X POST http://localhost:8000/api/v1/analysis/comprehensive \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": ["legacy-banking-app"],
    "agents": ["architecture-analyzer", "security-analyzer"],
    "generate_report": true
  }'
```

**Request Body**:
```json
{
  "repositories": ["legacy-banking-app"],
  "agents": ["architecture-analyzer", "security-analyzer", "migration-planner"],
  "generate_report": true,
  "report_format": "json",
  "include_code_samples": true
}
```

**Response**:
```json
{
  "success": true,
  "analysis_id": "comprehensive_xyz789",
  "job_id": "analysis_job_456",
  "status": "running",
  "status_url": "/api/v1/analysis/jobs/analysis_job_456/status",
  "results_url": "/api/v1/analysis/results/comprehensive_xyz789",
  "estimated_completion": "2024-01-15T11:00:00Z"
}
```

### **GET /api/v1/analysis/results/{analysis_id}**
Get comprehensive analysis results.

```bash
curl http://localhost:8000/api/v1/analysis/results/comprehensive_xyz789
```

**Response**:
```json
{
  "success": true,
  "analysis_id": "comprehensive_xyz789",
  "status": "completed",
  "repositories": ["legacy-banking-app"],
  "agents_executed": ["architecture-analyzer", "security-analyzer"],
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:55:30Z",
  "results": {
    "architecture": {
      "patterns_found": ["MVC", "DAO", "Factory"],
      "complexity_score": 7.2,
      "maintainability_index": 65
    },
    "security": {
      "vulnerabilities_found": 3,
      "risk_level": "medium",
      "recommendations": ["Update dependencies", "Add input validation"]
    },
    "summary": {
      "total_classes": 245,
      "total_methods": 1832,
      "business_rules": 45,
      "technical_debt_hours": 120
    }
  },
  "report_url": "/api/v1/analysis/results/comprehensive_xyz789/export?format=pdf"
}
```

## 🔄 **Job Management**

### **GET /api/v1/repositories/jobs/{job_id}/status**
Check status of repository operations.

```bash
curl http://localhost:8000/api/v1/repositories/jobs/clone_def456/status
```

**Response**:
```json
{
  "success": true,
  "job_id": "clone_def456",
  "type": "repository_clone",
  "status": "completed",
  "progress": 100,
  "started_at": "2024-01-15T10:20:00Z",
  "completed_at": "2024-01-15T10:25:30Z",
  "results": {
    "cloned_repositories": 3,
    "failed_repositories": 0,
    "total_size_mb": 245.7
  }
}
```

### **DELETE /api/v1/repositories/jobs/{job_id}**
Cancel a running job.

```bash
curl -X DELETE http://localhost:8000/api/v1/repositories/jobs/clone_def456
```

**Response**:
```json
{
  "success": true,
  "message": "Job clone_def456 cancelled successfully"
}
```

## 📈 **System Information**

### **GET /system/info**
Get detailed system information and metrics.

```bash
curl http://localhost:8000/system/info
```

**Response**:
```json
{
  "system": {
    "platform": "Windows-10-10.0.22621-SP0",
    "python_version": "3.11.9",
    "cpu_count": 8,
    "memory_total": 17179869184
  },
  "services": {
    "total_services": 4,
    "active_services": ["codebert", "graphiti", "repository"],
    "service_health": {
      "codebert": "healthy",
      "graphiti": "healthy", 
      "repository": "healthy"
    }
  },
  "environment": {
    "workspace_dir": "workspace",
    "use_gpu": "false",
    "codebert_model": "microsoft/codebert-base"
  }
}
```

## 🚨 **Error Handling**

### **Standard Error Response**
```json
{
  "success": false,
  "error": "Repository not found",
  "detail": "Repository with ID 'invalid_repo' does not exist",
  "status_code": 404,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **Common HTTP Status Codes**
- `200`: Success
- `201`: Created
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `422`: Validation Error (invalid request body)
- `500`: Internal Server Error
- `503`: Service Unavailable (system not ready)

## 🔧 **Rate Limiting & Performance**

### **Request Limits**
- **Search requests**: 100 per minute
- **Analysis requests**: 10 per minute  
- **Repository operations**: 5 per minute

### **Timeout Values**
- **Search queries**: 30 seconds
- **Agent execution**: 300 seconds (5 minutes)
- **Repository cloning**: 600 seconds (10 minutes)

### **Pagination**
Most list endpoints support pagination:
- `limit`: Maximum results per page (default: 50, max: 100)
- `offset`: Number of results to skip (default: 0)

## 🔍 **Advanced Usage Examples**

### **Batch Repository Analysis**
```bash
# 1. Discover dependencies
curl -X POST http://localhost:8000/api/v1/repositories/discover \
  -d '{"starting_repository": "https://github.com/company/main.git"}'

# 2. Clone discovered repositories  
curl -X POST http://localhost:8000/api/v1/repositories/clone \
  -d '{"repositories": ["repo1.git", "repo2.git"], "analyze_immediately": true}'

# 3. Run comprehensive analysis
curl -X POST http://localhost:8000/api/v1/analysis/comprehensive \
  -d '{"repositories": ["repo1", "repo2"], "agents": ["all"]}'
```

### **Semantic Search Workflow**
```bash
# 1. Get search suggestions
curl "http://localhost:8000/api/v1/search/suggestions?query=payment"

# 2. Perform semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -d '{"query": "payment processing with validation", "max_results": 20}'

# 3. Get detailed code analysis
curl -X POST http://localhost:8000/api/v1/agents/code-analyzer/execute \
  -d '{"code_identifiers": ["com.bank.PaymentProcessor.validate"]}'
```

## 📞 **Support & Troubleshooting**

### **Health Check Endpoints**
- `/api/v1/health` - Basic health check
- `/api/v1/health/detailed` - Detailed system status
- `/readiness` - Kubernetes readiness probe
- `/liveness` - Kubernetes liveness probe

### **Debug Information**
Add `?debug=true` to any endpoint for additional debug information in the response.

### **API Documentation**
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **ReDoc**: http://localhost:8000/redoc