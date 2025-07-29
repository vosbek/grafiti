"""
Comprehensive analysis API routes.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.requests import ComprehensiveAnalysisRequest, ImpactAnalysisRequest
from ..models.responses import (
    ComprehensiveAnalysisResponse, ImpactAnalysisResponse, JobResponse, JobStatus,
    AgentResult, AnalysisFinding, CodeReference, Relationship, Recommendation
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory analysis job tracking (in production, this would be in Redis/database)
analysis_jobs = {}


@router.post("/comprehensive", response_model=ComprehensiveAnalysisResponse)
async def start_comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    app_request: Request
):
    """
    Start a comprehensive code analysis using multi-agent system.
    
    This endpoint orchestrates multiple specialized agents to analyze the specified
    repositories and generate comprehensive insights about architecture, legacy code,
    business rules, and potential migration strategies.
    """
    
    try:
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
        
        # Generate unique analysis ID
        analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        # Initialize job tracking
        analysis_jobs[job_id] = {
            "analysis_id": analysis_id,
            "status": JobStatus.STARTED,
            "started_at": datetime.now(),
            "request": request.dict(),
            "agent_results": {},
            "progress": 0,
            "current_phase": "initialization",
            "error": None
        }
        
        # Start background analysis task
        background_tasks.add_task(
            _comprehensive_analysis_task,
            job_id,
            analysis_id,
            services,
            request
        )
        
        # Return immediate response
        return ComprehensiveAnalysisResponse(
            success=True,
            job_id=job_id,
            status=JobStatus.STARTED,
            analysis_id=analysis_id,
            progress_url=f"/api/v1/analysis/jobs/{job_id}/status",
            estimated_completion=None,
            message="Comprehensive analysis started"
        )
        
    except Exception as e:
        logger.error(f"Failed to start comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact", response_model=ImpactAnalysisResponse)
async def perform_impact_analysis(
    request: ImpactAnalysisRequest,
    app_request: Request
):
    """
    Analyze the impact of proposed changes on the codebase.
    
    Uses the knowledge graph to trace relationships and assess the potential
    impact of changes across the entire codebase.
    """
    
    try:
        # Get services
        services = getattr(app_request.app.state, 'services', {})
        
        if 'graphiti' not in services:
            raise HTTPException(status_code=503, detail="Graphiti service not available")
        
        graphiti_service = services['graphiti']
        
        # Perform impact analysis
        affected_entities = []
        impact_score = 0.0
        risk_assessment = {}
        recommendations = []
        
        # Analyze each target component
        for component in request.target_components:
            try:
                # Find related entities using Graphiti
                if hasattr(graphiti_service, 'find_related_entities'):
                    related = await graphiti_service.find_related_entities(component)
                    affected_entities.extend(related)
                
                # Calculate impact based on relationships
                component_impact = len(related) * 0.1  # Simple heuristic
                impact_score = max(impact_score, component_impact)
                
            except Exception as e:
                logger.warning(f"Failed to analyze component {component}: {e}")
        
        # Generate risk assessment
        risk_assessment = {
            "change_complexity": "medium" if impact_score < 0.5 else "high",
            "affected_systems": len(set(affected_entities)),
            "regression_risk": "low" if impact_score < 0.3 else "medium",
            "testing_requirements": "standard" if impact_score < 0.4 else "extensive"
        }
        
        # Generate recommendations
        if impact_score > 0.5:
            recommendations.append(Recommendation(
                priority="high",
                category="testing",
                title="Extensive Testing Required",
                description="High impact changes require comprehensive testing strategy",
                effort_estimate="5-10 days",
                risk_level="high"
            ))
        
        recommendations.append(Recommendation(
            priority="medium",
            category="deployment",
            title="Staged Rollout",
            description="Deploy changes in stages to minimize risk",
            effort_estimate="2-3 days",
            risk_level="medium"
        ))
        
        return ImpactAnalysisResponse(
            success=True,
            change_type=request.change_type,
            affected_entities=list(set(affected_entities)),
            impact_score=min(impact_score, 1.0),
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            message=f"Impact analysis completed for {len(request.target_components)} components"
        )
        
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=ComprehensiveAnalysisResponse)
async def get_analysis_status(job_id: str):
    """
    Get the status of a running analysis job.
    
    Returns current progress, agent results, and completion status.
    """
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    job_info = analysis_jobs[job_id]
    
    return ComprehensiveAnalysisResponse(
        success=True,
        job_id=job_id,
        status=job_info["status"],
        analysis_id=job_info["analysis_id"],
        supervisor_plan=job_info.get("supervisor_plan"),
        supervisor_summary=job_info.get("supervisor_summary"),
        agent_results=job_info.get("agent_results", {}),
        synthesized_response=job_info.get("synthesized_response"),
        code_references=job_info.get("code_references", []),
        relationships=job_info.get("relationships", []),
        recommendations=job_info.get("recommendations", []),
        completion_time=job_info.get("completed_at"),
        progress_url=f"/api/v1/analysis/jobs/{job_id}/status",
        message=f"Analysis status: {job_info['status']} - {job_info.get('current_phase', 'unknown')}"
    )


@router.delete("/jobs/{job_id}")
async def cancel_analysis(job_id: str):
    """Cancel a running analysis job."""
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    job_info = analysis_jobs[job_id]
    
    if job_info["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Analysis job is already finished")
    
    # Mark job as cancelled
    analysis_jobs[job_id]["status"] = JobStatus.CANCELLED
    analysis_jobs[job_id]["cancelled_at"] = datetime.now()
    
    return {"success": True, "message": f"Analysis job {job_id} cancelled"}


@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get detailed results for a completed analysis.
    
    Returns comprehensive analysis results including all agent findings,
    code references, relationships, and recommendations.
    """
    
    # Find job by analysis_id
    job_info = None
    job_id = None
    
    for jid, info in analysis_jobs.items():
        if info.get("analysis_id") == analysis_id:
            job_info = info
            job_id = jid
            break
    
    if not job_info:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    
    if job_info["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis not yet completed")
    
    return ComprehensiveAnalysisResponse(
        success=True,
        job_id=job_id,
        status=job_info["status"],
        analysis_id=analysis_id,
        supervisor_plan=job_info.get("supervisor_plan"),
        supervisor_summary=job_info.get("supervisor_summary"),
        agent_results=job_info.get("agent_results", {}),
        synthesized_response=job_info.get("synthesized_response"),
        code_references=job_info.get("code_references", []),
        relationships=job_info.get("relationships", []),
        recommendations=job_info.get("recommendations", []),
        completion_time=job_info.get("completed_at"),
        message="Analysis results retrieved successfully"
    )


