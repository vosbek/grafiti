#!/usr/bin/env python3
"""
CodeAnalysis MultiAgent MVP - Custom Port Startup Script

Start frontend and backend on custom ports to avoid conflicts.

Usage:
    python start_custom_ports.py
    python start_custom_ports.py --frontend-port 3001 --backend-port 8080
"""

import os
import sys
import subprocess
import argparse
import time
import threading
from pathlib import Path

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CustomPortStarter:
    def __init__(self, frontend_port=3001, backend_port=8080):
        self.frontend_port = frontend_port
        self.backend_port = backend_port
        self.project_root = Path(__file__).parent
        self.processes = []
        
        print(f"{Color.CYAN}{Color.BOLD}🚀 Starting CodeAnalysis with Custom Ports{Color.END}")
        print(f"{Color.WHITE}Frontend: http://localhost:{frontend_port}{Color.END}")
        print(f"{Color.WHITE}Backend: http://localhost:{backend_port}{Color.END}\n")
    
    def check_port_available(self, port):
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    def start_backend(self):
        """Start backend on custom port"""
        print(f"{Color.BLUE}🔧 Starting Backend on port {self.backend_port}...{Color.END}")
        
        backend_dir = self.project_root / 'backend'
        if not backend_dir.exists():
            print(f"{Color.RED}❌ Backend directory not found: {backend_dir}{Color.END}")
            return False
        
        # Check if virtual environment exists
        venv_dir = self.project_root / 'venv'
        if venv_dir.exists():
            if os.name == 'nt':  # Windows
                python_exe = venv_dir / 'Scripts' / 'python.exe'
            else:  # Linux/Mac
                python_exe = venv_dir / 'bin' / 'python'
        else:
            python_exe = sys.executable
            print(f"{Color.YELLOW}⚠️  Virtual environment not found, using system Python{Color.END}")
        
        # Set environment variables
        env = os.environ.copy()
        env['PORT'] = str(self.backend_port)
        env['HOST'] = '0.0.0.0'
        
        # Start backend
        try:
            process = subprocess.Popen([
                str(python_exe), '-m', 'uvicorn', 'main:app',
                '--host', '0.0.0.0',
                '--port', str(self.backend_port),
                '--reload'
            ], cwd=backend_dir, env=env)
            
            self.processes.append(('backend', process))
            print(f"{Color.GREEN}✅ Backend started on port {self.backend_port}{Color.END}")
            return True
            
        except Exception as e:
            print(f"{Color.RED}❌ Failed to start backend: {e}{Color.END}")
            return False
    
    def start_frontend(self):
        """Start frontend on custom port"""
        print(f"{Color.BLUE}🔧 Starting Frontend on port {self.frontend_port}...{Color.END}")
        
        frontend_dir = self.project_root / 'frontend'
        if not frontend_dir.exists():
            print(f"{Color.RED}❌ Frontend directory not found: {frontend_dir}{Color.END}")
            return False
        
        # Check if node_modules exists
        node_modules = frontend_dir / 'node_modules'
        if not node_modules.exists():
            print(f"{Color.YELLOW}📦 Installing frontend dependencies...{Color.END}")
            try:
                subprocess.run(['npm', 'install', '--legacy-peer-deps'], 
                             cwd=frontend_dir, check=True)
                print(f"{Color.GREEN}✅ Dependencies installed{Color.END}")
            except subprocess.CalledProcessError as e:
                print(f"{Color.RED}❌ Failed to install dependencies: {e}{Color.END}")
                return False
        
        # Set environment variables
        env = os.environ.copy()
        env['PORT'] = str(self.frontend_port)
        env['REACT_APP_API_URL'] = f'http://localhost:{self.backend_port}'
        env['BROWSER'] = 'none'  # Don't auto-open browser
        
        # Start frontend
        try:
            process = subprocess.Popen(['npm', 'start'], 
                                     cwd=frontend_dir, env=env)
            
            self.processes.append(('frontend', process))
            print(f"{Color.GREEN}✅ Frontend started on port {self.frontend_port}{Color.END}")
            return True
            
        except Exception as e:
            print(f"{Color.RED}❌ Failed to start frontend: {e}{Color.END}")
            return False
    
    def wait_for_services(self):
        """Wait for services to be ready"""
        print(f"{Color.BLUE}⏳ Waiting for services to be ready...{Color.END}")
        
        # Wait for backend
        import requests
        backend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f'http://localhost:{self.backend_port}/api/v1/health', timeout=2)
                if response.status_code == 200:
                    backend_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if backend_ready:
            print(f"{Color.GREEN}✅ Backend is ready{Color.END}")
        else:
            print(f"{Color.YELLOW}⚠️  Backend may still be starting{Color.END}")
        
        # Wait for frontend
        frontend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f'http://localhost:{self.frontend_port}', timeout=2)
                if response.status_code == 200:
                    frontend_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if frontend_ready:
            print(f"{Color.GREEN}✅ Frontend is ready{Color.END}")
        else:
            print(f"{Color.YELLOW}⚠️  Frontend may still be starting{Color.END}")
    
    def print_summary(self):
        """Print access information"""
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 Services Started Successfully!{Color.END}")
        print(f"\n{Color.CYAN}{Color.BOLD}🌐 Access URLs:{Color.END}")
        print(f"{Color.WHITE}Frontend Dashboard:{Color.END} {Color.CYAN}http://localhost:{self.frontend_port}{Color.END}")
        print(f"{Color.WHITE}Backend API:{Color.END} {Color.CYAN}http://localhost:{self.backend_port}{Color.END}")
        print(f"{Color.WHITE}API Documentation:{Color.END} {Color.CYAN}http://localhost:{self.backend_port}/docs{Color.END}")
        
        print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  Note:{Color.END}")
        print(f"{Color.WHITE}This runs frontend/backend only. For full system (Neo4j, Redis, etc.),{Color.END}")
        print(f"{Color.WHITE}use the full setup script with custom docker-compose ports.{Color.END}")
        
        print(f"\n{Color.CYAN}{Color.BOLD}🛑 To Stop:{Color.END}")
        print(f"{Color.WHITE}Press Ctrl+C to stop all services{Color.END}")
    
    def cleanup(self):
        """Clean up processes"""
        print(f"\n{Color.YELLOW}🛑 Stopping services...{Color.END}")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"{Color.GREEN}✅ Stopped {name}{Color.END}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"{Color.YELLOW}⚠️  Force killed {name}{Color.END}")
            except Exception as e:
                print(f"{Color.RED}❌ Error stopping {name}: {e}{Color.END}")
    
    def run(self):
        """Run the startup process"""
        try:
            # Check port availability
            if not self.check_port_available(self.frontend_port):
                print(f"{Color.RED}❌ Port {self.frontend_port} is already in use{Color.END}")
                return False
            
            if not self.check_port_available(self.backend_port):
                print(f"{Color.RED}❌ Port {self.backend_port} is already in use{Color.END}")
                return False
            
            # Start services
            if not self.start_backend():
                return False
            
            time.sleep(3)  # Give backend a moment to start
            
            if not self.start_frontend():
                return False
            
            # Wait for services and print summary
            self.wait_for_services()
            self.print_summary()
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            
            return True
            
        except Exception as e:
            print(f"{Color.RED}❌ Startup failed: {e}{Color.END}")
            return False
        finally:
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Start CodeAnalysis with custom ports')
    parser.add_argument('--frontend-port', type=int, default=3001,
                       help='Frontend port (default: 3001)')
    parser.add_argument('--backend-port', type=int, default=8080,
                       help='Backend port (default: 8080)')
    
    args = parser.parse_args()
    
    starter = CustomPortStarter(args.frontend_port, args.backend_port)
    success = starter.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()