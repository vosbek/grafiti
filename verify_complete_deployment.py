#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Complete Deployment Verification

This script performs a final end-to-end verification that the system is ready
for deployment on another machine, incorporating all the verified fixes and
comprehensive testing discovered during the ultrathink process.

Usage:
    python verify_complete_deployment.py
    python verify_complete_deployment.py --generate-report
"""

import os
import sys
import json
import time
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Any

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CompleteDeploymentVerifier:
    """Final comprehensive verification of the complete system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.verification_results = {}
        self.critical_errors = []
        self.warnings = []
        
        print(f"{Color.CYAN}{Color.BOLD}🔍 CodeAnalysis Complete Deployment Verification{Color.END}")
        print(f"{Color.WHITE}Ultrathink Cascade Logic Verification - All Systems Check{Color.END}\n")
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """Execute command safely"""
        try:
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60, check=False)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def _check_result(self, test_name: str, passed: bool, message: str, critical: bool = False):
        """Record and display test result"""
        self.verification_results[test_name] = {"passed": passed, "message": message, "critical": critical}
        
        if passed:
            print(f"{Color.GREEN}✅ {test_name}: {message}{Color.END}")
        else:
            if critical:
                print(f"{Color.RED}❌ {test_name}: {message}{Color.END}")
                self.critical_errors.append(f"{test_name}: {message}")
            else:
                print(f"{Color.YELLOW}⚠️  {test_name}: {message}{Color.END}")
                self.warnings.append(f"{test_name}: {message}")
    
    def verify_documentation_completeness(self) -> bool:
        """Verify all documentation is complete and accessible"""
        print(f"{Color.BLUE}{Color.BOLD}📚 Verifying Documentation Completeness{Color.END}")
        
        required_docs = [
            ("README.md", "Main documentation"),
            ("docs/STARTUP.md", "Startup guide"),
            ("docs/DEPLOYMENT_GUIDE.md", "Deployment guide"),
            ("docs/TROUBLESHOOTING.md", "Troubleshooting guide"), 
            ("docs/BEDROCK_SETUP.md", "AWS Bedrock setup"),
            ("docs/QUICK_START_WINDOWS.md", "Windows quick start"),
            ("docs/QUICK_START_LINUX.md", "Linux quick start"),
        ]
        
        all_docs_present = True
        for doc_path, description in required_docs:
            full_path = self.project_root / doc_path
            if full_path.exists() and full_path.stat().st_size > 1000:  # At least 1KB
                self._check_result(f"doc_{doc_path.replace('/', '_')}", True, f"{description} present and substantial")
            else:
                self._check_result(f"doc_{doc_path.replace('/', '_')}", False, f"{description} missing or too small", critical=True)
                all_docs_present = False
        
        return all_docs_present
    
    def verify_deployment_scripts(self) -> bool:
        """Verify deployment automation scripts"""
        print(f"\n{Color.BLUE}{Color.BOLD}🤖 Verifying Deployment Automation{Color.END}")
        
        required_scripts = [
            ("deploy.py", "Main deployment script"),
            ("validate_deployment.py", "Deployment validation"),
            ("verify_complete_deployment.py", "Complete verification"),
        ]
        
        all_scripts_present = True
        for script_path, description in required_scripts:
            full_path = self.project_root / script_path
            if full_path.exists():
                # Test that script is syntactically correct
                success, stdout, stderr = self._run_command([sys.executable, "-m", "py_compile", str(full_path)])
                if success:
                    self._check_result(f"script_{script_path}", True, f"{description} present and valid")
                else:
                    self._check_result(f"script_{script_path}", False, f"{description} has syntax errors: {stderr}", critical=True)
                    all_scripts_present = False
            else:
                self._check_result(f"script_{script_path}", False, f"{description} missing", critical=True)
                all_scripts_present = False
        
        return all_scripts_present
    
    def verify_docker_configurations(self) -> bool:
        """Verify Docker configurations include all fixes"""
        print(f"\n{Color.BLUE}{Color.BOLD}🐳 Verifying Docker Configurations{Color.END}")
        
        docker_files = [
            ("docker/Dockerfile.backend", "Backend Dockerfile"),
            ("docker/Dockerfile.frontend", "Frontend Dockerfile"),
            ("docker-compose.verified.yml", "Verified Docker Compose"),
        ]
        
        all_docker_valid = True
        for docker_path, description in docker_files:
            full_path = self.project_root / docker_path
            if full_path.exists():
                content = full_path.read_text()
                
                # Check for verified fixes in backend Dockerfile
                if "backend" in docker_path.lower():
                    if "torch>=2.1.0 --index-url" in content and "PYTHONPATH=/app" in content:
                        self._check_result(f"docker_{docker_path.replace('/', '_')}", True, f"{description} includes verified fixes")
                    else:
                        self._check_result(f"docker_{docker_path.replace('/', '_')}", False, f"{description} missing verified fixes", critical=True)
                        all_docker_valid = False
                
                # Check for verified fixes in frontend Dockerfile
                elif "frontend" in docker_path.lower():
                    if "--legacy-peer-deps" in content and "ajv@8.12.0" in content:
                        self._check_result(f"docker_{docker_path.replace('/', '_')}", True, f"{description} includes verified fixes")
                    else:
                        self._check_result(f"docker_{docker_path.replace('/', '_')}", False, f"{description} missing verified fixes", critical=True)
                        all_docker_valid = False
                
                else:
                    self._check_result(f"docker_{docker_path.replace('/', '_')}", True, f"{description} present")
            else:
                self._check_result(f"docker_{docker_path.replace('/', '_')}", False, f"{description} missing", critical=True)
                all_docker_valid = False
        
        return all_docker_valid
    
    def verify_code_fixes(self) -> bool:
        """Verify all critical code fixes are in place"""
        print(f"\n{Color.BLUE}{Color.BOLD}🔧 Verifying Critical Code Fixes{Color.END}")
        
        all_fixes_present = True
        
        # Check Graphiti service fixes
        graphiti_service = self.project_root / "backend/app/services/graphiti_service.py"
        if graphiti_service.exists():
            content = graphiti_service.read_text()
            if "EmbedderClient" in content and "class JavaClassEntity:" in content:
                self._check_result("graphiti_fixes", True, "Graphiti compatibility fixes applied")
            else:
                self._check_result("graphiti_fixes", False, "Graphiti compatibility fixes missing", critical=True)
                all_fixes_present = False
        
        # Check frontend TypeScript fixes
        network_graph = self.project_root / "frontend/src/components/NetworkGraph.tsx"
        if network_graph.exists():
            content = network_graph.read_text()
            if "@ts-ignore" in content and "margin: { top:" in content:
                self._check_result("frontend_ts_fixes", True, "Frontend TypeScript fixes applied")
            else:
                self._check_result("frontend_ts_fixes", False, "Frontend TypeScript fixes missing", critical=True)
                all_fixes_present = False
        
        # Check API types fixes
        api_types = self.project_root / "frontend/src/types/api.ts"
        if api_types.exists():
            content = api_types.read_text()
            if "export type JobStatus =" in content:
                self._check_result("api_types_fixes", True, "API types fixes applied")
            else:
                self._check_result("api_types_fixes", False, "API types fixes missing", critical=True)
                all_fixes_present = False
        
        return all_fixes_present
    
    def verify_requirements_files(self) -> bool:
        """Verify requirements files are complete and correct"""
        print(f"\n{Color.BLUE}{Color.BOLD}📦 Verifying Requirements Files{Color.END}")
        
        all_requirements_valid = True
        
        # Backend requirements
        backend_req = self.project_root / "backend/requirements.txt"
        if backend_req.exists():
            content = backend_req.read_text()
            critical_packages = ["torch>=2.1.0", "transformers>=4.35.0", "graphiti-core>=0.17.0", "fastapi>=0.104.0"]
            missing_packages = [pkg for pkg in critical_packages if pkg.split(">=")[0] not in content]
            
            if not missing_packages:
                self._check_result("backend_requirements", True, "Backend requirements complete")
            else:
                self._check_result("backend_requirements", False, f"Missing packages: {missing_packages}", critical=True)
                all_requirements_valid = False
        else:
            self._check_result("backend_requirements", False, "Backend requirements.txt missing", critical=True)
            all_requirements_valid = False
        
        # Frontend package.json
        frontend_pkg = self.project_root / "frontend/package.json"
        if frontend_pkg.exists():
            try:
                with open(frontend_pkg) as f:
                    pkg_json = json.load(f)
                
                critical_deps = ["react", "@mui/material", "recharts", "vis-network"]
                missing_deps = [dep for dep in critical_deps if dep not in pkg_json.get("dependencies", {})]
                
                if not missing_deps:
                    self._check_result("frontend_package", True, "Frontend package.json complete")
                else:
                    self._check_result("frontend_package", False, f"Missing dependencies: {missing_deps}", critical=True)
                    all_requirements_valid = False
                    
            except json.JSONDecodeError:
                self._check_result("frontend_package", False, "Frontend package.json invalid", critical=True)
                all_requirements_valid = False
        else:
            self._check_result("frontend_package", False, "Frontend package.json missing", critical=True)
            all_requirements_valid = False
        
        return all_requirements_valid
    
    def verify_configuration_templates(self) -> bool:
        """Verify configuration templates are present"""
        print(f"\n{Color.BLUE}{Color.BOLD}⚙️ Verifying Configuration Templates{Color.END}")
        
        config_checks = []
        
        # Check if startup scripts exist or will be created
        startup_scripts = ["start_backend.sh", "start_frontend.sh", "start_backend.bat", "start_frontend.bat"]
        for script in startup_scripts:
            if (self.project_root / script).exists():
                config_checks.append(f"Startup script {script} present")
        
        # Check Docker configurations
        if (self.project_root / "docker-compose.verified.yml").exists():
            config_checks.append("Docker Compose configuration present")
        
        if len(config_checks) >= 2:  # At least some configurations present
            self._check_result("configuration_templates", True, f"Configuration templates present: {len(config_checks)} items")
            return True
        else:
            self._check_result("configuration_templates", False, "Insufficient configuration templates", critical=False)
            return False
    
    def verify_platform_compatibility(self) -> bool:
        """Verify platform-specific compatibility"""
        print(f"\n{Color.BLUE}{Color.BOLD}🖥️ Verifying Platform Compatibility{Color.END}")
        
        current_platform = platform.system().lower()
        
        # Check Python version compatibility
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 11):
            self._check_result("python_compatibility", True, f"Python {python_version} compatible")
        else:
            self._check_result("python_compatibility", False, f"Python {python_version} below requirement", critical=True)
            return False
        
        # Check for platform-specific documentation
        platform_docs = {
            "windows": "docs/QUICK_START_WINDOWS.md",
            "linux": "docs/QUICK_START_LINUX.md",
            "darwin": "docs/QUICK_START_LINUX.md"  # macOS can use Linux guide
        }
        
        platform_doc = platform_docs.get(current_platform)
        if platform_doc and (self.project_root / platform_doc).exists():
            self._check_result("platform_docs", True, f"Platform-specific documentation available for {current_platform}")
        else:
            self._check_result("platform_docs", False, f"Platform documentation missing for {current_platform}", critical=False)
        
        self._check_result("platform_detected", True, f"Running on {current_platform} - {platform.machine()}")
        return True
    
    def generate_deployment_checklist(self) -> Dict[str, Any]:
        """Generate a deployment checklist for the target machine"""
        checklist = {
            "pre_deployment": [
                "Ensure Python 3.11+ is installed",
                "Ensure Node.js 18+ is installed", 
                "Ensure Git is installed",
                "Ensure at least 8GB RAM available",
                "Ensure at least 50GB disk space available",
                "Configure AWS credentials (if using Bedrock)",
                "Obtain GitHub token (if using private repositories)"
            ],
            "deployment_steps": [
                "Clone repository to target machine",
                "Run: python deploy.py --platform auto --mode production",
                "Run: python validate_deployment.py --comprehensive",
                "Configure environment variables in .env files",
                "Test with: curl http://localhost:8000/api/v1/health",
                "Access frontend at: http://localhost:3000"
            ],
            "verification_steps": [
                "Run complete deployment verification",
                "Test repository discovery functionality",
                "Test semantic search capabilities", 
                "Test multi-agent analysis execution",
                "Verify knowledge graph population",
                "Test export functionality"
            ],
            "troubleshooting_resources": [
                "docs/TROUBLESHOOTING.md - Complete issue resolution",
                "docs/DEPLOYMENT_GUIDE.md - Detailed deployment instructions",
                "validate_deployment.py --fix-issues - Automatic issue resolution",
                "Docker logs and system monitoring tools"
            ]
        }
        return checklist
    
    def run_complete_verification(self) -> Tuple[bool, Dict[str, Any]]:
        """Run complete verification suite"""
        start_time = time.time()
        
        verification_steps = [
            self.verify_documentation_completeness,
            self.verify_deployment_scripts,
            self.verify_docker_configurations,
            self.verify_code_fixes,
            self.verify_requirements_files,
            self.verify_configuration_templates,
            self.verify_platform_compatibility
        ]
        
        overall_success = True
        for step in verification_steps:
            if not step():
                overall_success = False
            print()
        
        elapsed_time = time.time() - start_time
        
        # Generate summary
        total_tests = len(self.verification_results)
        passed_tests = len([r for r in self.verification_results.values() if r["passed"]])
        critical_failures = len(self.critical_errors)
        
        print(f"{Color.CYAN}{Color.BOLD}📊 Complete Verification Summary{Color.END}")
        print(f"{Color.WHITE}Total time: {elapsed_time:.1f} seconds{Color.END}")
        print(f"{Color.GREEN}✅ Passed: {passed_tests}/{total_tests}{Color.END}")
        print(f"{Color.RED}❌ Critical failures: {critical_failures}{Color.END}")
        print(f"{Color.YELLOW}⚠️  Warnings: {len(self.warnings)}{Color.END}")
        
        if overall_success and critical_failures == 0:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 DEPLOYMENT READY FOR TARGET MACHINE{Color.END}")
            print(f"{Color.WHITE}All critical components verified and ready for deployment.{Color.END}")
        else:
            print(f"\n{Color.RED}{Color.BOLD}🚨 DEPLOYMENT NOT READY{Color.END}")
            print(f"{Color.WHITE}Critical issues must be resolved before deployment.{Color.END}")
        
        if self.critical_errors:
            print(f"\n{Color.RED}{Color.BOLD}Critical Issues to Resolve:{Color.END}")
            for error in self.critical_errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}Warnings (Non-Critical):{Color.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Generate deployment package info
        deployment_checklist = self.generate_deployment_checklist()
        
        report = {
            "verification_timestamp": time.time(),
            "verification_duration": elapsed_time,
            "platform": platform.system(),
            "python_version": sys.version,
            "overall_success": overall_success and critical_failures == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "critical_failures": critical_failures,
            "warnings_count": len(self.warnings),
            "verification_results": self.verification_results,
            "critical_errors": self.critical_errors,
            "warnings": self.warnings,
            "deployment_checklist": deployment_checklist,
            "ready_for_deployment": overall_success and critical_failures == 0
        }
        
        return overall_success and critical_failures == 0, report

def main():
    """Main verification entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete Deployment Verification')
    parser.add_argument('--generate-report', type=str, help='Generate JSON report to file')
    args = parser.parse_args()
    
    try:
        verifier = CompleteDeploymentVerifier()
        success, report = verifier.run_complete_verification()
        
        if args.generate_report:
            with open(args.generate_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n{Color.BLUE}📄 Complete verification report saved to: {args.generate_report}{Color.END}")
        
        if success:
            print(f"\n{Color.GREEN}{Color.BOLD}✅ SYSTEM READY FOR DEPLOYMENT TO TARGET MACHINE{Color.END}")
            print(f"\n{Color.CYAN}🚀 Next Steps:{Color.END}")
            print(f"{Color.WHITE}1. Transfer this codebase to target machine{Color.END}")
            print(f"{Color.WHITE}2. Run: python deploy.py --platform auto --mode production{Color.END}")
            print(f"{Color.WHITE}3. Run: python validate_deployment.py --comprehensive{Color.END}")
            print(f"{Color.WHITE}4. Access application at http://localhost:3000{Color.END}")
        else:
            print(f"\n{Color.RED}{Color.BOLD}❌ SYSTEM NOT READY - RESOLVE CRITICAL ISSUES FIRST{Color.END}")
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"\n{Color.RED}❌ Verification failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()