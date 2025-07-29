#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Podman-Compatible Deployment Script

This is a modified version of deploy.py specifically for podman compatibility.
All Docker commands have been replaced with podman equivalents.
"""

import os
import sys
import subprocess
import platform
import json
import time
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class DeploymentManager:
    """Manages the complete deployment process with podman compatibility"""
    
    def __init__(self, target_platform: str, mode: str, options: Dict):
        self.platform = self._detect_platform() if target_platform == 'auto' else target_platform
        self.mode = mode
        self.options = options
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        
        # Use podman instead of docker
        self.container_runtime = 'podman'
        self.compose_command = 'podman-compose'
        
        # Verified system requirements
        self.requirements = {
            'python_version': '3.11',
            'node_version': '18.0',
            'min_memory_gb': 8,
            'min_storage_gb': 50
        }
        
        print(f"{Color.CYAN}{Color.BOLD}🚀 CodeAnalysis MultiAgent MVP Deployment (Podman){Color.END}")
        print(f"{Color.WHITE}Platform: {self.platform} | Mode: {mode} | Container Runtime: {self.container_runtime}{Color.END}\n")
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'darwin':
            return 'macos'
        elif system == 'linux':
            return 'linux'
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
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
    
    def check_system_requirements(self) -> bool:
        """Verify system meets minimum requirements"""
        self._print_step("1/10", "Checking system requirements")
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        required_python = self.requirements['python_version']
        
        if python_version >= required_python:
            self._print_success(f"Python {python_version} meets requirement (>= {required_python})")
        else:
            self._print_error(f"Python {python_version} does not meet requirement (>= {required_python})")
            return False
        
        # Check Node.js version
        success, stdout, stderr = self._run_command(['node', '--version'], check=False)
        if success:
            node_version = stdout.strip().lstrip('v')
            if node_version >= self.requirements['node_version']:
                self._print_success(f"Node.js {node_version} meets requirement (>= {self.requirements['node_version']})")
            else:
                self._print_warning(f"Node.js {node_version} may not meet requirement (>= {self.requirements['node_version']})")
        else:
            self._print_error("Node.js not found - please install Node.js 18+")
            return False
        
        # Check podman instead of docker
        success, stdout, stderr = self._run_command([self.container_runtime, '--version'], check=False)
        if success:
            self._print_success(f"Podman available: {stdout.strip()}")
        else:
            self._print_error(f"Podman not found: {stderr}")
            return False
        
        # Check podman-compose
        success, stdout, stderr = self._run_command([self.compose_command, '--version'], check=False)
        if success:
            self._print_success(f"Podman-compose available: {stdout.strip()}")
        else:
            self._print_warning("Podman-compose not found - installing...")
            install_success, install_out, install_err = self._run_command([sys.executable, '-m', 'pip', 'install', 'podman-compose'])
            if not install_success:
                self._print_error(f"Failed to install podman-compose: {install_err}")
                return False
        
        # Check available memory
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb >= self.requirements['min_memory_gb']:
                self._print_success(f"Memory: {memory_gb:.1f} GB meets requirement (>= {self.requirements['min_memory_gb']} GB)")
            else:
                self._print_warning(f"Memory: {memory_gb:.1f} GB below recommended {self.requirements['min_memory_gb']} GB")
        except ImportError:
            self._print_warning("Cannot check memory requirements - psutil not available")
        
        # Check available storage
        try:
            storage_free = shutil.disk_usage(self.project_root).free / (1024**3)
            if storage_free >= self.requirements['min_storage_gb']:
                self._print_success(f"Storage: {storage_free:.1f} GB available meets requirement (>= {self.requirements['min_storage_gb']} GB)")
            else:
                self._print_error(f"Storage: {storage_free:.1f} GB available below requirement {self.requirements['min_storage_gb']} GB")
                return False
        except Exception as e:
            self._print_warning(f"Cannot check storage requirements: {e}")
        
        return True
    
    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment"""
        self._print_step("2/10", "Setting up Python virtual environment")
        
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
        
        # Determine activation script path
        if self.platform == 'windows':
            activate_script = venv_path / 'Scripts' / 'activate.bat'
            python_executable = venv_path / 'Scripts' / 'python.exe'
        else:
            activate_script = venv_path / 'bin' / 'activate'
            python_executable = venv_path / 'bin' / 'python'
        
        if not python_executable.exists():
            self._print_error(f"Python executable not found in virtual environment: {python_executable}")
            return False
        
        # Upgrade pip in virtual environment
        success, stdout, stderr = self._run_command([str(python_executable), '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])
        if not success:
            self._print_warning(f"Failed to upgrade pip: {stderr}")
        else:
            self._print_success("Pip upgraded successfully")
        
        return True
    
    def install_backend_dependencies(self) -> bool:
        """Install backend Python dependencies with verified fixes"""
        self._print_step("3/10", "Installing backend dependencies")
        
        backend_path = self.project_root / 'backend'
        venv_python = self.project_root / 'venv' / ('Scripts' if self.platform == 'windows' else 'bin') / ('python.exe' if self.platform == 'windows' else 'python')
        
        if not backend_path.exists():
            self._print_error(f"Backend directory not found: {backend_path}")
            return False
        
        # Install PyTorch first (with verified CPU index URL)
        self._print_success("Installing PyTorch (CPU version)...")
        torch_command = [str(venv_python), '-m', 'pip', 'install', 'torch>=2.1.0', '--index-url', 'https://download.pytorch.org/whl/cpu']
        success, stdout, stderr = self._run_command(torch_command)
        if not success:
            self._print_error(f"Failed to install PyTorch: {stderr}")
            return False
        
        # Install core ML dependencies
        ml_deps = ['transformers>=4.35.0', 'sentence-transformers>=2.2.2', 'graphiti-core>=0.17.0']
        for dep in ml_deps:
            self._print_success(f"Installing {dep}...")
            success, stdout, stderr = self._run_command([str(venv_python), '-m', 'pip', 'install', dep])
            if not success:
                self._print_warning(f"Failed to install {dep}: {stderr}")
        
        # Install remaining dependencies
        requirements_file = backend_path / 'requirements.txt'
        if requirements_file.exists():
            self._print_success("Installing remaining backend dependencies...")
            success, stdout, stderr = self._run_command([str(venv_python), '-m', 'pip', 'install', '-r', str(requirements_file)])
            if not success:
                self._print_warning(f"Some dependencies failed to install: {stderr}")
        
        # Verify critical imports
        critical_imports = [
            'torch',
            'transformers', 
            'sentence_transformers',
            'graphiti_core',
            'fastapi',
            'uvicorn'
        ]
        
        for module in critical_imports:
            success, stdout, stderr = self._run_command([str(venv_python), '-c', f'import {module}; print("✓ {module} imported successfully")'])
            if success:
                self._print_success(f"{module} import verified")
            else:
                self._print_error(f"Failed to import {module}: {stderr}")
                return False
        
        return True
    
    def install_frontend_dependencies(self) -> bool:
        """Install frontend dependencies with verified fixes"""
        self._print_step("4/10", "Installing frontend dependencies")
        
        frontend_path = self.project_root / 'frontend'
        
        if not frontend_path.exists():
            self._print_error(f"Frontend directory not found: {frontend_path}")
            return False
        
        # Install dependencies with legacy peer deps (verified fix)
        self._print_success("Installing frontend dependencies with legacy peer deps...")
        success, stdout, stderr = self._run_command(['npm', 'install', '--legacy-peer-deps'], cwd=frontend_path)
        if not success:
            self._print_error(f"Failed to install frontend dependencies: {stderr}")
            return False
        
        # Install specific AJV version (verified fix)
        self._print_success("Installing AJV compatibility fix...")
        success, stdout, stderr = self._run_command(['npm', 'install', 'ajv@8.12.0', '--legacy-peer-deps'], cwd=frontend_path)
        if not success:
            self._print_warning(f"Failed to install AJV fix: {stderr}")
        
        return True
    
    def setup_database(self) -> bool:
        """Set up Neo4j database with podman"""
        self._print_step("5/10", "Setting up Neo4j database with podman")
        
        # Check if podman is available (already verified in requirements)
        self._print_success("Podman detected - setting up Neo4j container")
        
        # Check if Neo4j container already exists
        success, stdout, stderr = self._run_command([self.container_runtime, 'ps', '-a', '--format', '{{.Names}}'], check=False)
        if 'neo4j-codeanalysis' in stdout:
            self._print_success("Neo4j container already exists - starting if stopped")
            self._run_command([self.container_runtime, 'start', 'neo4j-codeanalysis'], check=False)
            return True
        
        # Create Neo4j container with podman
        neo4j_command = [
            self.container_runtime, 'run', '-d',
            '--name', 'neo4j-codeanalysis',
            '-p', '7474:7474', '-p', '7687:7687',
            '-e', 'NEO4J_AUTH=neo4j/codeanalysis123',
            '-e', 'NEO4J_PLUGINS=["apoc"]',
            '-v', 'neo4j_data:/data',
            'neo4j:5.15'
        ]
        
        success, stdout, stderr = self._run_command(neo4j_command)
        if success:
            self._print_success("Neo4j container created and started with podman")
            # Wait for Neo4j to be ready
            time.sleep(10)
            return True
        else:
            self._print_error(f"Failed to create Neo4j container with podman: {stderr}")
            return False
    
    def setup_aws_bedrock(self) -> bool:
        """Set up AWS Bedrock if enabled"""
        if not self.options.get('bedrock', False):
            return True
        
        self._print_step("6/10", "Setting up AWS Bedrock integration")
        
        venv_python = self.project_root / 'venv' / ('Scripts' if self.platform == 'windows' else 'bin') / ('python.exe' if self.platform == 'windows' else 'python')
        
        # Install LiteLLM proxy
        success, stdout, stderr = self._run_command([str(venv_python), '-m', 'pip', 'install', 'litellm[proxy]', 'boto3'])
        if not success:
            self._print_error(f"Failed to install LiteLLM: {stderr}")
            return False
        
        # Check AWS credentials
        success, stdout, stderr = self._run_command(['aws', 'sts', 'get-caller-identity'], check=False)
        if success:
            self._print_success("AWS credentials configured")
        else:
            self._print_warning("AWS credentials not configured - please run 'aws configure'")
        
        # Test Bedrock access
        success, stdout, stderr = self._run_command(['aws', 'bedrock', 'list-foundation-models', '--region', 'us-east-1'], check=False)
        if success:
            self._print_success("AWS Bedrock access verified")
        else:
            self._print_warning("Cannot verify Bedrock access - check AWS permissions")
        
        return True
    
    def create_configuration_files(self) -> bool:
        """Create necessary configuration files"""
        self._print_step("7/10", "Creating configuration files")
        
        # Backend .env file
        backend_env = self.project_root / 'backend' / '.env'
        if not backend_env.exists():
            env_content = f"""# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# AI Configuration
{'OPENAI_API_BASE=http://localhost:8001/v1' if self.options.get('bedrock') else '# OPENAI_API_KEY=your-key-here'}
{'OPENAI_API_KEY=bedrock-proxy' if self.options.get('bedrock') else '# OPENAI_API_KEY=your-key-here'}

# Repository Configuration
# GITHUB_TOKEN=your-github-token
REPOSITORY_BASE_PATH=./repositories

# Application Settings
DEBUG={'true' if self.mode == 'development' else 'false'}
LOG_LEVEL={'DEBUG' if self.mode == 'development' else 'INFO'}
WORKERS=4
"""
            backend_env.write_text(env_content)
            self._print_success("Backend .env file created")
        else:
            self._print_success("Backend .env file already exists")
        
        # Frontend .env.local file
        frontend_env = self.project_root / 'frontend' / '.env.local'
        if not frontend_env.exists():
            env_content = f"""REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG={'true' if self.mode == 'development' else 'false'}
"""
            frontend_env.write_text(env_content)
            self._print_success("Frontend .env.local file created")
        else:
            self._print_success("Frontend .env.local file already exists")
        
        return True
    
    def build_frontend(self) -> bool:
        """Build frontend for production"""
        if self.mode == 'development':
            return True
        
        self._print_step("8/10", "Building frontend for production")
        
        frontend_path = self.project_root / 'frontend'
        
        # Build frontend
        success, stdout, stderr = self._run_command(['npm', 'run', 'build'], cwd=frontend_path)
        if success:
            # Check for warnings vs errors
            if 'Compiled with warnings' in stdout:
                self._print_success("Frontend built successfully (with non-critical warnings)")
            else:
                self._print_success("Frontend built successfully")
            return True
        else:
            self._print_error(f"Frontend build failed: {stderr}")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify the deployment is working"""
        self._print_step("9/10", "Verifying deployment")
        
        # Test backend imports
        venv_python = self.project_root / 'venv' / ('Scripts' if self.platform == 'windows' else 'bin') / ('python.exe' if self.platform == 'windows' else 'python')
        backend_path = self.project_root / 'backend'
        
        test_command = [str(venv_python), '-c', 'import sys; sys.path.append("."); from main import app; print("✓ Backend application loads successfully")']
        success, stdout, stderr = self._run_command(test_command, cwd=backend_path)
        
        if success:
            self._print_success("Backend verification passed")
        else:
            self._print_error(f"Backend verification failed: {stderr}")
            return False
        
        # Check frontend build
        if self.mode == 'production':
            frontend_build = self.project_root / 'frontend' / 'build'
            if frontend_build.exists():
                self._print_success("Frontend build artifacts verified")
            else:
                self._print_error("Frontend build artifacts not found")
                return False
        
        return True
    
    def create_startup_scripts(self) -> bool:
        """Create startup scripts for the application"""
        self._print_step("10/10", "Creating startup scripts")
        
        # Backend startup script
        if self.platform == 'windows':
            backend_script = self.project_root / 'start_backend_podman.bat'
            script_content = f"""@echo off
cd /d "{self.project_root / 'backend'}"
"{self.project_root / 'venv' / 'Scripts' / 'python.exe'}" -c "import sys; sys.path.append('.')" 
"{self.project_root / 'venv' / 'Scripts' / 'python.exe'}" -m uvicorn main:app --host 0.0.0.0 --port 8000 {'--reload' if self.mode == 'development' else ''}
"""
        else:
            backend_script = self.project_root / 'start_backend_podman.sh'
            script_content = f"""#!/bin/bash
cd "{self.project_root / 'backend'}"
source "{self.project_root / 'venv' / 'bin' / 'activate'}"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 {'--reload' if self.mode == 'development' else ''}
"""
        
        backend_script.write_text(script_content)
        if self.platform != 'windows':
            os.chmod(backend_script, 0o755)
        self._print_success(f"Backend startup script created: {backend_script}")
        
        # Frontend startup script
        if self.mode == 'development':
            if self.platform == 'windows':
                frontend_script = self.project_root / 'start_frontend_podman.bat'
                script_content = f"""@echo off
cd /d "{self.project_root / 'frontend'}"
npm start
"""
            else:
                frontend_script = self.project_root / 'start_frontend_podman.sh'
                script_content = f"""#!/bin/bash
cd "{self.project_root / 'frontend'}"
npm start
"""
        else:
            if self.platform == 'windows':
                frontend_script = self.project_root / 'start_frontend_podman.bat'
                script_content = f"""@echo off
cd /d "{self.project_root / 'frontend'}"
npx serve -s build -l 3000
"""
            else:
                frontend_script = self.project_root / 'start_frontend_podman.sh'
                script_content = f"""#!/bin/bash
cd "{self.project_root / 'frontend'}"
npx serve -s build -l 3000
"""
        
        frontend_script.write_text(script_content)
        if self.platform != 'windows':
            os.chmod(frontend_script, 0o755)
        self._print_success(f"Frontend startup script created: {frontend_script}")
        
        # AWS Bedrock proxy script (if enabled)
        if self.options.get('bedrock', False):
            if self.platform == 'windows':
                bedrock_script = self.project_root / 'start_bedrock_proxy_podman.bat'
                script_content = f"""@echo off
"{self.project_root / 'venv' / 'Scripts' / 'python.exe'}" -m litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001
"""
            else:
                bedrock_script = self.project_root / 'start_bedrock_proxy_podman.sh'
                script_content = f"""#!/bin/bash
source "{self.project_root / 'venv' / 'bin' / 'activate'}"
python -m litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001
"""
            
            bedrock_script.write_text(script_content)
            if self.platform != 'windows':
                os.chmod(bedrock_script, 0o755)
            self._print_success(f"Bedrock proxy script created: {bedrock_script}")
        
        return True
    
    def deploy(self) -> bool:
        """Execute the complete deployment process"""
        start_time = time.time()
        
        steps = [
            self.check_system_requirements,
            self.setup_python_environment,
            self.install_backend_dependencies,
            self.install_frontend_dependencies,
            self.setup_database,
            self.setup_aws_bedrock,
            self.create_configuration_files,
            self.build_frontend,
            self.verify_deployment,
            self.create_startup_scripts
        ]
        
        for step in steps:
            if not step():
                self._print_error(f"Deployment failed at step: {step.__name__}")
                return False
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 Podman deployment completed successfully!{Color.END}")
        print(f"{Color.WHITE}Total time: {elapsed_time:.1f} seconds{Color.END}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  Warnings ({len(self.warnings)}):{Color.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print(f"\n{Color.CYAN}{Color.BOLD}🚀 Quick Start (Podman):{Color.END}")
        
        if self.options.get('bedrock', False):
            print(f"{Color.WHITE}1. Start Bedrock proxy:{Color.END}")
            if self.platform == 'windows':
                print(f"   {Color.CYAN}start_bedrock_proxy_podman.bat{Color.END}")
            else:
                print(f"   {Color.CYAN}./start_bedrock_proxy_podman.sh{Color.END}")
        
        print(f"{Color.WHITE}{'2' if self.options.get('bedrock') else '1'}. Start backend:{Color.END}")
        if self.platform == 'windows':
            print(f"   {Color.CYAN}start_backend_podman.bat{Color.END}")
        else:
            print(f"   {Color.CYAN}./start_backend_podman.sh{Color.END}")
        
        print(f"{Color.WHITE}{'3' if self.options.get('bedrock') else '2'}. Start frontend:{Color.END}")
        if self.platform == 'windows':
            print(f"   {Color.CYAN}start_frontend_podman.bat{Color.END}")
        else:
            print(f"   {Color.CYAN}./start_frontend_podman.sh{Color.END}")
        
        print(f"\n{Color.WHITE}Access the application at: {Color.CYAN}http://localhost:3000{Color.END}")
        print(f"{Color.WHITE}API documentation at: {Color.CYAN}http://localhost:8000/docs{Color.END}")
        
        return True

def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description='CodeAnalysis MultiAgent MVP Podman Deployment Script')
    parser.add_argument('--platform', choices=['auto', 'windows', 'linux', 'macos'], default='auto',
                       help='Target platform (auto-detect by default)')
    parser.add_argument('--mode', choices=['development', 'production'], default='production',
                       help='Deployment mode')
    parser.add_argument('--gpu-enabled', action='store_true',
                       help='Enable GPU acceleration for PyTorch')
    parser.add_argument('--bedrock', action='store_true',
                       help='Enable AWS Bedrock integration')
    parser.add_argument('--skip-verification', action='store_true',
                       help='Skip system requirements verification')
    
    args = parser.parse_args()
    
    options = {
        'gpu_enabled': args.gpu_enabled,
        'bedrock': args.bedrock,
        'skip_verification': args.skip_verification
    }
    
    try:
        deployment = DeploymentManager(args.platform, args.mode, options)
        success = deployment.deploy()
        
        if success:
            print(f"\n{Color.GREEN}✅ Podman deployment completed successfully!{Color.END}")
            sys.exit(0)
        else:
            print(f"\n{Color.RED}❌ Podman deployment failed. Check the output above for details.{Color.END}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  Deployment interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}❌ Deployment failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()