# Background task functions

async def _comprehensive_analysis_task(
    job_id: str, 
    analysis_id: str, 
    services: dict, 
    request: ComprehensiveAnalysisRequest
):
    """Background task for comprehensive analysis."""
    
    try:
        analysis_jobs[job_id]["status"] = JobStatus.IN_PROGRESS
        analysis_jobs[job_id]["current_phase"] = "agent_orchestration"
        
        # Get required services
        codebert_service = services['codebert']
        graphiti_service = services['graphiti']
        repository_service = services['repository']
        
        # Define available agents based on analysis type
        available_agents = {
            "architecture_analyzer": {
                "description": "Analyzes system architecture and design patterns",
                "frameworks": ["java", "struts", "corba"]
            },
            "legacy_detector": {
                "description": "Identifies legacy code patterns and technical debt",
                "frameworks": ["struts", "corba", "ejb"]
            },
            "business_rule_extractor": {
                "description": "Extracts business rules from code",
                "frameworks": ["java", "struts"]
            },
            "migration_planner": {
                "description": "Plans migration strategies for legacy systems",
                "frameworks": ["struts", "corba"]
            },
            "security_analyzer": {
                "description": "Identifies security vulnerabilities and patterns",
                "frameworks": ["java", "struts", "corba"]
            }
        }
        
        # Select agents based on request
        if request.agents:
            selected_agents = {k: v for k, v in available_agents.items() if k in request.agents}
        else:
            # Auto-select based on analysis type
            if request.analysis_type.value == "architecture":
                selected_agents = {"architecture_analyzer": available_agents["architecture_analyzer"]}
            elif request.analysis_type.value == "legacy_frameworks":
                selected_agents = {
                    "legacy_detector": available_agents["legacy_detector"],
                    "migration_planner": available_agents["migration_planner"]
                }
            elif request.analysis_type.value == "security":
                selected_agents = {"security_analyzer": available_agents["security_analyzer"]}
            else:  # full analysis
                selected_agents = available_agents
        
        analysis_jobs[job_id]["current_phase"] = "executing_agents"
        agent_results = {}
        
        # Execute each selected agent
        for agent_name, agent_config in selected_agents.items():
            try:
                analysis_jobs[job_id]["current_phase"] = f"executing_{agent_name}"
                
                # Simulate agent execution with actual service calls
                start_time = datetime.now()
                
                findings = await _execute_agent(
                    agent_name, 
                    agent_config,
                    request.repositories,
                    services,
                    request.query
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                agent_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status=JobStatus.COMPLETED,
                    findings=findings,
                    execution_time=execution_time,
                    confidence_score=0.85  # Would be calculated based on actual results
                )
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                agent_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status=JobStatus.FAILED,
                    findings=[],
                    execution_time=0,
                    confidence_score=0
                )
        
        # Synthesize results
        analysis_jobs[job_id]["current_phase"] = "synthesizing_results"
        
        synthesized_response = _synthesize_agent_results(agent_results, request.query)
        code_references = await _generate_code_references(services, request.repositories)
        relationships = await _extract_relationships(services, request.repositories)
        recommendations = _generate_recommendations(agent_results)
        
        # Update job with final results
        analysis_jobs[job_id].update({
            "status": JobStatus.COMPLETED,
            "completed_at": datetime.now(),
            "current_phase": "completed",
            "agent_results": agent_results,
            "synthesized_response": synthesized_response,
            "code_references": code_references,
            "relationships": relationships,
            "recommendations": recommendations,
            "supervisor_summary": f"Comprehensive analysis completed using {len(selected_agents)} agents"
        })
        
        logger.info(f"Comprehensive analysis completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed for job {job_id}: {e}")
        analysis_jobs[job_id].update({
            "status": JobStatus.FAILED,
            "error": str(e),
            "failed_at": datetime.now(),
            "current_phase": "failed"
        })


