#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Pre-flight Check Script

Comprehensive validation of system readiness before running setup.py
Checks all prerequisites and configurations to prevent setup failures.

Usage:
    python preflight_check.py
    python preflight_check.py --fix-issues
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class PreflightChecker:
    def __init__(self, fix_issues: bool = False):
        self.fix_issues = fix_issues
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system().lower() == 'windows'
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        
        print(f"{Color.CYAN}{Color.BOLD}🔍 CodeAnalysis Pre-flight Check{Color.END}")
        print(f"{Color.WHITE}Platform: {platform.system()} | Fix Issues: {fix_issues}{Color.END}\n")
    
    def _run_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute a command safely"""
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def _check_success(self, name: str, condition: bool, message: str, fix_suggestion: str = None):
        """Record check result"""
        if condition:
            print(f"{Color.GREEN}✅ {name}: {message}{Color.END}")
        else:
            print(f"{Color.RED}❌ {name}: {message}{Color.END}")
            if fix_suggestion:
                print(f"{Color.YELLOW}   💡 Fix: {fix_suggestion}{Color.END}")
            self.issues.append(f"{name}: {message}")
    
    def _check_warning(self, name: str, message: str, fix_suggestion: str = None):
        """Record warning"""
        print(f"{Color.YELLOW}⚠️  {name}: {message}{Color.END}")
        if fix_suggestion:
            print(f"{Color.YELLOW}   💡 Fix: {fix_suggestion}{Color.END}")
        self.warnings.append(f"{name}: {message}")
    
    def check_prerequisites(self) -> bool:
        """Check all system prerequisites"""
        print(f"{Color.BLUE}🔧 Checking Prerequisites{Color.END}")
        
        all_good = True
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 11)
        self._check_success(
            "Python", python_ok, 
            f"Version {python_version}" + (" (OK)" if python_ok else " (Need 3.11+)"),
            "Install Python 3.11+ from python.org"
        )
        if not python_ok:
            all_good = False
        
        # Node.js
        node_success, node_stdout, node_stderr = self._run_command(['node', '--version'])
        if node_success:
            node_version = node_stdout.strip().lstrip('v')
            try:
                major_version = int(node_version.split('.')[0])
                node_ok = major_version >= 18
                self._check_success(
                    "Node.js", node_ok,
                    f"Version {node_version}" + (" (OK)" if node_ok else " (Need 18+)"),
                    "Install Node.js 18+ from nodejs.org"
                )
                if not node_ok:
                    all_good = False
            except:
                self._check_success("Node.js", False, f"Cannot parse version: {node_version}", 
                                  "Reinstall Node.js from nodejs.org")
                all_good = False
        else:
            self._check_success("Node.js", False, "Not found", "Install Node.js 18+ from nodejs.org")
            all_good = False
        
        # Docker
        docker_success, docker_stdout, docker_stderr = self._run_command(['docker', '--version'])
        if docker_success:
            self._check_success("Docker", True, f"Available: {docker_stdout.strip()}")
        else:
            # Check for Podman as alternative
            podman_success, podman_stdout, podman_stderr = self._run_command(['podman', '--version'])
            if podman_success:
                self._check_success("Container Engine", True, f"Podman available: {podman_stdout.strip()}")
            else:
                self._check_success("Container Engine", False, "Neither Docker nor Podman found",
                                  "Install Docker Desktop from docker.com")
                all_good = False
        
        # AWS CLI
        aws_success, aws_stdout, aws_stderr = self._run_command(['aws', '--version'])
        if aws_success:
            self._check_success("AWS CLI", True, f"Available: {aws_stdout.strip()}")
        else:
            self._check_success("AWS CLI", False, "Not found",
                              "Install AWS CLI from AWS documentation")
            all_good = False
        
        # Git
        git_success, git_stdout, git_stderr = self._run_command(['git', '--version'])
        if git_success:
            self._check_success("Git", True, f"Available: {git_stdout.strip()}")
        else:
            self._check_success("Git", False, "Not found", "Install Git from git-scm.com")
            all_good = False
        
        return all_good
    
    def check_aws_configuration(self) -> bool:
        """Check AWS configuration"""
        print(f"\n{Color.BLUE}☁️  Checking AWS Configuration{Color.END}")
        
        all_good = True
        
        # AWS credentials
        aws_success, aws_stdout, aws_stderr = self._run_command(['aws', 'sts', 'get-caller-identity'])
        if aws_success:
            try:
                identity = json.loads(aws_stdout)
                account = identity.get('Account', 'Unknown')
                self._check_success("AWS Credentials", True, f"Valid for account {account}")
            except:
                self._check_success("AWS Credentials", False, "Invalid response format",
                                  "Run 'aws configure' to set up credentials")
                all_good = False
        else:
            self._check_success("AWS Credentials", False, "Not configured",
                              "Run 'aws configure' to set up credentials")
            all_good = False
        
        # AWS region
        region_success, region_stdout, region_stderr = self._run_command(['aws', 'configure', 'get', 'region'])
        if region_success and region_stdout.strip():
            region = region_stdout.strip()
            if region == 'us-east-1':
                self._check_success("AWS Region", True, f"Configured for {region}")
            else:
                self._check_warning("AWS Region", f"Configured for {region}, app expects us-east-1",
                                  "Run 'aws configure set region us-east-1' or set AWS_REGION environment variable")
        else:
            self._check_warning("AWS Region", "Not configured, will use us-east-1 default",
                              "Run 'aws configure set region us-east-1'")
        
        # Bedrock access
        if aws_success:
            bedrock_success, bedrock_stdout, bedrock_stderr = self._run_command([
                'aws', 'bedrock', 'list-foundation-models', '--region', 'us-east-1'
            ], timeout=30)
            
            if bedrock_success:
                try:
                    models = json.loads(bedrock_stdout)
                    claude_models = [m for m in models.get('modelSummaries', []) 
                                   if 'claude-3-sonnet' in m.get('modelId', '')]
                    if claude_models:
                        self._check_success("Bedrock Access", True, 
                                          f"Available with {len(claude_models)} Claude 3 Sonnet models")
                    else:
                        self._check_success("Bedrock Access", False, "Claude 3 Sonnet not available",
                                          "Check Bedrock model access in AWS console")
                        all_good = False
                except:
                    self._check_success("Bedrock Access", False, "Invalid response format",
                                      "Check AWS credentials and Bedrock permissions")
                    all_good = False
            else:
                error_msg = bedrock_stderr.lower()
                if 'accessdenied' in error_msg:
                    fix_msg = "Add Bedrock permissions: bedrock:ListFoundationModels, bedrock:InvokeModel"
                elif 'region' in error_msg:
                    fix_msg = "Bedrock may not be available in your region. Try us-east-1"
                else:
                    fix_msg = "Check AWS credentials and network connectivity"
                
                self._check_success("Bedrock Access", False, f"Cannot access: {bedrock_stderr}", fix_msg)
                all_good = False
        
        return all_good
    
    def check_project_structure(self) -> bool:
        """Check project files and structure"""
        print(f"\n{Color.BLUE}📁 Checking Project Structure{Color.END}")
        
        all_good = True
        
        required_files = [
            ("setup.py", "Main setup script"),
            ("backend/main.py", "Backend application"),
            ("backend/requirements.txt", "Backend dependencies"),
            ("frontend/package.json", "Frontend configuration"),
            ("config/litellm_config.yaml", "LiteLLM configuration"),
            ("docker-compose.verified.yml", "Docker compose file")
        ]
        
        for file_path, description in required_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            self._check_success(description, exists, f"Found at {file_path}" if exists else f"Missing: {file_path}",
                              f"Ensure {file_path} exists in project root" if not exists else None)
            if not exists:
                all_good = False
        
        return all_good
    
    def check_configuration_files(self) -> bool:
        """Check and validate configuration files"""
        print(f"\n{Color.BLUE}⚙️  Checking Configuration Files{Color.END}")
        
        all_good = True
        
        # Backend .env
        backend_env = self.project_root / 'backend' / '.env'
        if backend_env.exists():
            try:
                with open(backend_env, 'r') as f:
                    env_content = f.read()
                
                # Check for Bedrock configuration
                bedrock_configs = [
                    ('AWS_BEDROCK_PROXY=true', 'Bedrock proxy enabled'),
                    ('BEDROCK_MODEL_ID=', 'Bedrock model configured'),
                    ('OPENAI_API_BASE=http://localhost:8001', 'LiteLLM proxy endpoint'),
                    ('OPENAI_API_KEY=bedrock-proxy', 'Proxy API key')
                ]
                
                for config_line, description in bedrock_configs:
                    has_config = config_line in env_content
                    self._check_success(f"Backend Config - {description}", has_config,
                                      "Configured" if has_config else "Missing",
                                      f"Add '{config_line}' to backend/.env" if not has_config else None)
                    if not has_config:
                        all_good = False
                        
            except Exception as e:
                self._check_success("Backend .env", False, f"Cannot read file: {e}",
                                  "Check file permissions and format")
                all_good = False
        else:
            self._check_success("Backend .env", False, "File not found",
                              "Create backend/.env with proper configuration")
            all_good = False
        
        # Frontend .env.local
        frontend_env = self.project_root / 'frontend' / '.env.local'
        if frontend_env.exists():
            try:
                with open(frontend_env, 'r') as f:
                    env_content = f.read()
                
                # Check API URL
                correct_api_url = 'REACT_APP_API_URL=http://localhost:8000' in env_content
                self._check_success("Frontend API URL", correct_api_url,
                                  "Points to backend (port 8000)" if correct_api_url else "Incorrect API URL",
                                  "Set REACT_APP_API_URL=http://localhost:8000 in frontend/.env.local" if not correct_api_url else None)
                if not correct_api_url:
                    all_good = False
                    
            except Exception as e:
                self._check_success("Frontend .env.local", False, f"Cannot read file: {e}",
                                  "Check file permissions and format")
                all_good = False
        else:
            self._check_warning("Frontend .env.local", "File not found (will use defaults)",
                              "Create frontend/.env.local with REACT_APP_API_URL=http://localhost:8000")
        
        return all_good
    
    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        print(f"\n{Color.BLUE}🌍 Checking Environment Variables{Color.END}")
        
        all_good = True
        
        # AWS environment variables (optional but recommended)
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        for var in aws_vars:
            value = os.getenv(var)
            if value:
                self._check_success(f"Environment - {var}", True, f"Set ({value[:8]}...)")
            else:
                self._check_warning(f"Environment - {var}", "Not set",
                                  f"Set {var} environment variable or run setup_environment script")
        
        return all_good
    
    def check_port_availability(self) -> bool:
        """Check if required ports are available"""
        print(f"\n{Color.BLUE}🔌 Checking Port Availability{Color.END}")
        
        all_good = True
        required_ports = [3000, 8000, 8001, 7474, 7687, 6379]
        
        for port in required_ports:
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        self._check_warning(f"Port {port}", "In use",
                                          f"Stop service using port {port} or use setup.py --force-kill-ports")
                    else:
                        self._check_success(f"Port {port}", True, "Available")
            except Exception as e:
                self._check_warning(f"Port {port}", f"Cannot check: {e}")
        
        return all_good
    
    def apply_fixes(self) -> bool:
        """Apply automatic fixes where possible"""
        if not self.fix_issues:
            return True
        
        print(f"\n{Color.YELLOW}🔧 Applying Automatic Fixes{Color.END}")
        
        fixes_applied = 0
        
        # Fix backend .env if needed
        backend_env = self.project_root / 'backend' / '.env'
        if backend_env.exists():
            try:
                with open(backend_env, 'r') as f:
                    content = f.read()
                
                # Add missing Bedrock configuration
                if 'AWS_BEDROCK_PROXY=true' not in content:
                    content += '\nAWS_BEDROCK_PROXY=true'
                    fixes_applied += 1
                
                if 'BEDROCK_MODEL_ID=' not in content:
                    content += '\nBEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0'
                    fixes_applied += 1
                
                if 'OPENAI_API_BASE=http://localhost:8001' not in content:
                    content += '\nOPENAI_API_BASE=http://localhost:8001/v1'
                    fixes_applied += 1
                
                if 'OPENAI_API_KEY=bedrock-proxy' not in content:
                    content += '\nOPENAI_API_KEY=bedrock-proxy'
                    fixes_applied += 1
                
                with open(backend_env, 'w') as f:
                    f.write(content)
                
                if fixes_applied > 0:
                    print(f"{Color.GREEN}✅ Fixed backend .env configuration{Color.END}")
                    
            except Exception as e:
                print(f"{Color.RED}❌ Could not fix backend .env: {e}{Color.END}")
        
        # Fix frontend .env.local if needed
        frontend_env = self.project_root / 'frontend' / '.env.local'
        try:
            if frontend_env.exists():
                with open(frontend_env, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            if 'REACT_APP_API_URL=http://localhost:8000' not in content:
                content = content.replace('REACT_APP_API_URL=http://localhost:8001', 
                                        'REACT_APP_API_URL=http://localhost:8000')
                if 'REACT_APP_API_URL=http://localhost:8000' not in content:
                    content += '\nREACT_APP_API_URL=http://localhost:8000'
                
                with open(frontend_env, 'w') as f:
                    f.write(content)
                
                print(f"{Color.GREEN}✅ Fixed frontend API URL{Color.END}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"{Color.RED}❌ Could not fix frontend .env.local: {e}{Color.END}")
        
        if fixes_applied > 0:
            print(f"{Color.GREEN}Applied {fixes_applied} automatic fixes{Color.END}")
        else:
            print(f"{Color.YELLOW}No automatic fixes needed{Color.END}")
        
        return True
    
    def run_check(self) -> bool:
        """Run complete pre-flight check"""
        start_time = time.time()
        
        checks = [
            ("Prerequisites", self.check_prerequisites),
            ("AWS Configuration", self.check_aws_configuration),
            ("Project Structure", self.check_project_structure),
            ("Configuration Files", self.check_configuration_files),
            ("Environment Variables", self.check_environment_variables),
            ("Port Availability", self.check_port_availability)
        ]
        
        overall_success = True
        for check_name, check_func in checks:
            try:
                success = check_func()
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"{Color.RED}❌ {check_name} check failed: {e}{Color.END}")
                overall_success = False
        
        # Apply fixes if requested
        if self.fix_issues:
            self.apply_fixes()
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        print(f"\n{Color.CYAN}{Color.BOLD}📊 Pre-flight Check Summary{Color.END}")
        print(f"{Color.WHITE}Total time: {elapsed_time:.1f} seconds{Color.END}")
        print(f"{Color.RED}❌ Issues: {len(self.issues)}{Color.END}")
        print(f"{Color.YELLOW}⚠️  Warnings: {len(self.warnings)}{Color.END}")
        
        if overall_success and len(self.issues) == 0:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 All checks passed! Ready to run setup.py{Color.END}")
            print(f"{Color.WHITE}You can now run: python setup.py{Color.END}")
        else:
            print(f"\n{Color.RED}{Color.BOLD}💥 Issues found that need attention{Color.END}")
            if self.issues:
                print(f"\n{Color.RED}{Color.BOLD}Critical Issues:{Color.END}")
                for issue in self.issues[:5]:  # Show top 5
                    print(f"  • {issue}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}Warnings:{Color.END}")
            for warning in self.warnings[:3]:  # Show top 3
                print(f"  • {warning}")
        
        return overall_success and len(self.issues) == 0

def main():
    parser = argparse.ArgumentParser(description='CodeAnalysis Pre-flight Check')
    parser.add_argument('--fix-issues', action='store_true',
                       help='Attempt to automatically fix detected issues')
    
    args = parser.parse_args()
    
    try:
        checker = PreflightChecker(args.fix_issues)
        success = checker.run_check()
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  Check interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}❌ Check failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    import time
    main()