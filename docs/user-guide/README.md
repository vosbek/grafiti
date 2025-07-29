# User Guide

## Getting Started

Welcome to CodeAnalysis-MultiAgent-MVP! This guide will help you get up and running with intelligent analysis of your Java enterprise applications.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Repository Management](#repository-management) 
3. [Code Analysis](#code-analysis)
4. [Multi-Agent System](#multi-agent-system)
5. [Semantic Search](#semantic-search)
6. [Understanding Results](#understanding-results)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Installation

Choose your preferred installation method:

**Option A: One-Command Setup (Recommended)**

```bash
# Linux/macOS/AWS
./startup.sh

# Windows
startup.bat

# With repository discovery
./startup.sh --discover-from=https://github.com/your-org/main-app.git
```

**Option B: Docker Compose**

```bash
git clone https://github.com/your-org/codeanalysis-multiagent-mvp.git
cd codeanalysis-multiagent-mvp
docker-compose -f docker/development/docker-compose.yml up -d
```

**Option C: Kubernetes**

```bash
kubectl apply -f kubernetes/
```

### 2. First Access

Once started, access the system:

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

### 3. System Status

Verify all services are running:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "redis": "connected",
    "codebert": "loaded",
    "agents": "ready"
  }
}
```

## Repository Management

### Adding Repositories

#### Method 1: Automatic Discovery

The system can automatically discover dependencies starting from a main repository:

```bash
curl -X POST "http://localhost:8000/api/v1/repositories/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/your-org/main-application.git",
    "max_depth": 3,
    "include_external": false,
    "analysis_config": {
      "frameworks": ["struts", "corba", "spring"],
      "skip_tests": true
    }
  }'
```

This will:
1. Clone the main repository
2. Analyze Maven/Gradle dependencies
3. Find internal dependency repositories
4. Clone all discovered repositories
5. Begin code analysis automatically

#### Method 2: Manual Repository List

If you know exactly which repositories to analyze:

```bash
curl -X POST "http://localhost:8000/api/v1/repositories/clone" \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": [
      {
        "url": "https://github.com/your-org/user-service.git",
        "branch": "main",
        "priority": "high"
      },
      {
        "url": "https://github.com/your-org/payment-service.git",
        "branch": "develop",
        "priority": "medium"
      }
    ],
    "concurrent_clones": 5
  }'
```

#### Method 3: Web Interface

1. Navigate to http://localhost:8000
2. Click "Add Repositories"
3. Choose "Discover Dependencies" or "Manual Entry"
4. Enter repository URLs or upload a CSV file
5. Configure analysis settings
6. Click "Start Analysis"

### Monitoring Progress

Track repository discovery and analysis progress:

```bash
# Check overall status
curl "http://localhost:8000/api/v1/repositories?status=analyzing"

# Monitor specific job
curl "http://localhost:8000/api/v1/repositories/jobs/{job_id}/status"
```

### Repository Configuration

#### Framework Detection

The system automatically detects:

- **Struts**: struts-config.xml, Action classes, JSP files
- **CORBA**: IDL files, POA servants, Helper classes
- **Spring**: @Component annotations, XML configs
- **EJB**: ejb-jar.xml, @Stateless annotations
- **Hibernate**: hibernate.cfg.xml, @Entity annotations

#### Custom Mappings

For internal dependencies, create a `repository-mappings.json` file:

```json
{
  "com.yourcompany.auth": "authentication-service",
  "com.yourcompany.payment": "payment-processing",
  "com.yourcompany.common": "shared-utilities"
}
```

Place this file in your workspace directory before starting analysis.

## Code Analysis

### Comprehensive Analysis

Perform deep analysis across all repositories:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": ["user-service", "payment-service"],
    "analysis_type": "full",
    "agents": [
      "architecture_analyzer",
      "struts_legacy_agent",
      "business_rules_extractor",
      "migration_planner"
    ],
    "query": "Analyze authentication and authorization patterns",
    "context": {
      "focus_areas": ["security", "user_management"],
      "modernization_target": "spring_boot"
    }
  }'
```

### Analysis Types

#### 1. Architecture Analysis

Understand your application structure:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -d '{
    "analysis_type": "architecture",
    "query": "Map the overall application architecture"
  }'
