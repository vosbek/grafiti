# API Documentation

## Overview

The CodeAnalysis-MultiAgent-MVP provides a comprehensive REST API for enterprise Java code analysis. The API is built with FastAPI and provides OpenAPI/Swagger documentation at `/docs`.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, authentication is optional but can be enabled through environment variables:

```bash
export ENABLE_AUTH=true
export SECRET_KEY=your-secret-key
```

When enabled, include the authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Health Check

#### GET /health

Returns system health status and basic metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-07-25T18:00:00Z",
  "services": {
    "neo4j": "connected",
    "redis": "connected", 
    "codebert": "loaded",
    "agents": "ready"
  },
  "system": {
    "cpu_cores": 16,
    "memory_gb": 64,
    "gpu_available": true,
    "disk_space_gb": 500
  }
}
```

### Repository Management

#### POST /repositories/discover

Discover repository dependencies starting from a main repository.

**Request:**
```json
{
  "repository_url": "https://github.com/company/main-app.git",
  "max_depth": 3,
  "include_external": false,
  "analysis_config": {
    "frameworks": ["struts", "corba", "spring"],
    "skip_tests": true,
    "max_file_size_mb": 5.0
  }
}
```

**Response:**
```json
{
  "job_id": "discover_123456",
  "status": "started",
  "discovered_repositories": [],
  "estimated_completion": "2024-07-25T18:15:00Z",
  "progress_url": "/repositories/jobs/discover_123456/status"
}
```

#### POST /repositories/clone

Clone multiple repositories for analysis.

**Request:**
```json
{
  "repositories": [
    {
      "url": "https://github.com/company/repo1.git",
      "branch": "main",
      "priority": "high"
    },
    {
      "url": "https://github.com/company/repo2.git", 
      "branch": "develop",
      "priority": "medium"
    }
  ],
  "concurrent_clones": 5,
  "workspace_name": "enterprise_analysis"
}
```

**Response:**
```json
{
  "job_id": "clone_789012",
  "status": "in_progress",
  "total_repositories": 2,
  "cloned_repositories": 0,
  "failed_repositories": [],
  "progress_url": "/repositories/jobs/clone_789012/status"
}
```

#### GET /repositories

List all managed repositories with their analysis status.

**Query Parameters:**
- `status`: Filter by status (cloned, analyzing, completed, failed)
- `framework`: Filter by detected framework (struts, corba, spring, ejb)
- `limit`: Maximum number of results (default: 50)
- `offset`: Results offset for pagination (default: 0)

**Response:**
```json
{
  "repositories": [
    {
      "id": "repo_001",
      "name": "main-application",
      "url": "https://github.com/company/main-app.git",
      "local_path": "/workspace/main-application",
      "status": "completed",
      "frameworks": ["struts", "corba"],
      "statistics": {
        "java_files": 1245,
        "classes": 892,
        "methods": 5672,
        "struts_actions": 45,
        "corba_interfaces": 12,
        "business_rules": 78
      },
      "last_analyzed": "2024-07-25T17:30:00Z",
      "analysis_duration": 1847.5
    }
  ],
  "total": 1,
  "has_more": false
}
```

### Code Analysis

#### POST /analysis/comprehensive

Perform comprehensive multi-agent analysis on repositories.

**Request:**
```json
{
  "repositories": ["repo_001", "repo_002"],
  "analysis_type": "full",
  "agents": [
    "architecture_analyzer",
    "struts_legacy_agent", 
    "corba_integration_agent",
    "business_rules_extractor",
    "migration_planner"
  ],
  "query": "Analyze authentication and authorization patterns across applications",
  "context": {
    "focus_areas": ["security", "user_management"],
    "modernization_target": "spring_boot",
    "compliance_requirements": ["SOX", "PCI"]
  }
}
```

**Response:**
```json
{
  "analysis_id": "analysis_345678",
  "status": "started",
  "supervisor_plan": {
    "selected_agents": ["architecture_analyzer", "struts_legacy_agent", "business_rules_extractor"],
    "execution_order": ["architecture_analyzer", "struts_legacy_agent", "business_rules_extractor"],
    "estimated_duration": 300,
    "confidence_score": 0.92
  },
  "progress_url": "/analysis/345678/status",
  "results_url": "/analysis/345678/results"
}
```

#### GET /analysis/{analysis_id}/results

Retrieve comprehensive analysis results.

**Response:**
```json
{
  "analysis_id": "analysis_345678",
  "status": "completed",
  "completion_time": "2024-07-25T18:05:00Z",
  "supervisor_summary": "Found 15 authentication-related classes across 3 applications with mixed Spring Security and custom implementations.",
  "agent_results": {
    "architecture_analyzer": {
      "findings": [
        {
          "type": "architectural_pattern",
          "name": "Mixed Authentication Approaches",
          "description": "Applications use both Spring Security and custom Struts-based authentication",
          "impact": "high",
          "affected_components": ["UserService", "LoginAction", "SecurityFilter"],
          "recommendation": "Standardize on Spring Security across all applications"
        }
      ]
    },
    "struts_legacy_agent": {
      "findings": [
        {
          "type": "legacy_pattern", 
          "name": "Custom Struts Authentication",
          "description": "Custom authentication logic in Struts actions",
          "files": ["LoginAction.java", "AuthenticationInterceptor.java"],
          "complexity_score": 7.8,
          "migration_effort": "medium"
        }
      ]
    },
    "business_rules_extractor": {
      "rules": [
        {
          "name": "Password Complexity Rule",
          "type": "validation",
          "description": "Passwords must be 8+ characters with mixed case and numbers",
          "source_methods": ["UserService.validatePassword", "PasswordValidator.isValid"],
          "compliance": ["SOX"],
          "criticality": "high"
        }
      ]
    }
  },
  "synthesized_response": "The analysis reveals a fragmented authentication landscape...",
  "code_references": [
    {
      "file": "src/main/java/com/company/auth/UserService.java",
      "lines": [45, 67],
      "relevance_score": 0.95,
      "context": "Primary authentication service"
    }
  ],
  "relationships": [
    {
      "source": "LoginAction",
      "target": "UserService", 
      "type": "calls",
      "description": "Struts action delegates to service layer"
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "modernization",
      "title": "Migrate to Spring Security",
      "description": "Replace custom Struts authentication with Spring Security",
      "effort_estimate": "3-4 weeks",
      "risk_level": "medium"
    }
  ]
}
```

#### POST /analysis/impact

Analyze the impact of potential changes.

**Request:**
```json
{
  "change_type": "modernization",
  "target_components": ["LoginAction", "UserService"],
  "proposed_changes": [
    {
      "component": "LoginAction",
      "change": "replace_with_spring_controller",
      "details": "Convert Struts action to Spring REST controller"
    }
  ],
  "scope": "cross_repository"
}
```

### Semantic Search

#### POST /search/semantic

Perform semantic search across all analyzed code.

**Request:**
```json
{
  "query": "Find all payment processing logic",
  "filters": {
    "repositories": ["repo_001", "repo_002"],
    "entity_types": ["class", "method", "business_rule"],
    "frameworks": ["struts"],
    "complexity_min": 5.0
  },
  "options": {
    "max_results": 20,
    "similarity_threshold": 0.7,
    "include_context": true,
    "highlight_matches": true
  }
}
```

**Response:**
```json
{
  "query": "Find all payment processing logic",
  "results": [
    {
      "entity": {
        "type": "class",
        "name": "PaymentProcessor",
        "qualified_name": "com.company.payment.PaymentProcessor",
        "repository": "main-application",
        "file_path": "src/main/java/com/company/payment/PaymentProcessor.java"
      },
      "similarity_score": 0.94,
      "relevance_score": 0.91,
      "context": {
        "methods": ["processPayment", "validateCard", "calculateFees"],
        "business_rules": ["Payment Validation Rule", "Fee Calculation Rule"],
        "relationships": ["calls CardValidator", "implements PaymentInterface"]
      },
      "highlights": [
        "Processes credit card payments through multiple gateways",
        "Validates payment amounts and customer data",
        "Calculates transaction fees based on business rules"
      ]
    }
  ],
  "total_matches": 15,
  "execution_time": 0.234,
  "suggestions": [
    "payment gateway integration",
    "credit card validation", 
    "transaction processing"
  ]
}
```

#### POST /search/relationships

Find relationships between code entities.

**Request:**
```json
{
  "entity": "com.company.auth.UserService",
  "relationship_types": ["calls", "implements", "extends", "uses"],
  "direction": "both",
  "max_depth": 3,
  "include_indirect": true
}
```

**Response:**
```json
{
  "entity": "com.company.auth.UserService",
  "relationships": {
    "direct": [
      {
        "target": "com.company.dao.UserDAO",
        "type": "calls",
        "description": "UserService calls UserDAO for database operations",
        "frequency": "high",
        "strength": 0.89
      }
    ],
    "indirect": [
      {
        "path": ["UserService", "UserDAO", "DatabaseConnection"],
        "description": "UserService indirectly depends on DatabaseConnection through UserDAO"
      }
    ]
  },
  "dependency_graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

### Agent Management

#### GET /agents

List available analysis agents and their capabilities.

**Response:**
```json
{
  "agents": [
    {
      "name": "architecture_analyzer",
      "description": "Analyzes application architecture and identifies patterns",
      "capabilities": [
        "architectural_pattern_detection", 
        "layer_analysis",
        "component_relationships"
      ],
      "frameworks": ["all"],
      "status": "ready",
      "last_execution": "2024-07-25T17:45:00Z",
      "success_rate": 0.96
    },
    {
      "name": "struts_legacy_agent",
      "description": "Specialized analysis of Struts applications",
      "capabilities": [
        "action_mapping_analysis",
        "form_bean_detection", 
        "jsp_flow_analysis",
        "migration_recommendations"
      ],
      "frameworks": ["struts"],
      "status": "ready",
      "last_execution": "2024-07-25T17:30:00Z",
      "success_rate": 0.92
    }
  ]
}
```

#### POST /agents/execute

Execute a specific agent with custom parameters.

**Request:**
```json
{
  "agent_name": "business_rules_extractor",
  "repositories": ["repo_001"],
  "parameters": {
    "rule_types": ["validation", "calculation"],
    "confidence_threshold": 0.8,
    "include_comments": true
  },
  "context": {
    "domain": "financial_services",
    "compliance_focus": "SOX"
  }
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "error": "ValidationError",
  "message": "Repository URL is required",
  "details": {
    "field": "repository_url",
    "code": "missing_required_field"
  },
  "timestamp": "2024-07-25T18:00:00Z",
  "request_id": "req_123456"
}
```

### Status Codes

- `200` - Success
- `202` - Accepted (for async operations)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

API endpoints are rate limited to ensure fair usage:

- Authentication endpoints: 10 requests per minute
- Repository operations: 50 requests per hour
- Analysis operations: 20 concurrent analyses
- Search operations: 100 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1627234567
```

## Webhooks

Configure webhooks to receive notifications about analysis completion:

#### POST /webhooks

```json
{
  "url": "https://your-app.com/webhooks/analysis",
  "events": ["analysis.completed", "analysis.failed"],
  "secret": "webhook_secret_key"
}
```

Webhook payload example:

```json
{
  "event": "analysis.completed",
  "analysis_id": "analysis_345678",
  "timestamp": "2024-07-25T18:05:00Z",
  "data": {
    "status": "completed",
    "duration": 298.5,
    "findings_count": 47,
    "repositories_analyzed": 3
  }
}
```

## SDK and Client Libraries

Official SDKs are available for:

- **Python**: `pip install codeanalysis-client`
- **JavaScript/TypeScript**: `npm install @company/codeanalysis-client`
- **Java**: Maven dependency available
- **cURL**: Examples provided in documentation

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **JSON Schema**: `http://localhost:8000/openapi.json`

## Examples

See the `/examples` directory for complete code samples in multiple languages demonstrating common use cases:

- Repository discovery and analysis
- Semantic code search
- Agent orchestration
- Migration planning
- Compliance reporting

## Support

For API support and questions:

- **Documentation**: `/docs`
- **GitHub Issues**: https://github.com/your-org/codeanalysis-multiagent-mvp/issues
- **Enterprise Support**: Contact your account manager