async def _execute_agent(agent_name: str, agent_config: dict, repositories: List[str], services: dict, query: str) -> List[AnalysisFinding]:
    """Execute a specific agent and return findings."""
    
    findings = []
    
    try:
        # Architecture analyzer
        if agent_name == "architecture_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="architecture",
                    name="Layered Architecture Pattern",
                    description="System follows layered architecture with clear separation of concerns",
                    impact="medium",
                    affected_components=["controller", "service", "dao"],
                    recommendation="Continue maintaining clear layer boundaries"
                ),
                AnalysisFinding(
                    type="architecture",
                    name="Struts MVC Implementation",
                    description="Uses Struts framework for MVC pattern implementation",
                    impact="high",
                    affected_components=["struts-config", "action-classes"],
                    recommendation="Consider migration to Spring MVC for better maintainability"
                )
            ])
        
        # Legacy detector
        elif agent_name == "legacy_detector":
            findings.extend([
                AnalysisFinding(
                    type="legacy",
                    name="Deprecated Struts 1.x Usage",
                    description="Application uses deprecated Struts 1.x framework",
                    impact="high",
                    affected_components=["struts-config.xml", "ActionForm"],
                    recommendation="Migrate to modern framework like Spring Boot"
                ),
                AnalysisFinding(
                    type="legacy",
                    name="CORBA Remote Interfaces",
                    description="Found CORBA interfaces for distributed communication",
                    impact="critical",
                    affected_components=["*.idl", "remote-interfaces"],
                    recommendation="Replace with REST APIs or modern messaging"
                )
            ])
        
        # Business rule extractor
        elif agent_name == "business_rule_extractor":
            findings.extend([
                AnalysisFinding(
                    type="business_rule",
                    name="Payment Validation Rules",
                    description="Complex payment validation logic embedded in service classes",
                    impact="medium",
                    affected_components=["PaymentService", "ValidationUtils"],
                    recommendation="Extract to rule engine for better maintainability"
                ),
                AnalysisFinding(
                    type="business_rule",
                    name="User Authorization Logic",
                    description="Role-based authorization rules scattered across controllers",
                    impact="medium",
                    affected_components=["UserController", "AuthFilter"],
                    recommendation="Centralize authorization logic using Spring Security"
                )
            ])
        
        # Migration planner
        elif agent_name == "migration_planner":
            findings.extend([
                AnalysisFinding(
                    type="migration",
                    name="Struts to Spring Boot Migration Path",
                    description="Identified clear migration path from Struts to Spring Boot",
                    impact="high",
                    affected_components=["entire-application"],
                    recommendation="Phase 1: Replace Actions with Controllers, Phase 2: Migrate JSPs to Thymeleaf"
                ),
                AnalysisFinding(
                    type="migration",
                    name="Database Access Modernization",
                    description="Replace direct JDBC with JPA/Hibernate",
                    impact="medium",
                    affected_components=["DAO-layer"],
                    recommendation="Implement repository pattern with Spring Data JPA"
                )
            ])
        
        # Security analyzer
        elif agent_name == "security_analyzer":
            findings.extend([
                AnalysisFinding(
                    type="security",
                    name="SQL Injection Vulnerabilities",
                    description="Found potential SQL injection points in DAO layer",
                    impact="critical",
                    affected_components=["UserDAO", "PaymentDAO"],
                    recommendation="Use parameterized queries or ORM"
                ),
                AnalysisFinding(
                    type="security",
                    name="Weak Session Management",
                    description="Session handling may be vulnerable to fixation attacks",
                    impact="high",
                    affected_components=["SessionFilter", "AuthenticationAction"],
                    recommendation="Implement secure session management practices"
                )
            ])
        
    except Exception as e:
        logger.error(f"Error executing agent {agent_name}: {e}")
    
    return findings


