#!/usr/bin/env python3
"""
Bootstrap Script for CodeAnalysis-MultiAgent-MVP

Handles final configuration and system setup based on detected hardware and environment.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import structlog

# Add the backend to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from app.config.settings import get_settings
    from app.services.repository_service import RepositoryService
    from app.utils.hardware_detector import HardwareDetector
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure to run this script after installing requirements.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger(__name__)


class SystemBootstrap:
    """Handles system bootstrap and configuration."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = Path(__file__).parent.parent
        self.settings = get_settings()
        
        # Update settings based on detected hardware
        self._configure_for_hardware()
    
    def _configure_for_hardware(self):
        """Configure system settings based on detected hardware."""
        
        # Set device based on GPU availability
        if self.args.gpu_available.lower() == 'true':
            os.environ['DEVICE'] = 'cuda'
            logger.info("GPU acceleration enabled")
        else:
            os.environ['DEVICE'] = 'cpu'
            logger.info("Using CPU-only processing")
        
        # Adjust batch sizes based on memory
        memory_gb = int(self.args.memory_gb)
        if memory_gb >= 32:
            batch_size = 32
        elif memory_gb >= 16:
            batch_size = 16
        elif memory_gb >= 8:
            batch_size = 8
        else:
            batch_size = 4
        
        os.environ['EMBEDDING_BATCH_SIZE'] = str(batch_size)
        logger.info(f"Set embedding batch size to {batch_size} based on {memory_gb}GB RAM")
        
        # Configure thread pool based on CPU cores
        cpu_cores = int(self.args.cpu_cores)
        thread_pool_size = min(cpu_cores * 2, 20)  # Cap at 20
        os.environ['THREAD_POOL_SIZE'] = str(thread_pool_size)
        logger.info(f"Set thread pool size to {thread_pool_size} based on {cpu_cores} CPU cores")
        
        # Cloud-specific optimizations
        if self.args.cloud_provider != 'local':
            logger.info(f"Applying {self.args.cloud_provider} cloud optimizations")
            # Enable more aggressive caching for cloud environments
            os.environ['ENABLE_CACHING'] = 'true'
    
    def create_environment_file(self):
        """Create .env file with detected configuration."""
        
        env_content = f"""# Auto-generated configuration by bootstrap.py
# Hardware Configuration
DEVICE={'cuda' if self.args.gpu_available.lower() == 'true' else 'cpu'}
CPU_CORES={self.args.cpu_cores}
MEMORY_GB={self.args.memory_gb}
GPU_AVAILABLE={self.args.gpu_available}

# Environment
ENVIRONMENT={self.args.environment}
CLOUD_PROVIDER={self.args.cloud_provider}

# Performance Tuning
EMBEDDING_BATCH_SIZE={os.environ.get('EMBEDDING_BATCH_SIZE', '16')}
THREAD_POOL_SIZE={os.environ.get('THREAD_POOL_SIZE', '10')}
MAX_CONCURRENT_CLONES={min(int(self.args.cpu_cores), 8)}

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379

# Application
DEBUG={'true' if self.args.environment == 'development' else 'false'}
LOG_LEVEL={'DEBUG' if self.args.environment == 'development' else 'INFO'}

# Repository Discovery
WORKSPACE_DIR=./repositories
MAX_REPOSITORY_SIZE_GB=10.0
"""
        
        # Add AWS Bedrock configuration if requested
        if hasattr(self.args, 'bedrock') and self.args.bedrock:
            env_content += """
# AWS Bedrock Configuration
AWS_BEDROCK_PROXY=true
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Graphiti LLM Configuration (for Bedrock proxy)
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=bedrock/anthropic.claude-3-sonnet
GRAPHITI_BASE_URL=http://localhost:8001
GRAPHITI_API_KEY=dummy

# CodeBERT Configuration (optimized for Bedrock usage)
CODEBERT_MODEL=microsoft/codebert-base
USE_GPU={'true' if self.args.gpu_available.lower() == 'true' else 'false'}
CODEBERT_CACHE_SIZE=5000
"""
            logger.info("Added AWS Bedrock configuration to environment")
        else:
            env_content += """
# Standard LLM Configuration (configure as needed)
# GRAPHITI_LLM_PROVIDER=openai
# GRAPHITI_LLM_MODEL=gpt-4
# GRAPHITI_API_KEY=your-api-key-here

# CodeBERT Configuration
CODEBERT_MODEL=microsoft/codebert-base
USE_GPU={'true' if self.args.gpu_available.lower() == 'true' else 'false'}
CODEBERT_CACHE_SIZE=10000
"""
        
        env_file = self.project_root / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        if hasattr(self.args, 'bedrock') and self.args.bedrock:
            logger.info(f"Created environment configuration with AWS Bedrock support: {env_file}")
        else:
            logger.info(f"Created environment configuration: {env_file}")
    
    def create_system_info(self):
        """Create system information file for monitoring."""
        
        system_info = {
            "hardware": {
                "cpu_cores": int(self.args.cpu_cores),
                "memory_gb": int(self.args.memory_gb),
                "gpu_available": self.args.gpu_available.lower() == 'true',
                "device": os.environ.get('DEVICE', 'cpu')
            },
            "environment": {
                "type": self.args.environment,
                "cloud_provider": self.args.cloud_provider,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            },
            "configuration": {
                "embedding_batch_size": int(os.environ.get('EMBEDDING_BATCH_SIZE', '16')),
                "thread_pool_size": int(os.environ.get('THREAD_POOL_SIZE', '10')),
                "max_concurrent_clones": min(int(self.args.cpu_cores), 8)
            }
        }
        
        system_info_file = self.project_root / "system_info.json"
        with open(system_info_file, 'w') as f:
            json.dump(system_info, f, indent=2)
        
        logger.info(f"Created system information: {system_info_file}")
    
    async def setup_workspace(self):
        """Set up workspace directories and initial configuration."""
        
        # Create necessary directories
        directories = [
            "repositories",
            "analysis-results", 
            "embeddings",
            "logs",
            "temp"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        
        # Create repositories workspace
        workspace_dir = self.project_root / "repositories"
        if not workspace_dir.exists():
            workspace_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Workspace setup complete")
    
    async def discover_repositories(self):
        """Handle repository discovery if requested."""
        
        if not self.args.discover_from and not self.args.repos:
            logger.info("No repository discovery requested")
            return
        
        try:
            # Initialize repository service
            repo_service = RepositoryService(
                workspace_dir=str(self.project_root / "repositories"),
                max_concurrent_clones=min(int(self.args.cpu_cores), 8)
            )
            
            if self.args.discover_from:
                logger.info(f"Starting repository discovery from: {self.args.discover_from}")
                
                # Discover dependencies
                discovered_repos = await repo_service.discover_dependencies(self.args.discover_from)
                logger.info(f"Discovered {len(discovered_repos)} repositories")
                
                # Clone repositories
                await repo_service.clone_repositories(discovered_repos)
                logger.info("Repository cloning complete")
                
            elif self.args.repos:
                repo_list = [r.strip() for r in self.args.repos.split(',')]
                logger.info(f"Cloning specified repositories: {repo_list}")
                
                await repo_service.clone_repositories(repo_list)
                logger.info("Repository cloning complete")
                
        except Exception as e:
            logger.error(f"Repository discovery failed: {e}")
            # Don't fail bootstrap, just log the error
    
    def create_launch_info(self):
        """Create information for post-startup display."""
        
        launch_info = {
            "status": "ready",
            "endpoints": {
                "web_interface": "http://localhost:8000",
                "api_docs": "http://localhost:8000/docs",
                "health_check": "http://localhost:8000/api/v1/health"
            },
            "system": {
                "cpu_cores": int(self.args.cpu_cores),
                "memory_gb": int(self.args.memory_gb),
                "gpu_available": self.args.gpu_available.lower() == 'true',
                "environment": self.args.environment
            },
            "features": {
                "repository_discovery": bool(self.args.discover_from or self.args.repos),
                "gpu_acceleration": self.args.gpu_available.lower() == 'true'
            }
        }
        
        launch_file = self.project_root / "launch_info.json"
        with open(launch_file, 'w') as f:
            json.dump(launch_info, f, indent=2)
        
        logger.info("System bootstrap complete and ready for launch")
    
    async def run(self):
        """Run the complete bootstrap process."""
        
        logger.info("Starting system bootstrap...")
        
        try:
            # Configuration
            self.create_environment_file()
            self.create_system_info()
            
            # Workspace setup
            await self.setup_workspace()
            
            # Repository discovery (if requested)
            await self.discover_repositories()
            
            # Final setup
            self.create_launch_info()
            
            logger.info("Bootstrap completed successfully!")
            
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            raise


def parse_arguments():
    """Parse command line arguments."""
    
    parser = argparse.ArgumentParser(description="Bootstrap CodeAnalysis-MultiAgent-MVP")
    
    parser.add_argument("--environment", default="development", 
                       help="Environment (development/production)")
    parser.add_argument("--cpu-cores", type=int, default=4, 
                       help="Number of CPU cores")
    parser.add_argument("--memory-gb", type=int, default=8, 
                       help="Amount of RAM in GB")
    parser.add_argument("--gpu-available", default="false", 
                       help="GPU availability (true/false)")
    parser.add_argument("--cloud-provider", default="local", 
                       help="Cloud provider (aws/gcp/azure/local)")
    parser.add_argument("--discover-from", 
                       help="Repository URL to start discovery from")
    parser.add_argument("--repos", 
                       help="Comma-separated list of repositories to clone")
    parser.add_argument("--bedrock", action="store_true",
                       help="Configure for AWS Bedrock integration with proxy")
    
    return parser.parse_args()


async def main():
    """Main bootstrap function."""
    
    args = parse_arguments()
    
    bootstrap = SystemBootstrap(args)
    await bootstrap.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        sys.exit(1)