#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Deployment Validation Script

Comprehensive validation of deployment to ensure everything is working correctly.
This script tests all components and provides detailed diagnostics.

Usage:
    python validate_deployment.py
    python validate_deployment.py --comprehensive
    python validate_deployment.py --fix-issues
"""

import os
import sys
import json
import time
import subprocess
import platform
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin

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

class ValidationResult:
    """Container for validation test results"""
    def __init__(self, name: str, passed: bool, message: str, details: Optional[Dict] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()

class DeploymentValidator:
    """Comprehensive deployment validation with automated fixes"""
    
    def __init__(self, comprehensive: bool = False, fix_issues: bool = False):
        self.comprehensive = comprehensive
        self.fix_issues = fix_issues
        self.project_root = Path(__file__).parent
        self.results: List[ValidationResult] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Service endpoints
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.neo4j_url = "http://localhost:7474"
        
        print(f"{Color.CYAN}{Color.BOLD}🔍 CodeAnalysis Deployment Validation{Color.END}")
        print(f"{Color.WHITE}Mode: {'Comprehensive' if comprehensive else 'Standard'} | Fix Issues: {fix_issues}{Color.END}\n")
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None, 
                    timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute a command safely with timeout"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def _make_request(self, url: str, timeout: int = 10) -> Tuple[bool, Optional[Dict], str]:
        """Make HTTP request with error handling"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                try:
                    return True, response.json(), ""
                except:
                    return True, {"raw": response.text}, ""
            else:
                return False, None, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection refused - service may not be running"
        except requests.exceptions.Timeout:
            return False, None, f"Request timed out after {timeout} seconds"
        except Exception as e:
            return False, None, str(e)
    
    def _print_test(self, test_name: str):
        """Print current test name"""
        print(f"{Color.BLUE}🧪 Testing: {test_name}{Color.END}")
    
    def _add_result(self, result: ValidationResult):
        """Add validation result and print status"""
        self.results.append(result)
        if result.passed:
            print(f"{Color.GREEN}  ✅ {result.message}{Color.END}")
        else:
            print(f"{Color.RED}  ❌ {result.message}{Color.END}")
            self.errors.append(f"{result.name}: {result.message}")
    
    def _add_warning(self, test_name: str, message: str):
        """Add warning result"""
        print(f"{Color.YELLOW}  ⚠️  {message}{Color.END}")
        self.warnings.append(f"{test_name}: {message}")
    
    def validate_system_requirements(self) -> bool:
        """Validate system meets requirements"""
        self._print_test("System Requirements")
        
        all_passed = True
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 11):
            self._add_result(ValidationResult(
                "python_version", True, f"Python {python_version} meets requirements", 
                {"version": python_version}
            ))
        else:
            self._add_result(ValidationResult(
                "python_version", False, f"Python {python_version} below requirement (3.11+)",
                {"version": python_version, "required": "3.11+"}
            ))
            all_passed = False
        
        # Node.js version
        success, stdout, stderr = self._run_command(['node', '--version'])
        if success:
            node_version = stdout.strip().lstrip('v')
            try:
                major_version = int(node_version.split('.')[0])
                if major_version >= 18:
                    self._add_result(ValidationResult(
                        "node_version", True, f"Node.js {node_version} meets requirements",
                        {"version": node_version}
                    ))
                else:
                    self._add_result(ValidationResult(
                        "node_version", False, f"Node.js {node_version} below requirement (18.x+)",
                        {"version": node_version, "required": "18.x+"}
                    ))
                    all_passed = False
            except:
                self._add_warning("node_version", f"Could not parse Node.js version: {node_version}")
        else:
            self._add_result(ValidationResult(
                "node_version", False, "Node.js not found or not accessible",
                {"error": stderr}
            ))
            all_passed = False
        
        # Git availability
        success, stdout, stderr = self._run_command(['git', '--version'])
        if success:
            self._add_result(ValidationResult(
                "git_available", True, f"Git available: {stdout.strip()}",
                {"version": stdout.strip()}
            ))
        else:
            self._add_result(ValidationResult(
                "git_available", False, "Git not found",
                {"error": stderr}
            ))
            all_passed = False
        
        # Memory check
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb >= 8:
                self._add_result(ValidationResult(
                    "memory_check", True, f"Memory: {memory_gb:.1f} GB meets requirements",
                    {"memory_gb": memory_gb}
                ))
            else:
                self._add_result(ValidationResult(
                    "memory_check", False, f"Memory: {memory_gb:.1f} GB below minimum 8 GB",
                    {"memory_gb": memory_gb, "required": 8}
                ))
                all_passed = False
        except ImportError:
            self._add_warning("memory_check", "Cannot check memory - psutil not available")
        
        return all_passed
    
    def validate_project_structure(self) -> bool:
        """Validate project directory structure"""
        self._print_test("Project Structure")
        
        required_paths = [
            "backend",
            "frontend", 
            "docs",
            "backend/main.py",
            "backend/requirements.txt",
            "frontend/package.json",
            "frontend/src",
            "deploy.py"
        ]
        
        all_passed = True
        for path_str in required_paths:
            path = self.project_root / path_str
            if path.exists():
                self._add_result(ValidationResult(
                    f"path_{path_str.replace('/', '_')}", True, f"Found {path_str}",
                    {"path": str(path)}
                ))
            else:
                self._add_result(ValidationResult(
                    f"path_{path_str.replace('/', '_')}", False, f"Missing {path_str}",
                    {"path": str(path), "expected": True}
                ))
                all_passed = False
        
        return all_passed
    
    def validate_python_environment(self) -> bool:
        """Validate Python virtual environment and dependencies"""
        self._print_test("Python Environment")
        
        venv_path = self.project_root / 'venv'
        python_executable = venv_path / ('Scripts' if platform.system() == 'Windows' else 'bin') / ('python.exe' if platform.system() == 'Windows' else 'python')
        
        all_passed = True
        
        # Check virtual environment
        if venv_path.exists() and python_executable.exists():
            self._add_result(ValidationResult(
                "venv_exists", True, "Virtual environment found",
                {"path": str(venv_path)}
            ))
        else:
            self._add_result(ValidationResult(
                "venv_exists", False, "Virtual environment not found",
                {"path": str(venv_path), "python_path": str(python_executable)}
            ))
            all_passed = False
            
            if self.fix_issues:
                print(f"{Color.YELLOW}  🔧 Creating virtual environment...{Color.END}")
                success, stdout, stderr = self._run_command([sys.executable, '-m', 'venv', 'venv'])
                if success:
                    print(f"{Color.GREEN}  ✅ Virtual environment created{Color.END}")
                else:
                    print(f"{Color.RED}  ❌ Failed to create virtual environment: {stderr}{Color.END}")
        
        # Check critical Python imports
        if python_executable.exists():
            critical_modules = [
                'torch',
                'transformers',
                'sentence_transformers', 
                'graphiti_core',
                'fastapi',
                'uvicorn',
                'pydantic',
                'neo4j'
            ]
            
            for module in critical_modules:
                success, stdout, stderr = self._run_command([str(python_executable), '-c', f'import {module}'])
                if success:
                    self._add_result(ValidationResult(
                        f"import_{module}", True, f"Can import {module}",
                        {"module": module}
                    ))
                else:
                    self._add_result(ValidationResult(
                        f"import_{module}", False, f"Cannot import {module}: {stderr}",
                        {"module": module, "error": stderr}
                    ))
                    all_passed = False
        
        return all_passed
    
    def validate_frontend_dependencies(self) -> bool:
        """Validate frontend dependencies"""
        self._print_test("Frontend Dependencies")
        
        frontend_path = self.project_root / 'frontend'
        node_modules = frontend_path / 'node_modules'
        package_json = frontend_path / 'package.json'
        
        all_passed = True
        
        # Check package.json
        if package_json.exists():
            self._add_result(ValidationResult(
                "package_json", True, "package.json found",
                {"path": str(package_json)}
            ))
        else:
            self._add_result(ValidationResult(
                "package_json", False, "package.json not found",
                {"path": str(package_json)}
            ))
            all_passed = False
        
        # Check node_modules
        if node_modules.exists():
            self._add_result(ValidationResult(
                "node_modules", True, "node_modules found",
                {"path": str(node_modules)}
            ))
        else:
            self._add_result(ValidationResult(
                "node_modules", False, "node_modules not found - run 'npm install --legacy-peer-deps'",
                {"path": str(node_modules)}
            ))
            all_passed = False
            
            if self.fix_issues:
                print(f"{Color.YELLOW}  🔧 Installing frontend dependencies...{Color.END}")
                success, stdout, stderr = self._run_command(['npm', 'install', '--legacy-peer-deps'], cwd=frontend_path, timeout=300)
                if success:
                    print(f"{Color.GREEN}  ✅ Frontend dependencies installed{Color.END}")
                else:
                    print(f"{Color.RED}  ❌ Failed to install dependencies: {stderr}{Color.END}")
        
        # Test frontend build
        if self.comprehensive and frontend_path.exists():
            print(f"{Color.BLUE}    🔨 Testing frontend build...{Color.END}")
            success, stdout, stderr = self._run_command(['npm', 'run', 'build'], cwd=frontend_path, timeout=300)
            if success:
                if 'Compiled with warnings' in stdout:
                    self._add_result(ValidationResult(
                        "frontend_build", True, "Frontend builds successfully (with warnings)",
                        {"warnings": True}
                    ))
                else:
                    self._add_result(ValidationResult(
                        "frontend_build", True, "Frontend builds successfully",
                        {"warnings": False}
                    ))
            else:
                self._add_result(ValidationResult(
                    "frontend_build", False, f"Frontend build failed: {stderr}",
                    {"error": stderr}
                ))
                all_passed = False
        
        return all_passed
    
    def validate_database_connection(self) -> bool:
        """Validate Neo4j database connection"""
        self._print_test("Database Connection")
        
        all_passed = True
        
        # Check if Docker is available
        docker_available, stdout, stderr = self._run_command(['docker', '--version'])
        if docker_available:
            self._add_result(ValidationResult(
                "docker_available", True, f"Docker available: {stdout.strip()}",
                {"version": stdout.strip()}
            ))
            
            # Check Neo4j container
            success, stdout, stderr = self._run_command(['docker', 'ps', '--format', '{{.Names}}'])
            if success and 'neo4j-codeanalysis' in stdout:
                self._add_result(ValidationResult(
                    "neo4j_container", True, "Neo4j container running",
                    {"container": "neo4j-codeanalysis"}
                ))
                
                # Test Neo4j HTTP endpoint
                success, data, error = self._make_request(self.neo4j_url)
                if success:
                    self._add_result(ValidationResult(
                        "neo4j_http", True, "Neo4j HTTP endpoint accessible",
                        {"url": self.neo4j_url}
                    ))
                else:
                    self._add_result(ValidationResult(
                        "neo4j_http", False, f"Neo4j HTTP endpoint not accessible: {error}",
                        {"url": self.neo4j_url, "error": error}
                    ))
                    all_passed = False
            else:
                self._add_result(ValidationResult(
                    "neo4j_container", False, "Neo4j container not running",
                    {"containers": stdout.split('\n') if stdout else []}
                ))
                all_passed = False
                
                if self.fix_issues:
                    print(f"{Color.YELLOW}  🔧 Starting Neo4j container...{Color.END}")
                    neo4j_command = [
                        'docker', 'run', '-d',
                        '--name', 'neo4j-codeanalysis',
                        '-p', '7474:7474', '-p', '7687:7687',
                        '-e', 'NEO4J_AUTH=neo4j/codeanalysis123',
                        'neo4j:5.15'
                    ]
                    success, stdout, stderr = self._run_command(neo4j_command)
                    if success:
                        print(f"{Color.GREEN}  ✅ Neo4j container started{Color.END}")
                        time.sleep(10)  # Wait for Neo4j to be ready
                    else:
                        print(f"{Color.RED}  ❌ Failed to start Neo4j: {stderr}{Color.END}")
        else:
            self._add_result(ValidationResult(
                "docker_available", False, f"Docker not available: {stderr}",
                {"error": stderr}
            ))
            self._add_warning("database", "Neo4j requires Docker or manual installation")
        
        return all_passed
    
    def validate_backend_service(self) -> bool:
        """Validate backend service"""
        self._print_test("Backend Service")
        
        all_passed = True
        
        # Test backend health endpoint
        success, data, error = self._make_request(f"{self.backend_url}/api/v1/health")
        if success:
            self._add_result(ValidationResult(
                "backend_health", True, "Backend health endpoint accessible",
                {"url": f"{self.backend_url}/api/v1/health", "response": data}
            ))
            
            # Check specific health indicators
            if data and isinstance(data, dict):
                status = data.get('status', 'unknown')
                if status == 'healthy':
                    self._add_result(ValidationResult(
                        "backend_status", True, "Backend reports healthy status",
                        {"status": status}
                    ))
                else:
                    self._add_result(ValidationResult(
                        "backend_status", False, f"Backend reports status: {status}",
                        {"status": status}
                    ))
                    all_passed = False
                
                # Check services
                services = data.get('services', {})
                for service_name, service_status in services.items():
                    if service_status in ['healthy', 'available', 'connected']:
                        self._add_result(ValidationResult(
                            f"service_{service_name}", True, f"{service_name}: {service_status}",
                            {"service": service_name, "status": service_status}
                        ))
                    else:
                        self._add_result(ValidationResult(
                            f"service_{service_name}", False, f"{service_name}: {service_status}",
                            {"service": service_name, "status": service_status}
                        ))
                        all_passed = False
        else:
            self._add_result(ValidationResult(
                "backend_health", False, f"Backend not accessible: {error}",
                {"url": f"{self.backend_url}/api/v1/health", "error": error}
            ))
            all_passed = False
        
        # Test API documentation endpoint
        success, data, error = self._make_request(f"{self.backend_url}/docs")
        if success:
            self._add_result(ValidationResult(
                "backend_docs", True, "Backend API documentation accessible",
                {"url": f"{self.backend_url}/docs"}
            ))
        else:
            self._add_warning("backend_docs", f"API documentation not accessible: {error}")
        
        return all_passed
    
    def validate_frontend_service(self) -> bool:
        """Validate frontend service"""
        self._print_test("Frontend Service")
        
        all_passed = True
        
        # Test frontend accessibility
        success, data, error = self._make_request(self.frontend_url)
        if success:
            self._add_result(ValidationResult(
                "frontend_accessible", True, "Frontend accessible",
                {"url": self.frontend_url}
            ))
        else:
            self._add_result(ValidationResult(
                "frontend_accessible", False, f"Frontend not accessible: {error}",
                {"url": self.frontend_url, "error": error}
            ))
            all_passed = False
        
        return all_passed
    
    def validate_integration(self) -> bool:
        """Validate integration between components"""
        self._print_test("Integration Tests")
        
        all_passed = True
        
        if self.comprehensive:
            # Test repository listing
            success, data, error = self._make_request(f"{self.backend_url}/api/v1/repositories")
            if success:
                self._add_result(ValidationResult(
                    "api_repositories", True, "Repository API endpoint working",
                    {"endpoint": "/api/v1/repositories"}
                ))
            else:
                self._add_result(ValidationResult(
                    "api_repositories", False, f"Repository API failed: {error}",
                    {"endpoint": "/api/v1/repositories", "error": error}
                ))
                all_passed = False
            
            # Test agents endpoint
            success, data, error = self._make_request(f"{self.backend_url}/api/v1/agents")
            if success:
                self._add_result(ValidationResult(
                    "api_agents", True, "Agents API endpoint working",
                    {"endpoint": "/api/v1/agents"}
                ))
            else:
                self._add_result(ValidationResult(
                    "api_agents", False, f"Agents API failed: {error}",
                    {"endpoint": "/api/v1/agents", "error": error}
                ))
                all_passed = False
        
        return all_passed
    
    def validate_configuration(self) -> bool:
        """Validate configuration files"""
        self._print_test("Configuration")
        
        all_passed = True
        
        # Check backend .env
        backend_env = self.project_root / 'backend' / '.env'
        if backend_env.exists():
            self._add_result(ValidationResult(
                "backend_env", True, "Backend .env file found",
                {"path": str(backend_env)}
            ))
        else:
            self._add_result(ValidationResult(
                "backend_env", False, "Backend .env file missing",
                {"path": str(backend_env)}
            ))
            self._add_warning("configuration", "Run deployment script to create configuration files")
        
        # Check frontend .env.local
        frontend_env = self.project_root / 'frontend' / '.env.local'
        if frontend_env.exists():
            self._add_result(ValidationResult(
                "frontend_env", True, "Frontend .env.local file found",
                {"path": str(frontend_env)}
            ))
        else:
            self._add_warning("frontend_env", "Frontend .env.local file missing (optional)")
        
        return all_passed
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        start_time = time.time()
        
        validation_steps = [
            self.validate_system_requirements,
            self.validate_project_structure,
            self.validate_python_environment,
            self.validate_frontend_dependencies,
            self.validate_configuration,
            self.validate_database_connection,
            self.validate_backend_service,
            self.validate_frontend_service,
        ]
        
        if self.comprehensive:
            validation_steps.append(self.validate_integration)
        
        overall_success = True
        for step in validation_steps:
            step_success = step()
            if not step_success:
                overall_success = False
            print()  # Add spacing between tests
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        print(f"{Color.CYAN}{Color.BOLD}📊 Validation Summary{Color.END}")
        print(f"{Color.WHITE}Total time: {elapsed_time:.1f} seconds{Color.END}")
        
        passed_tests = len([r for r in self.results if r.passed])
        total_tests = len(self.results)
        
        print(f"{Color.GREEN}✅ Passed: {passed_tests}{Color.END}")
        print(f"{Color.RED}❌ Failed: {total_tests - passed_tests}{Color.END}")
        print(f"{Color.YELLOW}⚠️  Warnings: {len(self.warnings)}{Color.END}")
        
        if overall_success:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 All critical validations passed!{Color.END}")
            print(f"{Color.WHITE}Your CodeAnalysis deployment is ready to use.{Color.END}")
        else:
            print(f"\n{Color.RED}{Color.BOLD}💥 Some validations failed{Color.END}")
            print(f"{Color.WHITE}Please address the issues above before using the system.{Color.END}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  Warnings:{Color.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors and not overall_success:
            print(f"\n{Color.RED}{Color.BOLD}❌ Critical Errors:{Color.END}")
            for error in self.errors:
                print(f"  • {error}")
        
        # Quick start instructions
        if overall_success:
            print(f"\n{Color.CYAN}{Color.BOLD}🚀 Quick Start:{Color.END}")
            print(f"{Color.WHITE}1. Backend: {Color.CYAN}./start_backend.sh{Color.END} {Color.WHITE}or{Color.END} {Color.CYAN}start_backend.bat{Color.END}")
            print(f"{Color.WHITE}2. Frontend: {Color.CYAN}./start_frontend.sh{Color.END} {Color.WHITE}or{Color.END} {Color.CYAN}start_frontend.bat{Color.END}")
            print(f"{Color.WHITE}3. Access: {Color.CYAN}http://localhost:3000{Color.END}")
        
        return overall_success
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate detailed JSON report"""
        return {
            "timestamp": time.time(),
            "platform": platform.system(),
            "python_version": sys.version,
            "comprehensive": self.comprehensive,
            "fix_issues": self.fix_issues,
            "overall_success": len(self.errors) == 0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ],
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": len([r for r in self.results if r.passed]),
                "failed_tests": len([r for r in self.results if not r.passed]),
                "warnings_count": len(self.warnings),
                "errors_count": len(self.errors)
            }
        }

def main():
    """Main validation entry point"""
    parser = argparse.ArgumentParser(description='CodeAnalysis Deployment Validation')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive validation including build tests')
    parser.add_argument('--fix-issues', action='store_true',
                       help='Attempt to automatically fix detected issues')
    parser.add_argument('--report', type=str,
                       help='Generate JSON report to specified file')
    
    args = parser.parse_args()
    
    try:
        validator = DeploymentValidator(args.comprehensive, args.fix_issues)
        success = validator.run_validation()
        
        if args.report:
            report = validator.generate_report()
            with open(args.report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n{Color.BLUE}📄 Report saved to: {args.report}{Color.END}")
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  Validation interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}❌ Validation failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()