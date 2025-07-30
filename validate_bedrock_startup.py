#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Bedrock Startup Validation Script

Lightweight script to validate AWS credentials, Bedrock access, and that all 
required services can start with Bedrock configuration.

Usage:
    python validate_bedrock_startup.py
    python validate_bedrock_startup.py --fix-issues
    python validate_bedrock_startup.py --verbose
"""

import os
import sys
import json
import time
import subprocess
import platform
import requests
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class BedrockValidationResult:
    """Container for validation test results"""
    def __init__(self, name: str, passed: bool, message: str, details: Optional[Dict] = None, fix_suggestion: Optional[str] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.fix_suggestion = fix_suggestion
        self.timestamp = time.time()

class BedrockStartupValidator:
    """Lightweight Bedrock integration startup validator"""
    
    def __init__(self, fix_issues: bool = False, verbose: bool = False):
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.results: List[BedrockValidationResult] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Configuration
        self.config = {
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'bedrock_model': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            'litellm_port': int(os.getenv('LITELLM_PORT', '8001')),
            'neo4j_password': 'codeanalysis123'
        }
        
        # Service endpoints
        self.endpoints = {
            'litellm_proxy': f"http://localhost:{self.config['litellm_port']}",
            'backend': "http://localhost:8000",
            'neo4j': "http://localhost:7474"
        }
        
        print(f"{Color.CYAN}{Color.BOLD}🔍 Bedrock Integration Startup Validation{Color.END}")
        print(f"{Color.WHITE}AWS Region: {self.config['aws_region']} | Model: {self.config['bedrock_model']}{Color.END}\n")
    
    def _run_command(self, command: List[str], timeout: int = 30, check: bool = False) -> Tuple[bool, str, str]:
        """Execute a command safely with timeout"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def _make_request(self, url: str, timeout: int = 10, headers: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], str]:
        """Make HTTP request with error handling"""
        try:
            if json_data:
                response = requests.post(url, json=json_data, headers=headers or {}, timeout=timeout)
            else:
                response = requests.get(url, headers=headers or {}, timeout=timeout)
            
            if response.status_code in [200, 201]:
                try:
                    return True, response.json(), ""
                except:
                    return True, {"raw": response.text}, ""
            else:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection refused - service may not be running"
        except requests.exceptions.Timeout:
            return False, None, f"Request timed out after {timeout} seconds"
        except Exception as e:
            return False, None, str(e)
    
    def _print_test(self, test_name: str):
        """Print current test name"""
        print(f"{Color.BLUE}🧪 {test_name}{Color.END}")
    
    def _add_result(self, result: BedrockValidationResult):
        """Add validation result and print status"""
        self.results.append(result)
        if result.passed:
            print(f"{Color.GREEN}  ✅ {result.message}{Color.END}")
            if self.verbose and result.details:
                for key, value in result.details.items():
                    print(f"{Color.WHITE}     {key}: {value}{Color.END}")
        else:
            print(f"{Color.RED}  ❌ {result.message}{Color.END}")
            if result.fix_suggestion:
                print(f"{Color.YELLOW}     💡 Fix: {result.fix_suggestion}{Color.END}")
            self.errors.append(f"{result.name}: {result.message}")
    
    def _add_warning(self, test_name: str, message: str, fix_suggestion: Optional[str] = None):
        """Add warning result"""
        print(f"{Color.YELLOW}  ⚠️  {message}{Color.END}")
        if fix_suggestion:
            print(f"{Color.YELLOW}     💡 Fix: {fix_suggestion}{Color.END}")
        self.warnings.append(f"{test_name}: {message}")
    
    def validate_aws_credentials(self) -> bool:
        """Validate AWS credentials and configuration"""
        self._print_test("AWS Credentials & Configuration")
        
        all_passed = True
        
        # Check AWS CLI availability
        if not shutil.which('aws'):
            self._add_result(BedrockValidationResult(
                "aws_cli", False, "AWS CLI not found",
                fix_suggestion="Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
            ))
            return False
        
        # Check AWS credentials
        success, stdout, stderr = self._run_command(['aws', 'sts', 'get-caller-identity'])
        if success:
            try:
                identity = json.loads(stdout)
                account_id = identity.get('Account', 'Unknown')
                user_arn = identity.get('Arn', 'Unknown')
                self._add_result(BedrockValidationResult(
                    "aws_credentials", True, f"AWS credentials valid",
                    {"account": account_id, "user": user_arn}
                ))
            except json.JSONDecodeError:
                self._add_result(BedrockValidationResult(
                    "aws_credentials", False, "Invalid AWS credentials response",
                    fix_suggestion="Run 'aws configure' to set up credentials"
                ))
                all_passed = False
        else:
            self._add_result(BedrockValidationResult(
                "aws_credentials", False, f"AWS credentials not configured: {stderr}",
                fix_suggestion="Run 'aws configure' to set up credentials"
            ))
            all_passed = False
        
        # Check AWS region configuration
        success, stdout, stderr = self._run_command(['aws', 'configure', 'get', 'region'])
        if success and stdout.strip():
            configured_region = stdout.strip()
            if configured_region == self.config['aws_region']:
                self._add_result(BedrockValidationResult(
                    "aws_region", True, f"AWS region configured correctly: {configured_region}",
                    {"region": configured_region}
                ))
            else:
                self._add_warning(
                    "aws_region", 
                    f"AWS region mismatch: configured={configured_region}, expected={self.config['aws_region']}",
                    f"Set AWS_REGION environment variable or run 'aws configure set region {self.config['aws_region']}'"
                )
        else:
            self._add_warning(
                "aws_region", 
                "AWS region not configured",
                f"Run 'aws configure set region {self.config['aws_region']}'"
            )
        
        return all_passed
    
    def validate_bedrock_access(self) -> bool:
        """Validate AWS Bedrock service access"""
        self._print_test("AWS Bedrock Service Access")
        
        all_passed = True
        
        # Test Bedrock service access
        success, stdout, stderr = self._run_command([
            'aws', 'bedrock', 'list-foundation-models', 
            '--region', self.config['aws_region']
        ], timeout=30)
        
        if success:
            try:
                models_response = json.loads(stdout)
                models = models_response.get('modelSummaries', [])
                
                # Check for Claude 3 Sonnet availability
                claude_models = [m for m in models if 'claude-3-sonnet' in m.get('modelId', '')]
                if claude_models:
                    target_model = next((m for m in claude_models if self.config['bedrock_model'] in m.get('modelId', '')), None)
                    if target_model:
                        self._add_result(BedrockValidationResult(
                            "bedrock_model", True, f"Target model available: {self.config['bedrock_model']}",
                            {"model_id": target_model.get('modelId'), "provider": target_model.get('providerName')}
                        ))
                    else:
                        self._add_result(BedrockValidationResult(
                            "bedrock_model", False, f"Target model not found: {self.config['bedrock_model']}",
                            {"available_claude_models": [m.get('modelId') for m in claude_models]},
                            f"Update BEDROCK_MODEL_ID to one of: {', '.join([m.get('modelId') for m in claude_models[:3]])}"
                        ))
                        all_passed = False
                else:
                    self._add_result(BedrockValidationResult(
                        "bedrock_model", False, "No Claude 3 Sonnet models available",
                        {"total_models": len(models)},
                        "Check Bedrock model access in AWS console or try a different region"
                    ))
                    all_passed = False
                
                self._add_result(BedrockValidationResult(
                    "bedrock_access", True, f"Bedrock service accessible ({len(models)} models available)",
                    {"total_models": len(models), "region": self.config['aws_region']}
                ))
                
            except json.JSONDecodeError:
                self._add_result(BedrockValidationResult(
                    "bedrock_access", False, "Invalid Bedrock API response",
                    fix_suggestion="Check AWS credentials and Bedrock service availability"
                ))
                all_passed = False
        else:
            error_msg = stderr.lower()
            if 'accessdenied' in error_msg or 'unauthorized' in error_msg:
                fix_msg = "Add Bedrock permissions to your AWS user/role. Required: bedrock:ListFoundationModels, bedrock:InvokeModel"
            elif 'region' in error_msg:
                fix_msg = f"Bedrock may not be available in {self.config['aws_region']}. Try us-east-1 or us-west-2"
            else:
                fix_msg = "Check AWS credentials and network connectivity"
            
            self._add_result(BedrockValidationResult(
                "bedrock_access", False, f"Cannot access Bedrock service: {stderr}",
                {"region": self.config['aws_region']},
                fix_msg
            ))
            all_passed = False
        
        return all_passed
    
    def validate_litellm_configuration(self) -> bool:
        """Validate LiteLLM configuration files"""
        self._print_test("LiteLLM Configuration")
        
        all_passed = True
        
        # Check LiteLLM config file
        config_file = self.project_root / 'config' / 'litellm_config.yaml'
        if config_file.exists():
            self._add_result(BedrockValidationResult(
                "litellm_config", True, "LiteLLM config file found",
                {"path": str(config_file)}
            ))
            
            # Validate config content
            try:
                import yaml
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                model_list = config.get('model_list', [])
                if model_list:
                    bedrock_models = [m for m in model_list if 'bedrock/' in str(m.get('litellm_params', {}).get('model', ''))]
                    if bedrock_models:
                        self._add_result(BedrockValidationResult(
                            "litellm_bedrock_config", True, f"Bedrock models configured ({len(bedrock_models)} models)",
                            {"bedrock_models": len(bedrock_models)}
                        ))
                    else:
                        self._add_result(BedrockValidationResult(
                            "litellm_bedrock_config", False, "No Bedrock models found in LiteLLM config",
                            fix_suggestion="Ensure config/litellm_config.yaml contains Bedrock model mappings"
                        ))
                        all_passed = False
                else:
                    self._add_result(BedrockValidationResult(
                        "litellm_bedrock_config", False, "No models configured in LiteLLM config",
                        fix_suggestion="Add model_list section to config/litellm_config.yaml"
                    ))
                    all_passed = False
                    
            except ImportError:
                self._add_warning("litellm_config", "Cannot validate config content - PyYAML not available")
            except Exception as e:
                self._add_result(BedrockValidationResult(
                    "litellm_config", False, f"Invalid LiteLLM config: {e}",
                    fix_suggestion="Check YAML syntax in config/litellm_config.yaml"
                ))
                all_passed = False
        else:
            self._add_result(BedrockValidationResult(
                "litellm_config", False, "LiteLLM config file not found",
                {"expected_path": str(config_file)},
                "Run setup script or create config/litellm_config.yaml manually"
            ))
            all_passed = False
        
        # Check environment variables
        required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        for var in required_env_vars:
            if os.getenv(var):
                self._add_result(BedrockValidationResult(
                    f"env_{var.lower()}", True, f"{var} is set",
                    {"masked_value": f"{os.getenv(var)[:8]}..."}
                ))
            else:
                self._add_result(BedrockValidationResult(
                    f"env_{var.lower()}", False, f"{var} not set",
                    fix_suggestion=f"Set {var} environment variable or run 'aws configure'"
                ))
                all_passed = False
        
        return all_passed
    
    def validate_container_engine(self) -> bool:
        """Validate Docker/Podman availability"""
        self._print_test("Container Engine")
        
        # Check for Docker
        if shutil.which('docker'):
            success, stdout, stderr = self._run_command(['docker', '--version'])
            if success:
                self._add_result(BedrockValidationResult(
                    "docker", True, f"Docker available: {stdout.strip()}",
                    {"version": stdout.strip()}
                ))
                return True
        
        # Check for Podman
        if shutil.which('podman'):
            success, stdout, stderr = self._run_command(['podman', '--version'])
            if success:
                self._add_result(BedrockValidationResult(
                    "podman", True, f"Podman available: {stdout.strip()}",
                    {"version": stdout.strip()}
                ))
                return True
        
        self._add_result(BedrockValidationResult(
            "container_engine", False, "Neither Docker nor Podman found",
            fix_suggestion="Install Docker Desktop or Podman for container support"
        ))
        return False
    
    def test_litellm_proxy_startup(self) -> bool:
        """Test LiteLLM proxy can start and respond"""
        self._print_test("LiteLLM Proxy Startup Test")
        
        all_passed = True
        
        # Check if proxy is already running
        success, data, error = self._make_request(f"{self.endpoints['litellm_proxy']}/health")
        if success:
            self._add_result(BedrockValidationResult(
                "litellm_running", True, "LiteLLM proxy is already running",
                {"endpoint": f"{self.endpoints['litellm_proxy']}/health"}
            ))
            return self.test_bedrock_integration()
        
        # Try to start proxy using Docker
        if not shutil.which('docker'):
            self._add_result(BedrockValidationResult(
                "litellm_startup", False, "Cannot test proxy startup - Docker not available",
                fix_suggestion="Install Docker or start LiteLLM proxy manually"
            ))
            return False
        
        print(f"{Color.BLUE}  🚀 Starting LiteLLM proxy for testing...{Color.END}")
        
        # Build Docker command
        config_file = self.project_root / 'config' / 'litellm_config.yaml'
        if not config_file.exists():
            self._add_result(BedrockValidationResult(
                "litellm_startup", False, "Cannot start proxy - config file missing",
                fix_suggestion="Create config/litellm_config.yaml or run setup script"
            ))
            return False
        
        docker_cmd = [
            'docker', 'run', '--rm', '-d',
            '--name', 'bedrock-proxy-test',
            '-p', f'{self.config["litellm_port"]}:8001',
            '-v', f'{config_file}:/app/litellm_config.yaml:ro',
            '-e', f'AWS_ACCESS_KEY_ID={os.getenv("AWS_ACCESS_KEY_ID", "")}',
            '-e', f'AWS_SECRET_ACCESS_KEY={os.getenv("AWS_SECRET_ACCESS_KEY", "")}',
            '-e', f'AWS_DEFAULT_REGION={self.config["aws_region"]}',
            '-e', 'LITELLM_MASTER_KEY=sk-bedrock-proxy-key',
            'ghcr.io/berriai/litellm:main-latest',
            '--config', '/app/litellm_config.yaml',
            '--port', '8001'
        ]
        
        # Add session token if available
        if os.getenv('AWS_SESSION_TOKEN'):
            docker_cmd.insert(-4, '-e')
            docker_cmd.insert(-4, f'AWS_SESSION_TOKEN={os.getenv("AWS_SESSION_TOKEN")}')
        
        success, stdout, stderr = self._run_command(docker_cmd)
        if not success:
            self._add_result(BedrockValidationResult(
                "litellm_startup", False, f"Failed to start LiteLLM proxy: {stderr}",
                fix_suggestion="Check Docker installation and AWS credentials"
            ))
            return False
        
        # Wait for proxy to start
        print(f"{Color.BLUE}  ⏳ Waiting for proxy to be ready...{Color.END}")
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            success, data, error = self._make_request(f"{self.endpoints['litellm_proxy']}/health", timeout=5)
            if success:
                self._add_result(BedrockValidationResult(
                    "litellm_startup", True, f"LiteLLM proxy started successfully (attempt {attempt + 1})",
                    {"startup_time": f"{(attempt + 1) * 2} seconds"}
                ))
                
                # Test Bedrock integration
                integration_success = self.test_bedrock_integration()
                
                # Clean up test container
                self._run_command(['docker', 'stop', 'bedrock-proxy-test'])
                
                return integration_success
        
        # Cleanup on failure
        self._run_command(['docker', 'stop', 'bedrock-proxy-test'])
        self._add_result(BedrockValidationResult(
            "litellm_startup", False, f"LiteLLM proxy failed to start within {max_attempts * 2} seconds",
            fix_suggestion="Check proxy logs: docker logs bedrock-proxy-test"
        ))
        return False
    
    def test_bedrock_integration(self) -> bool:
        """Test actual Bedrock integration through LiteLLM proxy"""
        self._print_test("Bedrock Integration Test")
        
        # Test proxy health endpoint
        success, data, error = self._make_request(f"{self.endpoints['litellm_proxy']}/health")
        if not success:
            self._add_result(BedrockValidationResult(
                "proxy_health", False, f"Proxy health check failed: {error}",
                fix_suggestion="Ensure LiteLLM proxy is running on the correct port"
            ))
            return False
        
        self._add_result(BedrockValidationResult(
            "proxy_health", True, "LiteLLM proxy health check passed",
            {"response": data}
        ))
        
        # Test Bedrock model inference
        test_payload = {
            "model": "gpt-4",  # This maps to Bedrock model via LiteLLM config
            "messages": [{"role": "user", "content": "Hello! Please respond with exactly: 'Bedrock integration working'"}],
            "max_tokens": 20,
            "temperature": 0
        }
        
        headers = {
            'Authorization': 'Bearer sk-bedrock-proxy-key',
            'Content-Type': 'application/json'
        }
        
        print(f"{Color.BLUE}  🧠 Testing Bedrock model inference...{Color.END}")
        success, data, error = self._make_request(
            f"{self.endpoints['litellm_proxy']}/v1/chat/completions",
            timeout=30,
            headers=headers,
            json_data=test_payload
        )
        
        if success and data:
            try:
                choices = data.get('choices', [])
                if choices and len(choices) > 0:
                    response_content = choices[0].get('message', {}).get('content', '')
                    model_used = data.get('model', 'unknown')
                    
                    self._add_result(BedrockValidationResult(
                        "bedrock_inference", True, "Bedrock model inference successful",
                        {
                            "model": model_used,
                            "response_preview": response_content[:50] + "..." if len(response_content) > 50 else response_content,
                            "tokens_used": data.get('usage', {}).get('total_tokens', 'unknown')
                        }
                    ))
                    return True
                else:
                    self._add_result(BedrockValidationResult(
                        "bedrock_inference", False, "Invalid response format from Bedrock",
                        {"response": data},
                        "Check LiteLLM configuration and Bedrock model permissions"
                    ))
            except Exception as e:
                self._add_result(BedrockValidationResult(
                    "bedrock_inference", False, f"Error parsing Bedrock response: {e}",
                    {"response": data},
                    "Check response format and LiteLLM configuration"
                ))
        else:
            error_lower = error.lower()
            if 'unauthorized' in error_lower or '401' in error_lower:
                fix_msg = "Check LiteLLM master key configuration"
            elif 'forbidden' in error_lower or '403' in error_lower:
                fix_msg = "Check AWS Bedrock permissions for your credentials"
            elif 'timeout' in error_lower:
                fix_msg = "Bedrock request timed out - check network and model availability"
            else:
                fix_msg = "Check LiteLLM proxy logs and AWS credentials"
            
            self._add_result(BedrockValidationResult(
                "bedrock_inference", False, f"Bedrock inference failed: {error}",
                fix_suggestion=fix_msg
            ))
        
        return False
    
    def validate_backend_configuration(self) -> bool:
        """Validate backend environment configuration for Bedrock"""
        self._print_test("Backend Configuration")
        
        all_passed = True
        
        # Check backend .env file
        backend_env = self.project_root / 'backend' / '.env'
        if backend_env.exists():
            self._add_result(BedrockValidationResult(
                "backend_env", True, "Backend .env file found",
                {"path": str(backend_env)}
            ))
            
            # Check key Bedrock configuration
            try:
                with open(backend_env, 'r') as f:
                    env_content = f.read()
                
                required_configs = {
                    'AWS_BEDROCK_PROXY=true': 'Bedrock proxy enabled',
                    'BEDROCK_MODEL_ID=': 'Bedrock model ID configured',
                    'OPENAI_API_BASE=http://localhost:8001': 'API base points to LiteLLM proxy',
                    'OPENAI_API_KEY=bedrock-proxy': 'API key set for proxy'
                }
                
                for config_check, description in required_configs.items():
                    if config_check in env_content:
                        self._add_result(BedrockValidationResult(
                            f"config_{config_check.split('=')[0].lower()}", True, description
                        ))
                    else:
                        self._add_result(BedrockValidationResult(
                            f"config_{config_check.split('=')[0].lower()}", False, f"Missing: {description}",
                            fix_suggestion=f"Add '{config_check}' to backend/.env"
                        ))
                        all_passed = False
                        
            except Exception as e:
                self._add_result(BedrockValidationResult(
                    "backend_env_content", False, f"Cannot read backend .env: {e}",
                    fix_suggestion="Check file permissions and content"
                ))
                all_passed = False
        else:
            self._add_result(BedrockValidationResult(
                "backend_env", False, "Backend .env file not found",
                {"expected_path": str(backend_env)},
                "Run setup script or create backend/.env with Bedrock configuration"
            ))
            all_passed = False
        
        return all_passed
    
    def run_validation(self) -> bool:
        """Run complete Bedrock startup validation"""
        start_time = time.time()
        
        print(f"{Color.CYAN}Starting Bedrock integration validation...{Color.END}\n")
        
        validation_steps = [
            ("AWS Credentials", self.validate_aws_credentials),
            ("Bedrock Access", self.validate_bedrock_access),
            ("LiteLLM Config", self.validate_litellm_configuration),
            ("Container Engine", self.validate_container_engine),
            ("Backend Config", self.validate_backend_configuration),
            ("Proxy Startup", self.test_litellm_proxy_startup)
        ]
        
        overall_success = True
        for step_name, step_func in validation_steps:
            try:
                step_success = step_func()
                if not step_success:
                    overall_success = False
                print()  # Add spacing between tests
            except Exception as e:
                self._add_result(BedrockValidationResult(
                    step_name.lower().replace(' ', '_'), False, f"Validation step failed: {e}",
                    fix_suggestion="Check system configuration and try again"
                ))
                overall_success = False
                print()
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        self.print_summary(elapsed_time, overall_success)
        
        return overall_success
    
    def print_summary(self, elapsed_time: float, overall_success: bool):
        """Print validation summary"""
        print(f"{Color.CYAN}{Color.BOLD}📊 Bedrock Validation Summary{Color.END}")
        print(f"{Color.WHITE}Total time: {elapsed_time:.1f} seconds{Color.END}")
        
        passed_tests = len([r for r in self.results if r.passed])
        total_tests = len(self.results)
        
        print(f"{Color.GREEN}✅ Passed: {passed_tests}{Color.END}")
        print(f"{Color.RED}❌ Failed: {total_tests - passed_tests}{Color.END}")
        print(f"{Color.YELLOW}⚠️  Warnings: {len(self.warnings)}{Color.END}")
        
        if overall_success:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 Bedrock integration is ready!{Color.END}")
            print(f"{Color.WHITE}You can now start the CodeAnalysis system with Bedrock support.{Color.END}")
            
            print(f"\n{Color.CYAN}{Color.BOLD}🚀 Next Steps:{Color.END}")
            print(f"{Color.WHITE}1. Start services: {Color.CYAN}python setup.py{Color.END}")
            print(f"{Color.WHITE}2. Or use Docker: {Color.CYAN}docker-compose -f docker-compose.verified.yml --profile bedrock up -d{Color.END}")
            print(f"{Color.WHITE}3. Access API: {Color.CYAN}http://localhost:8000{Color.END}")
            
        else:
            print(f"\n{Color.RED}{Color.BOLD}💥 Bedrock integration has issues{Color.END}")
            print(f"{Color.WHITE}Please address the issues above before starting the system.{Color.END}")
            
            # Show critical fixes
            critical_fixes = [r for r in self.results if not r.passed and r.fix_suggestion]
            if critical_fixes:
                print(f"\n{Color.YELLOW}{Color.BOLD}🔧 Critical Fixes Needed:{Color.END}")
                for result in critical_fixes[:5]:  # Show top 5 fixes
                    print(f"  • {result.name}: {result.fix_suggestion}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  Warnings:{Color.END}")
            for warning in self.warnings[:3]:  # Show top 3 warnings
                print(f"  • {warning}")
        
        # Configuration summary
        print(f"\n{Color.CYAN}{Color.BOLD}⚙️  Configuration:{Color.END}")
        print(f"{Color.WHITE}AWS Region: {self.config['aws_region']}{Color.END}")
        print(f"{Color.WHITE}Bedrock Model: {self.config['bedrock_model']}{Color.END}")
        print(f"{Color.WHITE}LiteLLM Port: {self.config['litellm_port']}{Color.END}")

def main():
    """Main validation entry point"""
    parser = argparse.ArgumentParser(description='Bedrock Integration Startup Validation')
    parser.add_argument('--fix-issues', action='store_true',
                       help='Attempt to automatically fix detected issues')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed information for each test')
    
    args = parser.parse_args()
    
    try:
        validator = BedrockStartupValidator(args.fix_issues, args.verbose)
        success = validator.run_validation()
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  Validation interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}❌ Validation failed with error: {e}{Color.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()