```

Results include:
- Package organization
- Layer separation (presentation, business, data)
- Component dependencies
- Framework usage patterns
- Architectural anti-patterns

#### 2. Legacy Framework Analysis

Deep dive into Struts and CORBA usage:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -d '{
    "analysis_type": "legacy_frameworks",
    "agents": ["struts_legacy_agent", "corba_integration_agent"],
    "query": "Analyze Struts actions and CORBA interfaces"
  }'
```

Results include:
- Struts action mappings and flows
- Form bean usage patterns
- CORBA interface definitions
- Distribution patterns
- Migration complexity scores

#### 3. Business Rules Extraction

Identify embedded business logic:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -d '{
    "analysis_type": "business_rules",
    "agents": ["business_rules_extractor"],
    "query": "Extract all validation and calculation rules",
    "context": {
      "domain": "financial_services",
      "compliance_focus": "SOX"
    }
  }'
```

Results include:
- Validation rules
- Calculation logic  
- Workflow patterns
- Compliance-related rules
- Rule interdependencies

#### 4. Migration Planning

Get modernization recommendations:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -d '{
    "analysis_type": "migration",
    "agents": ["migration_planner"],
    "query": "Plan migration from Struts to Spring Boot",
    "context": {
      "target_framework": "spring_boot",
      "timeline": "6_months",
      "risk_tolerance": "medium"
    }
  }'
```

Results include:
- Migration roadmap
- Effort estimates
- Risk assessments
- Priority recommendations
- Impact analysis

### Monitoring Analysis Progress

```bash
# Check analysis status
curl "http://localhost:8000/api/v1/analysis/{analysis_id}/status"

# Get partial results (for long-running analyses)
curl "http://localhost:8000/api/v1/analysis/{analysis_id}/results?partial=true"
```

## Multi-Agent System

### Available Agents

#### 1. Supervisor Agent
- **Purpose**: Orchestrates other agents and synthesizes results
- **Use Case**: Complex queries requiring multiple perspectives
- **Automatic**: Always included in comprehensive analysis

#### 2. Architecture Analyzer
- **Purpose**: Maps application structure and design patterns
- **Use Case**: Understanding system organization
- **Example Query**: "What is the overall architecture of this system?"

#### 3. Struts Legacy Agent
- **Purpose**: Specialized Struts framework analysis
- **Use Case**: Legacy Struts application modernization
- **Example Query**: "How complex would it be to migrate this Struts app?"

#### 4. CORBA Integration Agent
- **Purpose**: Analyzes CORBA distributed systems
- **Use Case**: Understanding distributed architecture
- **Example Query**: "Map all CORBA interfaces and their usage"

#### 5. Business Rules Extractor
- **Purpose**: Identifies business logic embedded in code
- **Use Case**: Business rule documentation and compliance
- **Example Query**: "What are all the validation rules for user registration?"

#### 6. Migration Planning Agent
- **Purpose**: Creates modernization strategies
- **Use Case**: Legacy system modernization
- **Example Query**: "Create a migration plan to Spring Boot"

#### 7. Technical Debt Agent
- **Purpose**: Identifies maintainability issues
- **Use Case**: Code quality assessment
- **Example Query**: "What are the biggest technical debt areas?"

### Custom Agent Execution

Execute specific agents with tailored parameters:

```bash
curl -X POST "http://localhost:8000/api/v1/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "business_rules_extractor",
    "repositories": ["user-service"],
    "parameters": {
      "rule_types": ["validation", "calculation"],
      "confidence_threshold": 0.8,
      "include_comments": true
    },
    "context": {
      "domain": "e_commerce",
      "compliance_focus": "PCI_DSS"
    }
  }'
```

### Agent Collaboration

Agents share context through the knowledge graph:

1. **Supervisor** creates analysis plan
2. **Architecture Analyzer** maps system structure
3. **Framework-specific agents** analyze their domains
4. **Business Rules Extractor** identifies logic patterns
5. **Migration Planner** synthesizes recommendations
6. **Supervisor** creates final comprehensive report

## Semantic Search

### Basic Search

Find code components using natural language:

```bash
curl -X POST "http://localhost:8000/api/v1/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all payment processing logic",
    "options": {
      "max_results": 20,
      "similarity_threshold": 0.7
    }
  }'
```

### Advanced Search

Use filters and options for precise results:

