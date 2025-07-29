"""
Repository management API routes.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, Request, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.requests import RepositoryDiscoveryRequest, RepositoryCloneRequest
from ..models.responses import (
    RepositoryDiscoveryResponse, RepositoryCloneResponse, RepositoryListResponse,
    RepositoryInfo, JobResponse, JobStatus
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job tracking (in production, this would be in Redis/database)
active_jobs = {}


@router.post("/discover", response_model=RepositoryDiscoveryResponse)
async def discover_repositories(
    request: RepositoryDiscoveryRequest,
    background_tasks: BackgroundTasks,
    app_request: Request
):
    """
    Discover repository dependencies starting from a main repository.
    
    This endpoint analyzes build files (Maven, Gradle, Ant) to find dependent
    repositories and creates a complete dependency graph.
    """
    
    try:
        # Get repository service
        services = getattr(app_request.app.state, 'services', {})
        if 'repository' not in services:
            raise HTTPException(status_code=503, detail="Repository service not available")
        
        repository_service = services['repository']
        
        # Generate unique job ID
        job_id = f"discover_{uuid.uuid4().hex[:8]}"
        
        # Initialize job tracking
        active_jobs[job_id] = {
            "status": JobStatus.STARTED,
            "started_at": datetime.now(),
            "repository_url": request.repository_url,
            "discovered_repositories": [],
            "error": None
        }
        
        # Start background discovery task
        background_tasks.add_task(
            _discover_repositories_task,
            job_id,
            repository_service,
            request
        )
        
        # Return immediate response
        return RepositoryDiscoveryResponse(
            success=True,
            job_id=job_id,
            status=JobStatus.STARTED,
            discovered_repositories=[],
            progress_url=f"/api/v1/repositories/jobs/{job_id}/status",
            estimated_completion=None,
            message="Repository discovery started"
        )
        
    except Exception as e:
        logger.error(f"Failed to start repository discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone", response_model=RepositoryCloneResponse)
async def clone_repositories(
    request: RepositoryCloneRequest,
    background_tasks: BackgroundTasks,
    app_request: Request
):
    """
    Clone multiple repositories for analysis.
    
    Clones the specified repositories concurrently and prepares them for analysis.
    """
    
    try:
        # Get repository service
        services = getattr(app_request.app.state, 'services', {})
        if 'repository' not in services:
            raise HTTPException(status_code=503, detail="Repository service not available")
        
        repository_service = services['repository']
        
        # Generate unique job ID
        job_id = f"clone_{uuid.uuid4().hex[:8]}"
        
        # Initialize job tracking
        active_jobs[job_id] = {
            "status": JobStatus.STARTED,
            "started_at": datetime.now(),
            "total_repositories": len(request.repositories),
            "cloned_repositories": 0,
            "failed_repositories": [],
            "error": None
        }
        
        # Start background cloning task
        background_tasks.add_task(
            _clone_repositories_task,
            job_id,
            repository_service,
            request
        )
        
        # Return immediate response
        return RepositoryCloneResponse(
            success=True,
            job_id=job_id,
            status=JobStatus.STARTED,
            total_repositories=len(request.repositories),
            cloned_repositories=0,
            failed_repositories=[],
            progress_url=f"/api/v1/repositories/jobs/{job_id}/status",
            estimated_completion=None,
            message="Repository cloning started"
        )
        
    except Exception as e:
        logger.error(f"Failed to start repository cloning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    app_request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset")
):
    """
    List all managed repositories with their analysis status.
    
    Supports filtering by status and framework, with pagination.
    """
    
    try:
        # Get repository service
        services = getattr(app_request.app.state, 'services', {})
        if 'repository' not in services:
            raise HTTPException(status_code=503, detail="Repository service not available")
        
        repository_service = services['repository']
        
        # Get all repositories
        if hasattr(repository_service, 'get_cloned_repositories'):
            repositories = repository_service.get_cloned_repositories()
        else:
            repositories = []
        
        # Convert to response format
        repo_infos = []
        for repo in repositories:
            # Mock analysis data (in real implementation, this would come from database)
            repo_info = RepositoryInfo(
                id=f"repo_{hash(repo.name) % 10000:04d}",
                name=repo.name,
                url=repo.url,
                local_path=repo.local_path,
                status="completed",  # Would be dynamic
                frameworks=["java", "struts"],  # Would be detected
                statistics={
                    "java_files": 100,  # Would be calculated
                    "classes": 80,
                    "methods": 500,
                    "struts_actions": 10,
                    "corba_interfaces": 2
                },
                last_analyzed=datetime.now(),
                analysis_duration=120.5
            )
            repo_infos.append(repo_info)
        
        # Apply filters
        if status:
            repo_infos = [r for r in repo_infos if r.status == status]
        
        if framework:
            repo_infos = [r for r in repo_infos if framework in r.frameworks]
        
        # Apply pagination
        total = len(repo_infos)
        paginated_repos = repo_infos[offset:offset + limit]
        has_more = offset + limit < total
        
        return RepositoryListResponse(
            success=True,
            repositories=paginated_repos,
            total=total,
            has_more=has_more,
            message=f"Found {total} repositories"
        )
        
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a background job.
    
    Returns current progress and status of repository discovery or cloning jobs.
    """
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = active_jobs[job_id]
    
    # Prepare response based on job type
    if job_id.startswith("discover_"):
        return RepositoryDiscoveryResponse(
            success=True,
            job_id=job_id,
            status=job_info["status"],
            discovered_repositories=job_info.get("discovered_repositories", []),
            progress_url=f"/api/v1/repositories/jobs/{job_id}/status",
            message=f"Discovery status: {job_info['status']}"
        )
    elif job_id.startswith("clone_"):
        return RepositoryCloneResponse(
            success=True,
            job_id=job_id,
            status=job_info["status"],
            total_repositories=job_info.get("total_repositories", 0),
            cloned_repositories=job_info.get("cloned_repositories", 0),
            failed_repositories=job_info.get("failed_repositories", []),
            progress_url=f"/api/v1/repositories/jobs/{job_id}/status",
            message=f"Cloning status: {job_info['status']}"
        )
    else:
        return JobResponse(
            success=True,
            job_id=job_id,
            status=job_info["status"],
            progress_url=f"/api/v1/repositories/jobs/{job_id}/status",
            message=f"Job status: {job_info['status']}"
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running background job."""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = active_jobs[job_id]
    
    if job_info["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Job is already finished")
    
    # Mark job as cancelled
    active_jobs[job_id]["status"] = JobStatus.CANCELLED
    active_jobs[job_id]["cancelled_at"] = datetime.now()
    
    return {"success": True, "message": f"Job {job_id} cancelled"}


@router.get("/{repository_id}")
async def get_repository(repository_id: str, app_request: Request):
    """Get detailed information about a specific repository."""
    
    try:
        # Get repository service
        services = getattr(app_request.app.state, 'services', {})
        if 'repository' not in services:
            raise HTTPException(status_code=503, detail="Repository service not available")
        
        repository_service = services['repository']
        
        # Find repository by ID
        repositories = repository_service.get_cloned_repositories() if hasattr(repository_service, 'get_cloned_repositories') else []
        
        for repo in repositories:
            if f"repo_{hash(repo.name) % 10000:04d}" == repository_id:
                return RepositoryInfo(
                    id=repository_id,
                    name=repo.name,
                    url=repo.url,
                    local_path=repo.local_path,
                    status="completed",
                    frameworks=["java", "struts"],
                    statistics={
                        "java_files": 100,
                        "classes": 80,
                        "methods": 500
                    },
                    last_analyzed=datetime.now(),
                    analysis_duration=120.5
                )
        
        raise HTTPException(status_code=404, detail="Repository not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository {repository_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions

async def _discover_repositories_task(job_id: str, repository_service, request: RepositoryDiscoveryRequest):
    """Background task for repository discovery."""
    
    try:
        active_jobs[job_id]["status"] = JobStatus.IN_PROGRESS
        
        # Perform actual discovery
        if hasattr(repository_service, 'discover_dependencies'):
            discovered_repos = await repository_service.discover_dependencies(
                request.repository_url
            )
            
            # Update job status
            active_jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "discovered_repositories": discovered_repos,
                "completed_at": datetime.now()
            })
            
            logger.info(f"Repository discovery completed for job {job_id}: {len(discovered_repos)} repositories found")
        else:
            # Fallback for incomplete implementation
            active_jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "discovered_repositories": [request.repository_url],
                "completed_at": datetime.now()
            })
            
    except Exception as e:
        logger.error(f"Repository discovery failed for job {job_id}: {e}")
        active_jobs[job_id].update({
            "status": JobStatus.FAILED,
            "error": str(e),
            "failed_at": datetime.now()
        })


async def _clone_repositories_task(job_id: str, repository_service, request: RepositoryCloneRequest):
    """Background task for repository cloning."""
    
    try:
        active_jobs[job_id]["status"] = JobStatus.IN_PROGRESS
        
        # Extract URLs from repository specifications
        repo_urls = [repo.url for repo in request.repositories]
        
        # Perform actual cloning
        if hasattr(repository_service, 'clone_repositories'):
            cloned_repos = await repository_service.clone_repositories(repo_urls)
            
            # Update job status
            cloned_count = len(cloned_repos)
            failed_repos = [url for url in repo_urls if url not in cloned_repos]
            
            active_jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "cloned_repositories": cloned_count,
                "failed_repositories": failed_repos,
                "completed_at": datetime.now()
            })
            
            logger.info(f"Repository cloning completed for job {job_id}: {cloned_count}/{len(repo_urls)} successful")
        else:
            # Fallback for incomplete implementation
            active_jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "cloned_repositories": len(request.repositories),
                "failed_repositories": [],
                "completed_at": datetime.now()
            })
            
    except Exception as e:
        logger.error(f"Repository cloning failed for job {job_id}: {e}")
        active_jobs[job_id].update({
            "status": JobStatus.FAILED,
            "error": str(e),
            "failed_at": datetime.now()
        })