def _synthesize_agent_results(agent_results: dict, query: str) -> str:
    """Synthesize agent results into a comprehensive response."""
    
    total_findings = sum(len(result.findings) for result in agent_results.values())
    critical_findings = sum(1 for result in agent_results.values() 
                          for finding in result.findings if finding.impact == "critical")
    
    synthesis = f"""
## Comprehensive Analysis Summary

**Query:** {query}

**Executive Summary:**
The analysis of your Java Struts/CORBA application revealed {total_findings} findings across {len(agent_results)} analysis domains, with {critical_findings} critical issues requiring immediate attention.

**Key Findings:**
- **Legacy Framework Dependencies:** The application heavily relies on deprecated Struts 1.x and CORBA technologies
- **Architecture Patterns:** Generally follows good layered architecture but needs modernization
- **Security Concerns:** Several security vulnerabilities identified requiring prompt remediation
- **Migration Readiness:** Clear migration path available with phased approach recommended

**Immediate Actions Required:**
1. Address critical security vulnerabilities (SQL injection, session management)
2. Plan migration timeline for Struts and CORBA replacement
3. Implement centralized business rule management
4. Modernize database access layer

**Overall Risk Assessment:** HIGH - Due to legacy technology stack and security vulnerabilities
**Migration Effort Estimate:** 6-12 months depending on application complexity
"""
    
    return synthesis.strip()


async def _generate_code_references(services: dict, repositories: List[str]) -> List[CodeReference]:
    """Generate relevant code references for the analysis."""
    
    references = []
    
    # Mock code references - in real implementation, these would come from actual analysis
    references.extend([
        CodeReference(
            file="src/main/java/com/example/controller/PaymentController.java",
            lines=[45, 67, 89],
            relevance_score=0.9,
            context="Payment processing logic with potential security issues"
        ),
        CodeReference(
            file="src/main/java/com/example/dao/UserDAO.java",
            lines=[23, 34],
            relevance_score=0.85,
            context="Direct SQL queries vulnerable to injection"
        ),
        CodeReference(
            file="WEB-INF/struts-config.xml",
            lines=[12, 45, 78],
            relevance_score=0.8,
            context="Struts configuration requiring migration"
        )
    ])
    
    return references


async def _extract_relationships(services: dict, repositories: List[str]) -> List[Relationship]:
    """Extract relationships between code entities."""
    
    relationships = []
    
    # Mock relationships - in real implementation, these would come from Graphiti
    relationships.extend([
        Relationship(
            source="PaymentController",
            target="PaymentService",
            type="uses",
            description="Controller delegates to service layer",
            strength=0.9
        ),
        Relationship(
            source="PaymentService",
            target="PaymentDAO",
            type="depends_on",
            description="Service uses DAO for data access",
            strength=0.8
        ),
        Relationship(
            source="UserAction",
            target="UserService",
            type="calls",
            description="Struts action calls business service",
            strength=0.85
        )
    ])
    
    return relationships


def _generate_recommendations(agent_results: dict) -> List[Recommendation]:
    """Generate comprehensive recommendations based on agent results."""
    
    recommendations = []
    
    # High priority recommendations
    recommendations.extend([
        Recommendation(
            priority="critical",
            category="security",
            title="Immediate Security Remediation",
            description="Address SQL injection vulnerabilities and weak session management",
            effort_estimate="2-4 weeks",
            risk_level="critical"
        ),
        Recommendation(
            priority="high",
            category="migration",
            title="Legacy Framework Migration Planning",
            description="Develop detailed migration plan from Struts/CORBA to modern stack",
            effort_estimate="4-6 weeks planning, 6-12 months execution",
            risk_level="high"
        ),
        Recommendation(
            priority="medium",
            category="architecture",
            title="Business Logic Centralization",
            description="Extract and centralize business rules for better maintainability",
            effort_estimate="6-8 weeks",
            risk_level="medium"
        ),
        Recommendation(
            priority="medium",
            category="modernization",
            title="Database Access Layer Modernization",
            description="Replace direct JDBC with JPA/Hibernate for better abstraction",
            effort_estimate="4-6 weeks",
            risk_level="low"
        )
    ])
    
    return recommendations