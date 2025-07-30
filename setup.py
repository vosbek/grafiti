#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Complete Setup Script

Single entry point for Windows/Linux with Podman/Docker support.
Validates AWS credentials, tears down existing services, and starts everything.

Usage:
    python setup.py                    # Full setup with validation
    python setup.py --quick           # Skip validation, start services
    python setup.py --teardown-only   # Only teardown existing services
    python setup.py --validate-only   # Only validate setup
"""

import os
import sys
import subprocess
import platform
import json
import time
import shutil
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CodeAnalysisSetup:
    """Complete setup manager for CodeAnalysis MultiAgent MVP"""
    
    def __init__(self, args):
        self.args = args
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system().lower() == 'windows'
        self.container_engine = self._detect_container_engine()
        self.errors = []
        self.warnings = []
        
        # Service configuration
        self.services = {
            'neo4j': {'port': 7687, 'health_port': 7474, 'container': 'neo4j-codeanalysis'},
            'redis': {'port': 6379, 'container': 'redis-codeanalysis'},
            'bedrock-proxy': {'port': 8001, 'container': 'bedrock-proxy'},
            'backend': {'port': 8000, 'container': 'codeanalysis-backend'},
            'frontend': {'port': 3000, 'container': 'codeanalysis-frontend'}
        }
        
        # Default credentials and configuration
        self.config = {
            'neo4j_password': 'codeanalysis123',
            'bedrock_model': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'aws_region': 'us-east-1',
            'litellm_port': 8001
        }
        
        print(f"{Color.CYAN}{Color.BOLD}🚀 CodeAnalysis MultiAgent MVP Setup{Color.END}")
        print(f"{Color.WHITE}Platform: {platform.system()} | Container: {self.container_engine}{Color.END}\n")
    
    def _detect_container_engine(self) -> str:
        """Detect available container engine (Docker or Podman)"""
        
        # Check for Podman first (preferred on some systems)
        if shutil.which('podman'):
            try:
                result = subprocess.run(['podman', '--version'], 
                                      capture_output=True, text=True, check=True)
                if result.returncode == 0:
                    return 'podman'
            except:
                pass
        
        # Check for Docker
        if shutil.which('docker'):
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True, check=True)
                if result.returncode == 0:
                    return 'docker'
            except:
                pass
        
        raise RuntimeError("Neither Docker nor Podman found. Please install one of them.")
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None, 
                    check: bool = True, shell: bool = False) -> Tuple[bool, str, str]:
        """Execute a command and return success status with output"""
        try:
            if shell and isinstance(command, list):
                command = ' '.join(command)
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check,
                shell=shell
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or '', e.stderr or str(e)
        except Exception as e:
            return False, '', str(e)
    
    def _print_step(self, step: str, description: str = ""):
        """Print formatted step information"""
        print(f"{Color.BLUE}{Color.BOLD}[STEP] {step}{Color.END}")
        if description:
            print(f"{Color.WHITE}  → {description}{Color.END}")
    
    def _print_success(self, message: str):
        """Print success message"""
        print(f"{Color.GREEN}✅ {message}{Color.END}")
    
    def _print_warning(self, message: str):
        """Print warning message"""
        print(f"{Color.YELLOW}⚠️  {message}{Color.END}")
        self.warnings.append(message)
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Color.RED}❌ {message}{Color.END}")
        self.errors.append(message)
    
    def validate_aws_credentials(self) -> bool:
        """Validate AWS credentials and Bedrock access"""
        self._print_step("1/8", "Validating AWS credentials and Bedrock access")
        
        # Check AWS CLI
        if not shutil.which('aws'):
            self._print_error("AWS CLI not found. Please install AWS CLI first.")
            return False
        
        # Check AWS credentials
        success, stdout, stderr = self._run_command(['aws', 'sts', 'get-caller-identity'], check=False)
        if not success:
            self._print_error("AWS credentials not configured. Run 'aws configure' first.")
            return False
        
        try:
            identity = json.loads(stdout)
            self._print_success(f"AWS credentials valid for account: {identity.get('Account', 'Unknown')}")
        except:
            self._print_error("Invalid AWS credentials response")
            return False
        
        # Check Bedrock access
        success, stdout, stderr = self._run_command([
            'aws', 'bedrock', 'list-foundation-models', 
            '--region', self.config['aws_region']
        ], check=False)
        
        if success:
            try:
                models = json.loads(stdout)
                claude_models = [m for m in models.get('modelSummaries', []) 
                               if 'claude-3-sonnet' in m.get('modelId', '')]
                if claude_models:
                    self._print_success(f"Bedrock access confirmed. Claude 3 Sonnet available.")
                else:
                    self._print_warning("Claude 3 Sonnet not found in available models")
            except:
                self._print_warning("Could not parse Bedrock models response")
        else:
            self._print_error("Cannot access AWS Bedrock. Check permissions.")
            return False
        
        return True
    
    def teardown_existing_services(self) -> bool:
        """Teardown any existing services"""
        self._print_step("2/8", "Tearing down existing services")
        
        # Force kill and remove containers (more aggressive)
        for service_name, service_config in self.services.items():
            container_name = service_config['container']
            
            # Force kill container (more aggressive than stop)
            success, stdout, stderr = self._run_command([
                self.container_engine, 'kill', container_name
            ], check=False)
            
            if success:
                self._print_success(f"Force killed {container_name}")
            else:
                # Try regular stop if kill fails
                success, stdout, stderr = self._run_command([
                    self.container_engine, 'stop', container_name
                ], check=False)
                if success:
                    self._print_success(f"Stopped {container_name}")
            
            # Force remove container (even if running)
            success, stdout, stderr = self._run_command([
                self.container_engine, 'rm', '-f', container_name
            ], check=False)
            
            if success:
                self._print_success(f"Force removed {container_name}")
        
        # Also kill any containers that might be using our ports
        port_containers = self._find_containers_using_ports()
        for container_id, port in port_containers:
            self._print_warning(f"Found container {container_id} using port {port}")
            if self.args.force_kill_ports:
                success, stdout, stderr = self._run_command([
                    self.container_engine, 'kill', container_id
                ], check=False)
                if success:
                    self._print_success(f"Force killed container {container_id} using port {port}")
        
        # Remove networks (force)
        network_name = 'codeanalysis-network'
        success, stdout, stderr = self._run_command([
            self.container_engine, 'network', 'rm', network_name
        ], check=False)
        
        if success:
            self._print_success(f"Removed network {network_name}")
        
        # Clean up volumes (optional - preserves data)
        if self.args.clean_volumes:
            volume_names = [
                'codeanalysis_neo4j_data',
                'codeanalysis_redis_data',
                'codeanalysis_repositories',
                'codeanalysis_analysis_results'
            ]
            
            for volume_name in volume_names:
                success, stdout, stderr = self._run_command([
                    self.container_engine, 'volume', 'rm', '-f', volume_name
                ], check=False)
                
                if success:
                    self._print_success(f"Force removed volume {volume_name}")
        
        # Kill any processes using our ports (nuclear option)
        if self.args.kill_port_processes:
            self._kill_processes_using_ports()
        
        return True
    
    def _find_containers_using_ports(self) -> List[Tuple[str, int]]:
        """Find containers using our target ports"""
        target_ports = [7474, 7687, 6379, 8001, 8000, 3000]
        containers_using_ports = []
        
        for port in target_ports:
            # Get container using this port
            success, stdout, stderr = self._run_command([
                self.container_engine, 'ps', '--filter', f'publish={port}', '--format', '{{.ID}}'
            ], check=False)
            
            if success and stdout.strip():
                container_ids = stdout.strip().split('\n')
                for container_id in container_ids:
                    if container_id:
                        containers_using_ports.append((container_id, port))
        
        return containers_using_ports
    
    def _kill_processes_using_ports(self):
        """Kill processes using our target ports (Windows)"""
        target_ports = [7474, 7687, 6379, 8001, 8000, 3000]
        
        for port in target_ports:
            # Find process using port
            success, stdout, stderr = self._run_command([
                'netstat', '-ano'
            ], check=False)
            
            if success:
                lines = stdout.split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                # Kill the process
                                success, stdout, stderr = self._run_command([
                                    'taskkill', '/F', '/PID', pid
                                ], check=False)
                                if success:
                                    self._print_success(f"Killed process {pid} using port {port}")
                            except:
                                pass
    
    def create_configuration_files(self) -> bool:
        """Create necessary configuration files"""
        self._print_step("3/8", "Creating configuration files")
        
        # Ensure config directory exists
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Create backend .env file
        backend_env = self.project_root / 'backend' / '.env'
        env_content = f"""# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD={self.config['neo4j_password']}