```bash
curl -X POST "http://localhost:8000/api/v1/search/semantic" \
  -d '{
    "query": "authentication and security validation",
    "filters": {
      "repositories": ["user-service", "auth-service"],
      "entity_types": ["class", "method"],
      "frameworks": ["struts", "spring"],
      "complexity_min": 3.0
    },
    "options": {
      "max_results": 50,
      "include_context": true,
      "highlight_matches": true
    }
  }'
```

### Search Examples

#### Find Business Logic
```bash
# Query
"Calculate payment fees and taxes"

# Results
- PaymentCalculator.calculateFees()
- TaxService.computeTax()
- PricingRule.applyDiscounts()
```

#### Find Security Code
```bash
# Query  
"User authentication and password validation"

# Results
- UserAuthenticator.authenticate()
- PasswordValidator.isValidPassword()
- LoginAction.execute()
```

#### Find Legacy Patterns
```bash
# Query
"Struts actions that handle form submissions"

# Results
- UserRegistrationAction.execute()
- PaymentFormAction.process()
- ProfileUpdateAction.perform()
```

### Relationship Search

Find connections between code components:

```bash
curl -X POST "http://localhost:8000/api/v1/search/relationships" \
  -d '{
    "entity": "com.company.auth.UserService",
    "relationship_types": ["calls", "implements", "uses"],
    "direction": "both",
    "max_depth": 3
  }'
```

## Understanding Results

### Analysis Report Structure

```json
{
  "analysis_id": "analysis_123456",
  "status": "completed",
  "supervisor_summary": "High-level summary of findings",
  "agent_results": {
    "architecture_analyzer": {
      "findings": [...],
      "patterns": [...],
      "recommendations": [...]
    },
    "struts_legacy_agent": {
      "actions": [...],
      "complexity_scores": [...],
      "migration_recommendations": [...]
    }
  },
  "synthesized_response": "Comprehensive analysis narrative",
  "code_references": [...],
  "relationships": [...],
  "recommendations": [...]
}
```

### Key Metrics

#### Complexity Scores
- **Low (1-3)**: Simple, well-structured code
- **Medium (4-7)**: Moderate complexity, some refactoring beneficial
- **High (8-12)**: Complex code, refactoring recommended
- **Very High (13+)**: Highly complex, prioritize for refactoring

#### Migration Effort
- **Low**: 1-2 weeks, straightforward conversion
- **Medium**: 3-6 weeks, some architectural changes needed
- **High**: 2-3 months, significant redesign required
- **Very High**: 6+ months, complete rewrite recommended

#### Risk Levels
- **Low**: Minimal risk, well-understood changes
- **Medium**: Some risk, requires careful testing  
- **High**: Significant risk, extensive testing needed
- **Critical**: High risk, consider alternatives

### Interpreting Recommendations

#### Priority Levels
1. **Critical**: Address immediately, blocks other work
2. **High**: Plan for next sprint/iteration
3. **Medium**: Include in upcoming milestone
4. **Low**: Address when resources permit

#### Recommendation Types
- **Technical Debt**: Code quality improvements
- **Security**: Security vulnerabilities and hardening
- **Performance**: Optimization opportunities
- **Modernization**: Framework and architecture updates
- **Compliance**: Regulatory requirement alignment

## Best Practices

### Repository Organization

