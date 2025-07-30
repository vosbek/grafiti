import os
import sys
import subprocess
import platform
import time
import shutil
import argparse
from pathlib import Path

print("Demo script starting...")

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def detect_container_engine():
    print("Detecting container engine...")
    # Check for podman first (preferred)
    if shutil.which('podman'):
        print("Found Podman")
        # Test if podman is working
        try:
            result = subprocess.run(['podman', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"Podman version: {result.stdout.strip()}")
                return 'podman'
            else:
                print(f"Podman found but not working: {result.stderr}")
        except Exception as e:
            print(f"Podman test failed: {e}")
    
    # Fallback to docker
    if shutil.which('docker'):
        print("Found Docker")
        return 'docker'
    
    print("ERROR: Neither Docker nor Podman found or working")
    return None

def run_command(command, check=True):
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout or '', e.stderr or str(e)
    except Exception as e:
        return False, '', str(e)

def check_status():
    print("Checking service status...")
    container_engine = detect_container_engine()
    if not container_engine:
        print("Cannot check status - no container engine available")
        return False
    
    print(f"Using {container_engine} to check services...")
    
    services = ['neo4j-codeanalysis', 'redis-codeanalysis', 'codeanalysis-backend', 'codeanalysis-frontend']
    for service in services:
        print(f"Checking {service}...")
        
        # Use simpler ps command for podman
        success, stdout, stderr = run_command([
            container_engine, 'ps', '-a', '--filter', f'name={service}'
        ], check=False)
        
        print(f"Command result: success={success}")
        if stdout:
            print(f"Output: {stdout}")
        if stderr:
            print(f"Error: {stderr}")
        
        if success and service in stdout and 'Up' in stdout:
            print(f"{Color.GREEN}✅ {service} is running{Color.END}")
        elif success and service in stdout:
            print(f"{Color.YELLOW}⚠️  {service} exists but may not be running{Color.END}")
        else:
            print(f"{Color.RED}❌ {service} is not running{Color.END}")
    
    return True

def create_demo_config():
    """Create demo configuration without AWS"""
    print("Creating demo configuration...")
    project_root = Path(__file__).parent
    backend_env = project_root / 'backend' / '.env'
    
    env_content = """# Demo Configuration - No AWS Required
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123
REDIS_URL=redis://redis:6379

# Disable AWS Bedrock for demo
AWS_BEDROCK_PROXY=false
GRAPHITI_LLM_PROVIDER=
GRAPHITI_API_KEY=

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
WORKERS=2
ENVIRONMENT=development
REPOSITORY_BASE_PATH=./repositories
WORKSPACE_DIR=workspace
USE_GPU=false
"""
    
    # Create backend directory if it doesn't exist
    backend_env.parent.mkdir(exist_ok=True)
    backend_env.write_text(env_content)
    
    # Also create frontend .env.local
    frontend_env = project_root / 'frontend' / '.env.local'
    frontend_env.parent.mkdir(exist_ok=True)
    frontend_env_content = """REACT_APP_API_URL=http://localhost:8001
REACT_APP_DEBUG=true
"""
    frontend_env.write_text(frontend_env_content)
    
    print(f"{Color.GREEN}✅ Demo configuration created{Color.END}")

def build_images():
    """Build backend and frontend Docker images"""
    print("Building application images...")
    container_engine = detect_container_engine()
    if not container_engine:
        return False
    
    project_root = Path(__file__).parent
    
    # Build backend image (skip import tests for demo)
    print("Building backend image...")
    backend_build_cmd = [
        container_engine, 'build',
        '-f', 'docker/Dockerfile.backend',
        '-t', 'localhost/codeanalysis-backend:demo',
        '--target', 'base',  # Use base target to skip import tests
        '--build-arg', 'ENVIRONMENT=development',
        '--build-arg', 'ENABLE_GPU=false',
        '.'
    ]
    
    success, stdout, stderr = run_command(backend_build_cmd, check=False)
    if success:
        print(f"{Color.GREEN}✅ Backend image built{Color.END}")
    else:
        print(f"{Color.RED}❌ Backend build failed: {stderr}{Color.END}")
        return False
    
    # Build frontend image
    print("Building frontend image...")
    frontend_build_cmd = [
        container_engine, 'build',
        '-f', 'docker/Dockerfile.frontend',
        '-t', 'localhost/codeanalysis-frontend:demo',
        '--target', 'development',
        '.'
    ]
    
    success, stdout, stderr = run_command(frontend_build_cmd, check=False)
    if success:
        print(f"{Color.GREEN}✅ Frontend image built{Color.END}")
    else:
        print(f"{Color.RED}❌ Frontend build failed: {stderr}{Color.END}")
        return False
    
    return True

def stop_services():
    """Stop all services"""
    print("Stopping all services...")
    container_engine = detect_container_engine()
    if not container_engine:
        return False
    
    services = ['neo4j-codeanalysis', 'redis-codeanalysis', 'codeanalysis-backend', 'codeanalysis-frontend']
    for service in services:
        print(f"Stopping {service}...")
        success, _, _ = run_command([container_engine, 'stop', service], check=False)
        if success:
            print(f"{Color.GREEN}✅ Stopped {service}{Color.END}")
        
        success, _, _ = run_command([container_engine, 'rm', service], check=False)
        if success:
            print(f"{Color.GREEN}✅ Removed {service}{Color.END}")
    
    # Remove network
    run_command([container_engine, 'network', 'rm', 'codeanalysis-network'], check=False)
    print(f"{Color.GREEN}✅ Cleaned up network{Color.END}")
    return True

def start_services():
    """Start core services"""
    print("Starting services...")
    container_engine = detect_container_engine()
    if not container_engine:
        return False
    
    # Stop existing services first
    stop_services()
    
    # Create network
    print("Creating network...")
    success, _, stderr = run_command([container_engine, 'network', 'create', 'codeanalysis-network'])
    if success:
        print(f"{Color.GREEN}✅ Created network{Color.END}")
    else:
        print(f"{Color.YELLOW}⚠️  Network creation: {stderr}{Color.END}")
    
    # Start Neo4j with different ports to avoid conflicts
    print("Starting Neo4j...")
    neo4j_cmd = [
        container_engine, 'run', '-d',
        '--name', 'neo4j-codeanalysis',
        '--network', 'codeanalysis-network',
        '-p', '7475:7474', '-p', '7688:7687',  # Use different external ports
        '-e', 'NEO4J_AUTH=neo4j/codeanalysis123',
        '-e', 'NEO4J_PLUGINS=["apoc"]',
        'neo4j:5.15'
    ]
    
    success, _, stderr = run_command(neo4j_cmd)
    if success:
        print(f"{Color.GREEN}✅ Neo4j started{Color.END}")
    else:
        print(f"{Color.RED}❌ Neo4j failed: {stderr}{Color.END}")
        return False
    
    # Start Redis with different port to avoid conflicts
    print("Starting Redis...")
    redis_cmd = [
        container_engine, 'run', '-d',
        '--name', 'redis-codeanalysis',
        '--network', 'codeanalysis-network',
        '-p', '6380:6379',  # Use different external port
        'redis:7-alpine'
    ]
    
    success, _, stderr = run_command(redis_cmd)
    if success:
        print(f"{Color.GREEN}✅ Redis started{Color.END}")
    else:
        print(f"{Color.RED}❌ Redis failed: {stderr}{Color.END}")
        return False
    
    print("Waiting for infrastructure services to be ready...")
    time.sleep(15)
    
    return True

def start_application():
    """Start backend and frontend application containers"""
    print("Starting application containers...")
    container_engine = detect_container_engine()
    if not container_engine:
        return False
    
    # Start backend
    print("Starting backend application...")
    backend_cmd = [
        container_engine, 'run', '-d',
        '--name', 'codeanalysis-backend',
        '--network', 'codeanalysis-network',
        '-p', '8001:8000',  # Use port 8001 to avoid conflicts
        '--env-file', 'backend/.env',
        '-v', f'{Path.cwd()}/backend:/app/backend',
        '-v', f'{Path.cwd()}/workspace:/app/workspace',
        'localhost/codeanalysis-backend:demo'  # Use localhost prefix for local images
    ]
    
    success, _, stderr = run_command(backend_cmd)
    if success:
        print(f"{Color.GREEN}✅ Backend started{Color.END}")
    else:
        print(f"{Color.RED}❌ Backend failed: {stderr}{Color.END}")
        return False
    
    # Start frontend
    print("Starting frontend application...")
    frontend_cmd = [
        container_engine, 'run', '-d',
        '--name', 'codeanalysis-frontend',
        '--network', 'codeanalysis-network',
        '-p', '3001:3000',  # Use port 3001 to avoid conflicts
        '--env-file', 'frontend/.env.local',
        '-v', f'{Path.cwd()}/frontend:/app/frontend',
        'localhost/codeanalysis-frontend:demo'  # Use localhost prefix for local images
    ]
    
    success, _, stderr = run_command(frontend_cmd)
    if success:
        print(f"{Color.GREEN}✅ Frontend started{Color.END}")
    else:
        print(f"{Color.RED}❌ Frontend failed: {stderr}{Color.END}")
        return False
    
    print("Waiting for application services to be ready...")
    time.sleep(20)
    
    return True

def print_summary(full_app=False):
    """Print access information"""
    if full_app:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 Complete CodeAnalysis Demo Running!{Color.END}")
        print(f"\n{Color.CYAN}🌐 Application Access:{Color.END}")
        print(f"Frontend Dashboard: {Color.CYAN}http://localhost:3001{Color.END}")
        print(f"Backend API: {Color.CYAN}http://localhost:8001{Color.END}")
        print(f"API Documentation: {Color.CYAN}http://localhost:8001/docs{Color.END}")
        print(f"\n{Color.CYAN}🗄️  Database Access:{Color.END}")
        print(f"Neo4j Browser: {Color.CYAN}http://localhost:7475{Color.END}")
        print(f"Neo4j Credentials: neo4j / codeanalysis123")
        print(f"Redis: localhost:6380")
        print(f"\n{Color.GREEN}✨ Features Available:{Color.END}")
        print(f"• Java code parsing and analysis")
        print(f"• CodeBERT semantic embeddings")
        print(f"• Knowledge graph visualization")
        print(f"• Multi-agent analysis system")
        print(f"• Repository management")
        print(f"\n{Color.YELLOW}⚠️  Demo Limitations:{Color.END}")
        print(f"• No AWS Bedrock (LLM features limited)")
        print(f"• Using alternate ports to avoid conflicts")
    else:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 Demo Infrastructure Started!{Color.END}")
        print(f"\n{Color.CYAN}Access Information:{Color.END}")
        print(f"Neo4j Browser: {Color.CYAN}http://localhost:7475{Color.END}")
        print(f"Neo4j Credentials: neo4j / codeanalysis123")
        print(f"Redis: localhost:6380")
        print(f"\n{Color.YELLOW}Note: Using alternate ports to avoid conflicts{Color.END}")
        print(f"{Color.YELLOW}Neo4j: 7475 (HTTP), 7688 (Bolt){Color.END}")
        print(f"{Color.YELLOW}Redis: 6380{Color.END}")

def main():
    print("Main function starting...")
    parser = argparse.ArgumentParser(description='CodeAnalysis Demo Setup')
    parser.add_argument('--status', action='store_true', help='Check service status')
    parser.add_argument('--stop', action='store_true', help='Stop all services')
    parser.add_argument('--infra-only', action='store_true', help='Start infrastructure only (Neo4j + Redis)')
    parser.add_argument('--build', action='store_true', help='Build application images')
    
    args = parser.parse_args()
    print(f"Args: status={args.status}, stop={args.stop}, infra_only={args.infra_only}, build={args.build}")
    
    if args.status:
        check_status()
    elif args.stop:
        stop_services()
    elif args.build:
        print("Building application images...")
        create_demo_config()
        if build_images():
            print(f"{Color.GREEN}✅ Images built successfully{Color.END}")
        else:
            print(f"{Color.RED}❌ Failed to build images{Color.END}")
    elif args.infra_only:
        print("Starting infrastructure only...")
        create_demo_config()
        if start_services():
            print_summary(full_app=False)
        else:
            print(f"{Color.RED}❌ Failed to start infrastructure{Color.END}")
    else:
        print("Starting complete demo setup...")
        create_demo_config()
        
        # Start infrastructure
        if not start_services():
            print(f"{Color.RED}❌ Failed to start infrastructure{Color.END}")
            return
        
        # Build images
        print("\nBuilding application images...")
        if not build_images():
            print(f"{Color.RED}❌ Failed to build images{Color.END}")
            return
        
        # Start applications
        print("\nStarting application containers...")
        if start_application():
            print_summary(full_app=True)
        else:
            print(f"{Color.RED}❌ Failed to start applications{Color.END}")
            print(f"{Color.YELLOW}Infrastructure is still running. Use --infra-only to see access info.{Color.END}")

if __name__ == '__main__':
    main()