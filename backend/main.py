"""
Main FastAPI application entry point for CodeAnalysis MultiAgent MVP.

This module initializes the FastAPI application, sets up all services,
and configures the API routes for the enterprise code analysis system.
"""

import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Service imports
from app.services.java_parser_service import JavaParserService
from app.services.codebert_service import CodeBERTService
from app.services.graphiti_service import GraphitiService
from app.services.repository_service import RepositoryService

# API route imports
from app.api.routes import (
    health_router,
    repositories_router,
    analysis_router,
    search_router,
    agents_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codeanalysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global services storage
services: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown procedures for all services.
    """
    
    # Startup
    logger.info("Starting CodeAnalysis MultiAgent MVP application...")
    
    try:
        # Initialize services
        await initialize_services()
        
        # Store services in app state
        app.state.services = services
        
        logger.info("All services initialized successfully")
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down CodeAnalysis MultiAgent MVP application...")
    
    try:
        await shutdown_services()
        logger.info("All services shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def initialize_services():
    """Initialize all application services."""
    
    logger.info("Initializing application services...")
    
    # Initialize Java Parser Service
    try:
        logger.info("Initializing Java Parser Service...")
        java_parser_service = JavaParserService()
        await java_parser_service.initialize()
        services['java_parser'] = java_parser_service
        logger.info("Java Parser Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Java Parser Service: {e}")
        raise
    
    # Initialize Repository Service
    try:
        logger.info("Initializing Repository Service...")
        
        # Get workspace directory from environment or use default
        workspace_dir = os.getenv('WORKSPACE_DIR', 'workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        
        repository_service = RepositoryService(workspace_dir=workspace_dir)
        await repository_service.initialize()
        services['repository'] = repository_service
        logger.info(f"Repository Service initialized with workspace: {workspace_dir}")
    except Exception as e:
        logger.error(f"Failed to initialize Repository Service: {e}")
        raise
    
    # Initialize CodeBERT Service
    try:
        logger.info("Initializing CodeBERT Service...")
        
        # Check for GPU availability
        use_gpu = os.getenv('USE_GPU', 'true').lower() == 'true'
        model_name = os.getenv('CODEBERT_MODEL', 'microsoft/codebert-base')
        
        codebert_service = CodeBERTService(
            model_name=model_name,
            use_gpu=use_gpu,
            cache_size=int(os.getenv('CODEBERT_CACHE_SIZE', '10000'))
        )
        await codebert_service.initialize()
        services['codebert'] = codebert_service
        logger.info(f"CodeBERT Service initialized with model: {model_name}")
    except Exception as e:
        logger.error(f"Failed to initialize CodeBERT Service: {e}")
        # Continue without CodeBERT if it fails (for development)
        logger.warning("Continuing without CodeBERT service")
    
    # Initialize Graphiti Service
    try:
        logger.info("Initializing Graphiti Service...")
        
        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        
        # Get LLM configuration from environment
        llm_provider = os.getenv('GRAPHITI_LLM_PROVIDER', 'openai')
        llm_model = os.getenv('GRAPHITI_LLM_MODEL', 'gpt-4')
        llm_api_key = os.getenv('GRAPHITI_API_KEY')
        llm_base_url = os.getenv('GRAPHITI_BASE_URL')
        
        # AWS Bedrock specific configuration
        aws_bedrock_proxy = os.getenv('AWS_BEDROCK_PROXY', 'false').lower() == 'true'
        bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Get CodeBERT service for custom embedder
        codebert_service = services.get('codebert')
        
        graphiti_service = GraphitiService(
            uri=neo4j_uri,
            user=neo4j_username,
            password=neo4j_password,
            codebert_service=codebert_service,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            aws_bedrock_proxy=aws_bedrock_proxy,
            bedrock_model_id=bedrock_model_id,
            aws_region=aws_region
        )
        await graphiti_service.initialize()
        services['graphiti'] = graphiti_service
        
        if aws_bedrock_proxy:
            logger.info("Graphiti Service initialized with AWS Bedrock proxy support")
        else:
            logger.info(f"Graphiti Service initialized with {llm_provider}")
            
    except Exception as e:
        logger.error(f"Failed to initialize Graphiti Service: {e}")
        # Continue without Graphiti if it fails (for development)
        logger.warning("Continuing without Graphiti service")
        
        if aws_bedrock_proxy:
            logger.error("Bedrock proxy setup required. See docs/BEDROCK_SETUP.md for instructions")
    
    logger.info(f"Successfully initialized {len(services)} services")


async def shutdown_services():
    """Shutdown all application services."""
    
    logger.info("Shutting down application services...")
    
    for service_name, service in services.items():
        try:
            if hasattr(service, 'shutdown'):
                await service.shutdown()
                logger.info(f"{service_name} service shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down {service_name} service: {e}")
    
    services.clear()
    logger.info("All services shut down")


# Create FastAPI application
app = FastAPI(
    title="CodeAnalysis MultiAgent MVP",
    description="""
    Enterprise-scale Java code analysis system combining CodeBERT embeddings, 
    Graphiti knowledge graph, and multi-agent orchestration for comprehensive 
    analysis of legacy Java applications (Struts, CORBA, EJB).
    
    ## Features
    
    - **Semantic Code Search**: Natural language search using CodeBERT embeddings
    - **Multi-Agent Analysis**: Specialized agents for architecture, security, migration planning
    - **Knowledge Graph**: Temporal knowledge graph with Graphiti for relationship mapping
    - **Repository Management**: Automated discovery and cloning of repository dependencies
    - **Legacy Framework Support**: Deep analysis of Struts, CORBA, and EJB applications
    - **Enterprise Scale**: Designed for 50-100 repositories with millions of lines of code
    
    ## Architecture
    
    The system uses a microservices architecture with the following components:
    
    - **FastAPI REST API**: Enterprise-grade API with comprehensive endpoints
    - **CodeBERT Service**: Transformer-based semantic code understanding
    - **Graphiti Service**: Neo4j-backed temporal knowledge graph
    - **Repository Service**: Git repository management and dependency discovery
    - **Multi-Agent System**: Specialized analysis agents with orchestration
    
    ## Usage
    
    1. **Repository Discovery**: Use `/api/v1/repositories/discover` to find dependencies
    2. **Repository Cloning**: Use `/api/v1/repositories/clone` to clone repositories
    3. **Comprehensive Analysis**: Use `/api/v1/analysis/comprehensive` for full analysis
    4. **Semantic Search**: Use `/api/v1/search/semantic` for code search
    5. **Agent Execution**: Use `/api/v1/agents/{agent_name}/execute` for specific analysis
    
    """.strip(),
    version="1.0.0",
    contact={
        "name": "CodeAnalysis Team",
        "email": "codeanalysis@example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes with versioning
API_V1_PREFIX = "/api/v1"

# Health and monitoring routes
app.include_router(
    health_router,
    prefix=f"{API_V1_PREFIX}",
    tags=["Health & Monitoring"]
)

# Repository management routes
app.include_router(
    repositories_router,
    prefix=f"{API_V1_PREFIX}/repositories",
    tags=["Repository Management"]
)

# Analysis routes
app.include_router(
    analysis_router,
    prefix=f"{API_V1_PREFIX}/analysis",
    tags=["Code Analysis"]
)

# Search routes
app.include_router(
    search_router,
    prefix=f"{API_V1_PREFIX}/search",
    tags=["Semantic Search"]
)

# Agent management routes
app.include_router(
    agents_router,
    prefix=f"{API_V1_PREFIX}/agents",
    tags=["Multi-Agent System"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing system information."""
    
    return {
        "name": "CodeAnalysis MultiAgent MVP",
        "version": "1.0.0",
        "description": "Enterprise Java code analysis with AI-powered insights",
        "status": "operational",
        "services": {
            "total": len(services),
            "available": list(services.keys())
        },
        "api_version": "v1",
        "documentation": "/docs",
        "health_check": "/api/v1/health"
    }


# System information endpoint
@app.get("/system/info")
async def system_info():
    """Get detailed system information."""
    
    import platform
    import psutil
    
    try:
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": platform.node()
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free
            },
            "services": {
                "total_services": len(services),
                "active_services": list(services.keys()),
                "service_health": {
                    name: "healthy" for name in services.keys()
                }
            },
            "environment": {
                "workspace_dir": os.getenv('WORKSPACE_DIR', 'workspace'),
                "use_gpu": os.getenv('USE_GPU', 'true'),
                "codebert_model": os.getenv('CODEBERT_MODEL', 'microsoft/codebert-base'),
                "neo4j_uri": os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {"error": "Failed to retrieve system information"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    
    logger.error(f"Unhandled exception in {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv('DEBUG', 'false').lower() == 'true' else "An unexpected error occurred",
            "timestamp": str(asyncio.get_event_loop().time())
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions."""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": str(asyncio.get_event_loop().time())
        }
    )


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="CodeAnalysis MultiAgent MVP",
        version="1.0.0",
        description="Enterprise Java code analysis with AI-powered insights",
        routes=app.routes,
    )
    
    # Add custom schema extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Development server configuration
if __name__ == "__main__":
    import uvicorn
    
    # Configuration from environment variables
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    reload = os.getenv('RELOAD', 'false').lower() == 'true'
    
    logger.info(f"Starting CodeAnalysis MultiAgent MVP on {host}:{port}")
    logger.info(f"Debug mode: {debug}, Reload: {reload}")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        debug=debug,
        reload=reload,
        log_level="info" if not debug else "debug",
        access_log=True
    )