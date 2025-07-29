"""
Health check API routes.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..models.requests import HealthCheckRequest
from ..models.responses import HealthCheckResponse, ServiceStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(request: Request, detailed: bool = False, include_metrics: bool = False):
    """
    Basic health check endpoint.
    
    Returns the status of all system components and optionally detailed metrics.
    """
    
    try:
        # Get services from application state
        services = getattr(request.app.state, 'services', {})
        
        # Check individual service health
        service_status = {}
        overall_healthy = True
        
        # Check Graphiti service
        if 'graphiti' in services:
            try:
                # Simple connectivity test - this would be implemented in the service
                graphiti_service = services['graphiti']
                # For now, assume it's healthy if it exists
                service_status['graphiti'] = ServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"Graphiti health check failed: {e}")
                service_status['graphiti'] = ServiceStatus.UNHEALTHY
                overall_healthy = False
        else:
            service_status['graphiti'] = ServiceStatus.UNKNOWN
            overall_healthy = False
        
        # Check CodeBERT service
        if 'codebert' in services:
            try:
                codebert_service = services['codebert']
                # Check if model is loaded
                if hasattr(codebert_service, 'model') and codebert_service.model is not None:
                    service_status['codebert'] = ServiceStatus.HEALTHY
                else:
                    service_status['codebert'] = ServiceStatus.DEGRADED
            except Exception as e:
                logger.warning(f"CodeBERT health check failed: {e}")
                service_status['codebert'] = ServiceStatus.UNHEALTHY
                overall_healthy = False
        else:
            service_status['codebert'] = ServiceStatus.UNKNOWN
            overall_healthy = False
        
        # Check Repository service
        if 'repository' in services:
            try:
                repo_service = services['repository']
                # Check if workspace directory is accessible
                if hasattr(repo_service, 'workspace_dir'):
                    service_status['repository'] = ServiceStatus.HEALTHY
                else:
                    service_status['repository'] = ServiceStatus.DEGRADED
            except Exception as e:
                logger.warning(f"Repository service health check failed: {e}")
                service_status['repository'] = ServiceStatus.UNHEALTHY
                overall_healthy = False
        else:
            service_status['repository'] = ServiceStatus.UNKNOWN
            overall_healthy = False
        
        # Check Agent service (if available)
        if 'agents' in services:
            try:
                agent_service = services['agents']
                service_status['agents'] = ServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"Agent service health check failed: {e}")
                service_status['agents'] = ServiceStatus.UNHEALTHY
                overall_healthy = False
        else:
            service_status['agents'] = ServiceStatus.UNKNOWN
        
        # Determine overall status
        overall_status = ServiceStatus.HEALTHY if overall_healthy else ServiceStatus.DEGRADED
        
        # Prepare response
        response_data = {
            "success": True,
            "status": overall_status,
            "services": service_status,
            "timestamp": datetime.now()
        }
        
        # Add system information if detailed
        if detailed:
            response_data["system"] = await _get_system_info(request)
        
        # Add metrics if requested
        if include_metrics:
            response_data["metrics"] = await _get_system_metrics(services)
        
        return HealthCheckResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health_check(request: Request):
    """Detailed health check with system information and metrics."""
    
    return await health_check(request, detailed=True, include_metrics=True)


async def _get_system_info(request: Request) -> Dict[str, Any]:
    """Get detailed system information."""
    
    try:
        import psutil
        import torch
        
        # CPU information
        cpu_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # GPU information
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name() if torch.cuda.is_available() else None
            }
            
            # Add memory info for each GPU
            for i in range(torch.cuda.device_count()):
                gpu_info[f"device_{i}_memory"] = {
                    "allocated": torch.cuda.memory_allocated(i),
                    "reserved": torch.cuda.memory_reserved(i)
                }
        else:
            gpu_info = {"available": False}
        
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "gpu": gpu_info,
            "python_version": f"{psutil.python_version()}",
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
    except ImportError:
        # psutil not available, return basic info
        return {
            "cpu": {"cpu_count": "unknown"},
            "memory": {"total": "unknown"},
            "note": "Install psutil for detailed system information"
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        return {"error": str(e)}


async def _get_system_metrics(services: Dict[str, Any]) -> Dict[str, Any]:
    """Get system performance metrics."""
    
    metrics = {
        "uptime": "unknown",
        "request_count": 0,
        "error_rate": 0.0
    }
    
    try:
        # Get CodeBERT service metrics
        if 'codebert' in services:
            codebert_service = services['codebert']
            if hasattr(codebert_service, 'get_statistics'):
                codebert_stats = codebert_service.get_statistics()
                metrics["codebert"] = codebert_stats
        
        # Get Repository service metrics
        if 'repository' in services:
            repo_service = services['repository']
            if hasattr(repo_service, 'get_cloned_repositories'):
                cloned_repos = repo_service.get_cloned_repositories()
                metrics["repositories"] = {
                    "total_cloned": len(cloned_repos),
                    "repository_names": [repo.name for repo in cloned_repos]
                }
        
        # Get Graphiti service metrics
        if 'graphiti' in services:
            graphiti_service = services['graphiti']
            metrics["graphiti"] = {
                "java_classes": len(getattr(graphiti_service, 'java_classes', {})),
                "java_methods": len(getattr(graphiti_service, 'java_methods', {})),
                "business_rules": len(getattr(graphiti_service, 'business_rules', {}))
            }
        
    except Exception as e:
        logger.warning(f"Failed to get metrics: {e}")
        metrics["error"] = str(e)
    
    return metrics


@router.get("/health/services")
async def service_health(request: Request):
    """Get health status of individual services."""
    
    services = getattr(request.app.state, 'services', {})
    
    service_details = {}
    
    for service_name, service in services.items():
        try:
            # Try to get service-specific health info
            if hasattr(service, 'get_health_status'):
                status = await service.get_health_status()
            else:
                # Default to healthy if service exists
                status = {
                    "status": "healthy",
                    "message": f"{service_name} service is running"
                }
            
            service_details[service_name] = status
            
        except Exception as e:
            service_details[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "services": service_details,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/readiness")
async def readiness_check(request: Request):
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if the service is ready to receive traffic.
    """
    
    services = getattr(request.app.state, 'services', {})
    
    # Check that critical services are available
    critical_services = ['codebert', 'repository']
    
    for service_name in critical_services:
        if service_name not in services:
            return JSONResponse(
                status_code=503,
                content={"ready": False, "missing_service": service_name}
            )
    
    return {"ready": True, "timestamp": datetime.now().isoformat()}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if the service is alive (basic health check).
    """
    
    return {"alive": True, "timestamp": datetime.now().isoformat()}