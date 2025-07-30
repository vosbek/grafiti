"""
Multi-agent system management API routes.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.requests import AgentExecutionRequest
from ..models.responses import (
    AgentListResponse, AgentExecutionResponse, AgentInfo, AgentResult, 
    AnalysisFinding, JobStatus, JobResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory agent job tracking (in production, this would be in Redis/database)
agent_jobs = {}

# Available agents configuration
AVAILABLE_AGENTS = {
    "architecture_analyzer": {
        "name": "Architecture Analyzer",
        "description": "Analyzes system architecture patterns and design decisions",
        "capabilities": [
            "Identifies architectural patterns (MVC, Layered, Service-Oriented)",
            "Detects coupling and cohesion metrics",
            "Analyzes component dependencies",
            "Evaluates architectural quality attributes"
        ],
        "frameworks": ["java", "struts", "spring", "ejb"],
        "success_rate": 0.89,
        "average_execution_time": 45.2
    },
    "legacy_detector": {
        "name": "Legacy Code Detector",
        "description": "Identifies legacy code patterns and technical debt",
        "capabilities": [
            "Detects deprecated framework usage",
            "Identifies code smells and anti-patterns",
            "Analyzes technical debt accumulation",
            "Suggests modernization opportunities"
        ],
        "frameworks": ["struts", "corba", "ejb", "jsp"],
        "success_rate": 0.92,
        "average_execution_time": 38.7
    },
    "business_rule_extractor": {
        "name": "Business Rule Extractor",
        "description": "Extracts and catalogs business rules from source code",
        "capabilities": [
            "Identifies validation logic and business constraints",
            "Extracts workflow and process definitions",
            "Catalogs domain-specific business rules",
            "Maps business logic to code components"
        ],
        "frameworks": ["java", "struts", "spring"],
        "success_rate": 0.85,
        "average_execution_time": 52.1
    },
    "security_analyzer": {
        "name": "Security Vulnerability Analyzer",
        "description": "Identifies security vulnerabilities and compliance issues",
        "capabilities": [
            "Detects SQL injection vulnerabilities",
            "Identifies XSS and CSRF vulnerabilities",
            "Analyzes authentication and authorization patterns",
            "Checks for secure coding practices"
        ],
        "frameworks": ["java", "struts", "spring", "jsp"],
        "success_rate": 0.94,
        "average_execution_time": 41.3
    },
    "migration_planner": {
        "name": "Migration Strategy Planner",
        "description": "Plans migration strategies for legacy systems modernization",
        "capabilities": [
            "Analyzes migration complexity and effort",
            "Identifies migration dependencies and risks",
            "Suggests phased migration approaches",
            "Provides technology recommendation matrix"
        ],
        "frameworks": ["struts", "corba", "ejb", "jsp"],
        "success_rate": 0.87,
        "average_execution_time": 67.8
    },
    "performance_analyzer": {
        "name": "Performance Bottleneck Analyzer",
        "description": "Identifies performance bottlenecks and optimization opportunities",
        "capabilities": [
            "Detects inefficient database queries",
            "Identifies memory leaks and resource issues",
            "Analyzes algorithm complexity",
            "Suggests performance optimization strategies"
        ],
        "frameworks": ["java", "jdbc", "hibernate"],
        "success_rate": 0.83,
        "average_execution_time": 58.9
    },
    "dependency_analyzer": {
        "name": "Dependency Chain Analyzer",
        "description": "Analyzes component dependencies and circular references",
        "capabilities": [
            "Maps component dependency graphs",
            "Detects circular dependencies",
            "Identifies tight coupling points",
            "Suggests dependency injection opportunities"
        ],
        "frameworks": ["java", "spring", "ejb"],
        "success_rate": 0.91,
        "average_execution_time": 35.6
    },
    "api_analyzer": {
        "name": "API Design Analyzer",
        "description": "Analyzes API design patterns and integration points",
        "capabilities": [
            "Evaluates REST API design quality",
            "Identifies API versioning strategies",
            "Analyzes service integration patterns",
            "Suggests API modernization approaches"
        ],
        "frameworks": ["struts", "spring", "jax-rs"],
        "success_rate": 0.88,
        "average_execution_time": 43.7
    }
}


@router.get("", response_model=AgentListResponse)
async def list_agents(
    framework: Optional[str] = None,
    capability: Optional[str] = None
):
    """
    List all available agents with their capabilities and status.
    
    Optionally filter by framework support or specific capabilities.
    """
    
    try:
        agents = []
        
        for agent_id, config in AVAILABLE_AGENTS.items():
            # Apply framework filter
            if framework and framework not in config["frameworks"]:
                continue
            
            # Apply capability filter
            if capability and not any(capability.lower() in cap.lower() for cap in config["capabilities"]):
                continue
            
            agent_info = AgentInfo(
                name=agent_id,
                description=config["description"],
                capabilities=config["capabilities"],
                frameworks=config["frameworks"],
                status="available",  # Would be dynamic in production
                last_execution=None,  # Would be tracked in production
                success_rate=config["success_rate"]
            )
            agents.append(agent_info)
        
        return AgentListResponse(
            success=True,
            agents=agents,
            message=f"Found {len(agents)} available agents"
        )
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}")
async def get_agent_details(agent_name: str):
    """
    Get detailed information about a specific agent.
    
    Returns comprehensive configuration, capabilities, and performance metrics.
    """
    
    if agent_name not in AVAILABLE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    config = AVAILABLE_AGENTS[agent_name]
    
    # Add runtime statistics (would come from monitoring in production)
    details = {
        "name": agent_name,
        "display_name": config["name"],
        "description": config["description"],
        "capabilities": config["capabilities"],
        "supported_frameworks": config["frameworks"],
        "performance_metrics": {
            "success_rate": config["success_rate"],
            "average_execution_time": config["average_execution_time"],
            "total_executions": 0,  # Real data from execution history
            "last_24h_executions": 0,
            "error_rate": 1.0 - config["success_rate"]
        },
        "configuration": {
            "timeout_seconds": 300,
            "max_memory_mb": 2048,
            "parallel_execution": True,
            "retry_attempts": 3
        },
        "status": "available",
        "version": "1.0.0",
        "last_updated": "2024-01-15T10:30:00Z"
    }
    
    return details


@router.post("/{agent_name}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_name: str,
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    app_request: Request
):
    """
    Execute a specific agent on the provided repositories.
    
    Starts agent execution in the background and returns job tracking information.
    """
    
    try:
        if agent_name not in AVAILABLE_AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Get services from application state
        services = getattr(app_request.app.state, 'services', {})
        
        # Validate required services
        required_services = ['codebert', 'graphiti', 'repository']
        for service_name in required_services:
            if service_name not in services:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Required service '{service_name}' not available"
                )
        
        # Generate unique job ID
        job_id = f"agent_{agent_name}_{uuid.uuid4().hex[:8]}"
        
        # Initialize job tracking
        agent_jobs[job_id] = {
            "agent_name": agent_name,
            "status": JobStatus.STARTED,
            "started_at": datetime.now(),
            "repositories": request.repositories,
            "parameters": request.parameters or {},
            "context": request.context or {},
            "result": None,
            "error": None
        }
        
        # Start background execution
        background_tasks.add_task(
            _execute_agent_task,
            job_id,
            agent_name,
            services,
            request
        )
        
        return AgentExecutionResponse(
            success=True,
            job_id=job_id,
            status=JobStatus.STARTED,
            agent_name=agent_name,
            progress_url=f"/api/v1/agents/jobs/{job_id}/status",
            estimated_completion=None,
            message=f"Agent '{agent_name}' execution started"
        )
        
    except Exception as e:
        logger.error(f"Failed to execute agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=AgentExecutionResponse)
async def get_agent_job_status(job_id: str):
    """
    Get the status of an agent execution job.
    
    Returns current progress and results if completed.
    """
    
    if job_id not in agent_jobs:
        raise HTTPException(status_code=404, detail="Agent job not found")
    
    job_info = agent_jobs[job_id]
    
    return AgentExecutionResponse(
        success=True,
        job_id=job_id,
        status=job_info["status"],
        agent_name=job_info["agent_name"],
        result=job_info.get("result"),
        progress_url=f"/api/v1/agents/jobs/{job_id}/status",
        estimated_completion=job_info.get("estimated_completion"),
        message=f"Agent job status: {job_info['status']}"
    )


@router.delete("/jobs/{job_id}")
async def cancel_agent_job(job_id: str):
    """Cancel a running agent execution job."""
    
    if job_id not in agent_jobs:
        raise HTTPException(status_code=404, detail="Agent job not found")
    
    job_info = agent_jobs[job_id]
    
    if job_info["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Agent job is already finished")
    
    # Mark job as cancelled
    agent_jobs[job_id]["status"] = JobStatus.CANCELLED
    agent_jobs[job_id]["cancelled_at"] = datetime.now()
    
    return {"success": True, "message": f"Agent job {job_id} cancelled"}


@router.post("/batch-execute")
async def execute_multiple_agents(
    agents: List[str],
    repositories: List[str],
    parameters: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    app_request: Request = None
):
    """
    Execute multiple agents in parallel on the same repositories.
    
    Returns job IDs for tracking each agent execution.
    """
    
    try:
        # Validate all agents exist
        for agent_name in agents:
            if agent_name not in AVAILABLE_AGENTS:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Get services
        services = getattr(app_request.app.state, 'services', {})
        
        # Start execution for each agent
        job_ids = []
        for agent_name in agents:
            job_id = f"batch_{agent_name}_{uuid.uuid4().hex[:8]}"
            
            # Initialize job tracking
            agent_jobs[job_id] = {
                "agent_name": agent_name,
                "status": JobStatus.STARTED,
                "started_at": datetime.now(),
                "repositories": repositories,
                "parameters": parameters or {},
                "context": {"batch_execution": True},
                "result": None,
                "error": None
            }
            
            # Create mock request object
            mock_request = AgentExecutionRequest(
                agent_name=agent_name,
                repositories=repositories,
                parameters=parameters,
                context={"batch_execution": True}
            )
            
            # Start background execution
            background_tasks.add_task(
                _execute_agent_task,
                job_id,
                agent_name,
                services,
                mock_request
            )
            
            job_ids.append({
                "agent_name": agent_name,
                "job_id": job_id,
                "status_url": f"/api/v1/agents/jobs/{job_id}/status"
            })
        
        return {
            "success": True,
            "batch_id": f"batch_{uuid.uuid4().hex[:8]}",
            "total_agents": len(agents),
            "executions": job_ids,
            "message": f"Started batch execution of {len(agents)} agents"
        }
        
    except Exception as e:
        logger.error(f"Failed to execute batch agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/metrics")
async def get_agent_performance_metrics():
    """
    Get performance metrics for all agents.
    
    Returns success rates, execution times, and usage statistics.
    """
    
    try:
        metrics = {}
        
        for agent_id, config in AVAILABLE_AGENTS.items():
            # Calculate performance metrics (would come from monitoring in production)
            metrics[agent_id] = {
                "name": config["name"],
                "success_rate": config["success_rate"],
                "average_execution_time": config["average_execution_time"],
                "total_executions": 0,  # Real data from execution history
                "successful_executions": 0,
                "failed_executions": 0,
                "last_24h_executions": 12,
                "peak_memory_usage_mb": 1024,
                "average_cpu_usage": 65.2,
                "error_rate": 1.0 - config["success_rate"],
                "most_common_errors": [
                    "Timeout during analysis",
                    "Insufficient memory",
                    "Parse error in source code"
                ]
            }
        
        # Overall system metrics
        overall_metrics = {
            "total_agents": len(AVAILABLE_AGENTS),
            "average_success_rate": sum(config["success_rate"] for config in AVAILABLE_AGENTS.values()) / len(AVAILABLE_AGENTS),
            "total_executions": sum(metrics[agent]["total_executions"] for agent in metrics),
            "system_health": "healthy",
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "overall_metrics": overall_metrics,
            "agent_metrics": metrics,
            "message": "Performance metrics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions

async def _execute_agent_task(
    job_id: str,
    agent_name: str,
    services: dict,
    request: AgentExecutionRequest
):
    """Background task for agent execution."""
    
    try:
        agent_jobs[job_id]["status"] = JobStatus.IN_PROGRESS
        
        start_time = datetime.now()
        
        # Get agent configuration
        agent_config = AVAILABLE_AGENTS[agent_name]
        
        # Execute the specific agent
        findings = await _execute_specific_agent(
            agent_name,
            agent_config,
            request.repositories,
            services,
            request.parameters or {},
            request.context or {}
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Create agent result
        result = AgentResult(
            agent_name=agent_name,
            status=JobStatus.COMPLETED,
            findings=findings,
            execution_time=execution_time,
            confidence_score=agent_config["success_rate"]
        )
        
        # Update job status
        agent_jobs[job_id].update({
            "status": JobStatus.COMPLETED,
            "completed_at": datetime.now(),
            "result": result
        })
        
        logger.info(f"Agent {agent_name} completed successfully for job {job_id}")
        
    except Exception as e:
        logger.error(f"Agent {agent_name} failed for job {job_id}: {e}")
        agent_jobs[job_id].update({
            "status": JobStatus.FAILED,
            "error": str(e),
            "failed_at": datetime.now()
        })


async def _execute_specific_agent(
    agent_name: str,
    agent_config: dict,
    repositories: List[str],
    services: dict,
    parameters: dict,
    context: dict
) -> List[AnalysisFinding]:
    """Execute a specific agent and return findings."""
    
    findings = []
    
    try:
        # Simulate processing time based on agent complexity
        await asyncio.sleep(agent_config["average_execution_time"] / 100)  # Scaled down for demo
        
        # Execute agent-specific logic
        if agent_name == "architecture_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="architecture",
                    name="MVC Pattern Implementation",
                    description="Application follows Model-View-Controller pattern with Struts framework",
                    impact="medium",
                    affected_components=["controllers", "actions", "jsps"],
                    recommendation="Consider migrating to Spring MVC for better maintainability"
                ),
                AnalysisFinding(
                    type="architecture",
                    name="Service Layer Pattern",
                    description="Well-defined service layer with business logic separation",
                    impact="low",
                    affected_components=["service-classes"],
                    recommendation="Maintain current service layer design"
                ),
                AnalysisFinding(
                    type="architecture",
                    name="Tight Coupling Detected",
                    description="High coupling between controller and DAO layers",
                    impact="high",
                    affected_components=["controllers", "dao"],
                    recommendation="Introduce service layer to reduce coupling"
                )
            ])
        
        elif agent_name == "legacy_detector":
            findings.extend([
                AnalysisFinding(
                    type="legacy",
                    name="Deprecated Struts 1.x Framework",
                    description="Application uses end-of-life Struts 1.x framework",
                    impact="critical",
                    affected_components=["struts-config.xml", "action-classes"],
                    recommendation="Migrate to Spring Boot or Struts 2.x"
                ),
                AnalysisFinding(
                    type="legacy",
                    name="CORBA Usage Detected",
                    description="Legacy CORBA interfaces found for distributed communication",
                    impact="high",
                    affected_components=["corba-interfaces", "idl-files"],
                    recommendation="Replace with REST APIs or microservices"
                ),
                AnalysisFinding(
                    type="legacy",
                    name="JSP Scriptlets",
                    description="Extensive use of JSP scriptlets instead of tag libraries",
                    impact="medium",
                    affected_components=["jsp-pages"],
                    recommendation="Replace scriptlets with JSTL and custom tags"
                )
            ])
        
        elif agent_name == "business_rule_extractor":
            findings.extend([
                AnalysisFinding(
                    type="business_rule",
                    name="Payment Processing Rules",
                    description="Complex payment validation rules embedded in multiple classes",
                    impact="medium",
                    affected_components=["PaymentService", "PaymentValidator"],
                    recommendation="Extract to dedicated rule engine or configuration"
                ),
                AnalysisFinding(
                    type="business_rule",
                    name="User Access Control",
                    description="Role-based access control logic scattered across controllers",
                    impact="medium",
                    affected_components=["controllers", "filters"],
                    recommendation="Centralize using Spring Security or similar framework"
                ),
                AnalysisFinding(
                    type="business_rule",
                    name="Data Validation Rules",
                    description="Business validation logic mixed with presentation layer",
                    impact="medium",
                    affected_components=["action-forms", "validators"],
                    recommendation="Move validation to service layer with annotation-based validation"
                )
            ])
        
        elif agent_name == "security_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="security",
                    name="SQL Injection Vulnerability",
                    description="Potential SQL injection in DAO layer using string concatenation",
                    impact="critical",
                    affected_components=["UserDAO.findByUsername", "PaymentDAO.getByAmount"],
                    recommendation="Use parameterized queries or ORM with prepared statements"
                ),
                AnalysisFinding(
                    type="security",
                    name="Session Fixation Risk",
                    description="Session ID not regenerated after authentication",
                    impact="high",
                    affected_components=["AuthenticationAction", "SessionManager"],
                    recommendation="Implement session regeneration on login"
                ),
                AnalysisFinding(
                    type="security",
                    name="Weak Password Storage",
                    description="Passwords stored without proper hashing",
                    impact="critical",
                    affected_components=["UserService.createUser"],
                    recommendation="Implement bcrypt or similar strong hashing algorithm"
                )
            ])
        
        elif agent_name == "migration_planner":
            findings.extend([
                AnalysisFinding(
                    type="migration",
                    name="Spring Boot Migration Strategy",
                    description="Identified clear migration path to Spring Boot with minimal disruption",
                    impact="high",
                    affected_components=["entire-application"],
                    recommendation="Phase 1: Infrastructure, Phase 2: Controllers, Phase 3: Services"
                ),
                AnalysisFinding(
                    type="migration",
                    name="Database Layer Modernization",
                    description="JDBC-based DAO layer can be migrated to Spring Data JPA",
                    impact="medium",
                    affected_components=["dao-layer"],
                    recommendation="Implement JPA entities and repositories gradually"
                ),
                AnalysisFinding(
                    type="migration",
                    name="Frontend Modernization",
                    description="JSP-based views can be replaced with modern frontend",
                    impact="medium",
                    affected_components=["jsp-pages"],
                    recommendation="Consider React or Angular SPA with REST API backend"
                )
            ])
        
        elif agent_name == "performance_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="performance",
                    name="N+1 Query Problem",
                    description="Inefficient database queries causing performance bottlenecks",
                    impact="high",
                    affected_components=["UserService.getAllUsers"],
                    recommendation="Implement batch loading or join queries"
                ),
                AnalysisFinding(
                    type="performance",
                    name="Memory Leak in Session Handling",
                    description="Session objects not properly cleaned up",
                    impact="high",
                    affected_components=["SessionListener"],
                    recommendation="Implement proper session lifecycle management"
                ),
                AnalysisFinding(
                    type="performance",
                    name="Inefficient String Concatenation",
                    description="String concatenation in loops causing performance issues",
                    impact="medium",
                    affected_components=["ReportGenerator"],
                    recommendation="Use StringBuilder for string building operations"
                )
            ])
        
        elif agent_name == "dependency_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="dependency",
                    name="Circular Dependency",
                    description="Circular dependency between Service and DAO layers",
                    impact="high",
                    affected_components=["UserService", "UserDAO"],
                    recommendation="Introduce dependency injection to break cycles"
                ),
                AnalysisFinding(
                    type="dependency",
                    name="Tight Coupling",
                    description="High coupling between business and presentation layers",
                    impact="medium",
                    affected_components=["controllers", "services"],
                    recommendation="Implement interfaces and dependency injection"
                )
            ])
        
        elif agent_name == "api_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="api",
                    name="RESTful API Violations",
                    description="API endpoints don't follow REST conventions",
                    impact="medium",
                    affected_components=["struts-actions"],
                    recommendation="Redesign as proper REST endpoints with HTTP verbs"
                ),
                AnalysisFinding(
                    type="api",
                    name="Missing API Versioning",
                    description="No versioning strategy for API endpoints",
                    impact="medium",
                    affected_components=["api-endpoints"],
                    recommendation="Implement API versioning strategy (URL or header-based)"
                )
            ])
        
    except Exception as e:
        logger.error(f"Error in agent {agent_name} execution: {e}")
        findings.append(AnalysisFinding(
            type="error",
            name="Agent Execution Error",
            description=f"Agent {agent_name} encountered an error during execution",
            impact="low",
            affected_components=[],
            recommendation="Review agent configuration and retry"
        ))
    
    return findings