REDIS_URL=redis://localhost:6379

# AWS Bedrock Configuration (ONLY BEDROCK - NO OPENAI)
AWS_BEDROCK_PROXY=true
BEDROCK_MODEL_ID={self.config['bedrock_model']}
AWS_REGION={self.config['aws_region']}

# LiteLLM Proxy Configuration
OPENAI_API_BASE=http://localhost:{self.config['litellm_port']}/v1
OPENAI_API_KEY=bedrock-proxy
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=gpt-4

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
ENVIRONMENT=production

# Repository Configuration
REPOSITORY_BASE_PATH=./repositories
MAX_CONCURRENT_REPOS=3
WORKSPACE_DIR=workspace

# Performance Settings
CODEBERT_BATCH_SIZE=16
TORCH_NUM_THREADS=4
USE_GPU=false
"""
        
        backend_env.write_text(env_content)
        self._print_success("Backend .env file created")
        
        # Create frontend .env.local file
        frontend_env = self.project_root / 'frontend' / '.env.local'
        frontend_env_content = f"""REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
"""
        frontend_env.write_text(frontend_env_content)
        self._print_success("Frontend .env.local file created")
        
        # Update LiteLLM config with current AWS credentials
        litellm_config = config_dir / 'litellm_config.yaml'
        if litellm_config.exists():
            self._print_success("LiteLLM config already exists")
        else:
            self._print_warning("LiteLLM config not found - using default")
        
        return True
    
    def setup_python_environment(self) -> bool:
        """Setup Python virtual environment"""
        self._print_step("4/8", "Setting up Python environment")
        
        venv_path = self.project_root / 'venv'
        
        # Create virtual environment if it doesn't exist
        if not venv_path.exists():
            success, stdout, stderr = self._run_command([sys.executable, '-m', 'venv', 'venv'])
            if not success:
                self._print_error(f"Failed to create virtual environment: {stderr}")
                return False
            self._print_success("Virtual environment created")
        else:
            self._print_success("Virtual environment already exists")
        
        # Determine Python executable path
        if self.is_windows:
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
        
        # Install LiteLLM and dependencies
        packages = [
            'litellm[proxy]>=1.25.0',
            'boto3>=1.34.0',
            'awscli>=1.32.0'
        ]
        
        for package in packages:
            success, stdout, stderr = self._run_command([str(python_exe), '-m', 'pip', 'install', package])
            if success:
                self._print_success(f"Installed {package}")
            else:
                self._print_warning(f"Failed to install {package}: {stderr}")
        
        return True
    
    def start_infrastructure_services(self) -> bool:
        """Start Neo4j and Redis services"""
        self._print_step("5/8", "Starting infrastructure services")
        
        # Create network
        success, stdout, stderr = self._run_command([
            self.container_engine, 'network', 'create', 'codeanalysis-network'
        ], check=False)
        
        if success:
            self._print_success("Created network codeanalysis-network")
        
        # Start Neo4j
        neo4j_command = [
            self.container_engine, 'run', '-d',
            '--name', 'neo4j-codeanalysis',
            '--network', 'codeanalysis-network',
            '-p', '7474:7474', '-p', '7687:7687',
            '-e', 'NEO4J_AUTH=neo4j/codeanalysis123',
            '-e', 'NEO4J_PLUGINS=["apoc"]',
            '-e', 'NEO4J_dbms_memory_heap_initial__size=1G',
            '-e', 'NEO4J_dbms_memory_heap_max__size=2G',
            '-v', 'codeanalysis_neo4j_data:/data',
            'neo4j:5.15'
        ]
        
        success, stdout, stderr = self._run_command(neo4j_command)
        if success:
            self._print_success("Neo4j started successfully")
        else:
            self._print_error(f"Failed to start Neo4j: {stderr}")
            return False
        
        # Start Redis
        redis_command = [
            self.container_engine, 'run', '-d',
            '--name', 'redis-codeanalysis',
            '--network', 'codeanalysis-network',
            '-p', '6379:6379',
            '-v', 'codeanalysis_redis_data:/data',
            'redis:7-alpine',
            'redis-server', '--appendonly', 'yes'
        ]
        
        success, stdout, stderr = self._run_command(redis_command)
        if success:
            self._print_success("Redis started successfully")
        else:
            self._print_error(f"Failed to start Redis: {stderr}")
            return False
        
        # Wait for services to be ready
        self._print_success("Waiting for infrastructure services to be ready...")
        time.sleep(15)
        
        return True
    
    def start_bedrock_proxy(self) -> bool:
        """Start LiteLLM Bedrock proxy"""
        self._print_step("6/8", "Starting AWS Bedrock proxy")
        
        # Get AWS credentials from environment
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        
        if not aws_access_key or not aws_secret_key:
            self._print_error("AWS credentials not found in environment")
            return False
        
        # Build environment variables for container
        env_vars = [
            '-e', f'AWS_ACCESS_KEY_ID={aws_access_key}',
            '-e', f'AWS_SECRET_ACCESS_KEY={aws_secret_key}',
            '-e', f'AWS_DEFAULT_REGION={self.config["aws_region"]}',
            '-e', 'LITELLM_MASTER_KEY=sk-bedrock-proxy-key'
        ]
        
        if aws_session_token:
            env_vars.extend(['-e', f'AWS_SESSION_TOKEN={aws_session_token}'])
        
        # Start LiteLLM proxy
        proxy_command = [
            self.container_engine, 'run', '-d',
            '--name', 'bedrock-proxy',
            '--network', 'codeanalysis-network',
            '-p', f'{self.config["litellm_port"]}:8001',
            '-v', f'{self.project_root / "config" / "litellm_config.yaml"}:/app/litellm_config.yaml:ro'
        ] + env_vars + [
            'ghcr.io/berriai/litellm:main-latest',
            '--config', '/app/litellm_config.yaml',
            '--port', '8001'
        ]
        
        success, stdout, stderr = self._run_command(proxy_command)
        if success:
            self._print_success("Bedrock proxy started successfully")
        else:
            self._print_error(f"Failed to start Bedrock proxy: {stderr}")
            return False
        
        # Wait for proxy to be ready
        self._print_success("Waiting for Bedrock proxy to be ready...")
        time.sleep(10)
        
        # Test proxy connection
        import requests
        try:
            response = requests.get(f'http://localhost:{self.config["litellm_port"]}/health', timeout=5)
            if response.status_code == 200:
                self._print_success("Bedrock proxy health check passed")
            else:
                self._print_warning(f"Bedrock proxy health check returned {response.status_code}")
        except Exception as e:
            self._print_warning(f"Could not verify Bedrock proxy health: {e}")
        
        return True
    
    def start_application_services(self) -> bool:
        """Start backend and frontend services"""
        self._print_step("7/8", "Starting application services")
        
        # Use docker-compose for application services
        compose_file = 'docker-compose.verified.yml'
        if self.container_engine == 'podman':
            # Use podman-compose if available
            if shutil.which('podman-compose'):
                compose_command = ['podman-compose']
            else:
                self._print_warning("podman-compose not found, using docker-compose with podman")
                compose_command = ['docker-compose']
        else:
            compose_command = ['docker-compose']
        
        # Start backend and frontend
        success, stdout, stderr = self._run_command([
            *compose_command, '-f', compose_file,
            'up', '-d', 'backend', 'frontend'
        ])
        
        if success:
            self._print_success("Application services started successfully")
        else:
            self._print_error(f"Failed to start application services: {stderr}")
            return False
        
        # Wait for services to be ready
        self._print_success("Waiting for application services to be ready...")
        time.sleep(30)
        
        return True
    
    def validate_complete_setup(self) -> bool:
        """Validate that all services are running correctly"""
        self._print_step("8/8", "Validating complete setup")
        
        import requests
        
        # Test all service endpoints
        service_tests = [
            ('Neo4j HTTP', 'http://localhost:7474', 200),
            ('Redis', None, None),  # Redis doesn't have HTTP endpoint
            ('Bedrock Proxy', f'http://localhost:{self.config["litellm_port"]}/health', 200),
            ('Backend API', 'http://localhost:8000/api/v1/health', 200),
            ('Frontend', 'http://localhost:3000', 200)
        ]
        
        all_healthy = True
        
        for service_name, url, expected_status in service_tests:
            if url is None:
                continue  # Skip services without HTTP endpoints
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == expected_status:
                    self._print_success(f"{service_name} is healthy")
                else:
                    self._print_error(f"{service_name} returned status {response.status_code}")
                    all_healthy = False
            except Exception as e:
                self._print_error(f"{service_name} is not accessible: {e}")
                all_healthy = False
        
        # Test Redis separately
        try:
            success, stdout, stderr = self._run_command([
                self.container_engine, 'exec', 'redis-codeanalysis', 'redis-cli', 'ping'
            ])
            if success and 'PONG' in stdout:
                self._print_success("Redis is healthy")
            else:
                self._print_error("Redis is not responding")
                all_healthy = False
        except Exception as e:
            self._print_error(f"Could not test Redis: {e}")
            all_healthy = False
        
        # Test Bedrock integration
        try:
            test_payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello, this is a test."}],
                "max_tokens": 10
            }
            
            response = requests.post(
                f'http://localhost:{self.config["litellm_port"]}/v1/chat/completions',
                json=test_payload,
                headers={'Authorization': 'Bearer sk-bedrock-proxy-key'},
                timeout=30
            )
            
            if response.status_code == 200:
                self._print_success("Bedrock integration test passed")
            else:
                self._print_warning(f"Bedrock integration test failed: {response.status_code}")
        except Exception as e:
            self._print_warning(f"Could not test Bedrock integration: {e}")
        
        return all_healthy
    
    def print_summary(self):
        """Print setup summary and access information"""
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 Setup Complete!{Color.END}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  Warnings ({len(self.warnings)}):{Color.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print(f"\n{Color.RED}{Color.BOLD}❌ Errors ({len(self.errors)}):{Color.END}")
            for error in self.errors:
                print(f"  • {error}")
        
        print(f"\n{Color.CYAN}{Color.BOLD}🌐 Access Information:{Color.END}")
        print(f"{Color.WHITE}Frontend Dashboard:{Color.END} {Color.CYAN}http://localhost:3000{Color.END}")
        print(f"{Color.WHITE}Backend API:{Color.END} {Color.CYAN}http://localhost:8000{Color.END}")
        print(f"{Color.WHITE}API Documentation:{Color.END} {Color.CYAN}http://localhost:8000/docs{Color.END}")
        print(f"{Color.WHITE}Neo4j Browser:{Color.END} {Color.CYAN}http://localhost:7474{Color.END}")
        print(f"{Color.WHITE}Bedrock Proxy:{Color.END} {Color.CYAN}http://localhost:{self.config['litellm_port']}{Color.END}")
        
        print(f"\n{Color.CYAN}{Color.BOLD}🔐 Default Credentials:{Color.END}")
        print(f"{Color.WHITE}Neo4j:{Color.END} neo4j / {self.config['neo4j_password']}")
        print(f"{Color.WHITE}LiteLLM Master Key:{Color.END} sk-bedrock-proxy-key")
        
        print(f"\n{Color.CYAN}{Color.BOLD}🛠️  Management Commands:{Color.END}")
        print(f"{Color.WHITE}Stop all services:{Color.END} {Color.CYAN}python setup.py --teardown-only{Color.END}")
        print(f"{Color.WHITE}View logs:{Color.END} {Color.CYAN}{self.container_engine} logs <container-name>{Color.END}")
        print(f"{Color.WHITE}Restart service:{Color.END} {Color.CYAN}{self.container_engine} restart <container-name>{Color.END}")
        
        print(f"\n{Color.GREEN}✅ Ready for Java code analysis with AWS Bedrock!{Color.END}")
    
    def run(self) -> bool:
        """Run the complete setup process"""
        start_time = time.time()
        
        try:
            if self.args.teardown_only:
                return self.teardown_existing_services()
            
            if self.args.validate_only:
                return self.validate_complete_setup()
            
            # Full setup process
            steps = [
                self.validate_aws_credentials if not self.args.quick else lambda: True,
                self.teardown_existing_services,
                self.create_configuration_files,
                self.setup_python_environment,
                self.start_infrastructure_services,
                self.start_bedrock_proxy,
                self.start_application_services,
                self.validate_complete_setup if not self.args.quick else lambda: True
            ]
            
            for step in steps:
                if not step():
                    self._print_error(f"Setup failed at step: {step.__name__}")
                    return False
            
            elapsed_time = time.time() - start_time
            print(f"\n{Color.GREEN}⏱️  Total setup time: {elapsed_time:.1f} seconds{Color.END}")
            
            self.print_summary()
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Color.YELLOW}⚠️  Setup interrupted by user{Color.END}")
            return False
        except Exception as e:
            self._print_error(f"Setup failed with error: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CodeAnalysis MultiAgent MVP Setup Script')
    parser.add_argument('--quick', action='store_true',
                       help='Skip validation steps for faster startup')
    parser.add_argument('--teardown-only', action='store_true',
                       help='Only teardown existing services')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate current setup')
    parser.add_argument('--clean-volumes', action='store_true',
                       help='Remove data volumes during teardown (WARNING: data loss)')
    parser.add_argument('--force-kill-ports', action='store_true',
                       help='Force kill any containers using our target ports')
    parser.add_argument('--kill-port-processes', action='store_true',
                       help='Kill any processes using our target ports (NUCLEAR OPTION)')
    
    args = parser.parse_args()
    
    try:
        setup = CodeAnalysisSetup(args)
        success = setup.run()
        
        if success:
            print(f"\n{Color.GREEN}✅ Setup completed successfully!{Color.END}")
            sys.exit(0)
        else:
            print(f"\n{Color.RED}❌ Setup failed. Check the output above for details.{Color.END}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n{Color.RED}❌ Setup failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()