1. **Consistent Naming**: Use consistent repository naming conventions
2. **Branch Strategy**: Use standard branch names (main, develop, feature/*)
3. **Documentation**: Include README files with setup instructions
4. **Dependencies**: Keep dependency declarations up to date

### Analysis Strategy

1. **Start Small**: Begin with 2-3 core repositories
2. **Iterative Approach**: Analyze in phases, not all at once
3. **Focus Areas**: Define specific goals (security, modernization, etc.)
4. **Regular Updates**: Re-analyze after significant changes

### Query Optimization

1. **Specific Questions**: Ask specific, focused questions
2. **Context Matters**: Provide business context for better results
3. **Iterative Refinement**: Refine queries based on initial results
4. **Use Filters**: Apply filters to narrow down large result sets

### Performance Optimization

1. **Hardware Scaling**: Use GPUs for faster embeddings
2. **Parallel Processing**: Clone repositories concurrently
3. **Caching**: Enable caching for repeated analyses
4. **Resource Monitoring**: Monitor CPU, memory, and GPU usage

## Troubleshooting

### Common Issues

#### 1. Repository Access Issues

**Problem**: Cannot clone private repositories

**Solution**:
```bash
# Configure Git credentials
git config --global credential.helper store
echo "https://username:token@github.com" > ~/.git-credentials

# Or use SSH keys
ssh-keygen -t rsa -b 4096 -C "your.email@company.com"
# Add public key to GitHub/GitLab
```

#### 2. Analysis Stuck/Slow

**Problem**: Analysis takes very long or appears stuck

**Solutions**:
- Check system resources: `curl http://localhost:8000/api/v1/health`
- Monitor logs: `docker logs codeanalysis-backend`
- Reduce batch size: Set `EMBEDDING_BATCH_SIZE=8` for low-memory systems
- Use CPU-only mode: Set `DEVICE=cpu` if GPU issues

#### 3. Incomplete Results

**Problem**: Missing classes or methods in results

**Solutions**:
- Check file size limits: Increase `MAX_FILE_SIZE_MB`
- Verify supported extensions: `.java`, `.jsp`, `.xml` are included
- Review parsing logs for errors
- Ensure repositories are fully cloned

#### 4. Performance Issues

**Problem**: Slow response times

**Solutions**:
- Scale backend replicas: `kubectl scale deployment codeanalysis-backend --replicas=3`
- Add more worker processes: Increase `CELERY_WORKERS`
- Optimize database: Add Neo4j indices
- Use SSD storage for better I/O performance

#### 5. Memory Issues

**Problem**: Out of memory errors

**Solutions**:
- Increase memory limits in deployment
- Reduce concurrent processing: Lower `MAX_CONCURRENT_CLONES`
- Use streaming processing for large files
- Clear caches: Restart services periodically

### Getting Help

#### 1. System Information

Collect system information for troubleshooting:

```bash
# System health
curl http://localhost:8000/api/v1/health/detailed

# Resource usage
curl http://localhost:8000/api/v1/metrics

# Recent logs
curl http://localhost:8000/api/v1/logs?level=error&limit=50
```

#### 2. Log Analysis

Check logs for specific issues:

```bash
# Application logs
docker logs codeanalysis-backend --tail=100

# Database logs
docker logs neo4j --tail=50

# Worker logs  
docker logs codeanalysis-worker --tail=50
```

#### 3. Performance Monitoring

Monitor system performance:

```bash
# CPU and memory usage
docker stats

# GPU usage (if applicable)
nvidia-smi

# Database performance
# Connect to Neo4j browser at http://localhost:7474
```

#### 4. Support Channels

- **Documentation**: Check `/docs` endpoint
- **GitHub Issues**: Report bugs and feature requests
- **Enterprise Support**: Contact your account manager
- **Community**: Join discussions on GitHub Discussions

### Debugging Tips

1. **Enable Debug Logging**: Set `LOG_LEVEL=DEBUG`
2. **Use Partial Results**: Get interim results with `?partial=true`
3. **Test Individual Agents**: Execute agents separately to isolate issues
4. **Check Resource Limits**: Monitor CPU, memory, and disk usage
5. **Validate Input Data**: Ensure repositories are accessible and valid

## Advanced Usage

### Custom Agent Development

Create custom agents for specific analysis needs:

```python
from app.agents.base_agent import BaseAgent

class CustomComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="compliance_agent")
    
    async def analyze(self, context):
        # Custom analysis logic
        return results
```

### Integration with CI/CD

Integrate with your CI/CD pipeline:

```yaml
# .github/workflows/code-analysis.yml
name: Code Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Analyze Code
      run: |
        curl -X POST "http://codeanalysis.company.com/api/v1/analysis/comprehensive" \
          -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
          -d '{
            "repositories": ["${{ github.repository }}"],
            "analysis_type": "ci_cd",
            "context": {"commit": "${{ github.sha }}"}
          }'
```

### API Client Libraries

Use official client libraries for common languages:

**Python**:
```python
from codeanalysis_client import CodeAnalysisClient

client = CodeAnalysisClient("http://localhost:8000")
result = client.analyze_comprehensive(
    repositories=["my-repo"],
    query="Find security vulnerabilities"
)
```

**JavaScript**:
```javascript
import { CodeAnalysisClient } from '@company/codeanalysis-client';

const client = new CodeAnalysisClient('http://localhost:8000');
const result = await client.analyzeComprehensive({
  repositories: ['my-repo'],
  query: 'Find security vulnerabilities'
});
```

This user guide provides comprehensive coverage of all system features, from basic setup to advanced usage patterns. Follow the examples and best practices to get the most value from your code analysis.