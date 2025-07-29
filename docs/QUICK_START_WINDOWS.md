# Windows 11 Quick Start Guide

## 🚀 5-Minute Setup for Windows 11

This guide gets you running on Windows 11 with verified, tested steps.

### Prerequisites (2 minutes)

Open PowerShell as Administrator and run:

```powershell
# Install all required tools via winget
winget install Python.Python.3.11
winget install OpenJS.NodeJS  
winget install Git.Git

# Optional but recommended for database
winget install Docker.DockerDesktop

# Restart PowerShell to refresh PATH
```

### Verify Installation

```powershell
# Check versions (should match these or newer)
python --version    # Python 3.11.9
node --version      # v18.x or v24.x  
npm --version       # 9.x or 11.x
git --version       # Any recent version
```

### Deploy Application (3 minutes)

```powershell
# Clone repository
git clone <your-repo-url>
cd graphiti

# Run automated deployment
python deploy.py --platform windows --mode production

# Expected output: "✅ Deployment completed successfully!"
```

### Start Services

The deployment creates batch files for easy startup:

```powershell
# Start backend API server
start_backend.bat

# In new PowerShell window, start frontend
start_frontend.bat

# If using AWS Bedrock, also start proxy
start_bedrock_proxy.bat  # Only if --bedrock was used
```

### Verify Everything Works

1. **Backend**: Open http://localhost:8000/docs - Should show API documentation
2. **Frontend**: Open http://localhost:3000 - Should show dashboard
3. **Database**: Check Docker Desktop - Should show neo4j-codeanalysis container running

### Quick Test

```powershell
# Test API
curl http://localhost:8000/api/v1/health

# Expected response: {"status": "healthy", ...}
```

## 🐛 Windows-Specific Troubleshooting

### PowerShell Execution Policy Issues

```powershell
# If scripts won't run, enable execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows Defender Issues

```powershell
# Add exclusions for development folders
Add-MpPreference -ExclusionPath "C:\path\to\graphiti"
Add-MpPreference -ExclusionProcess "python.exe"
Add-MpPreference -ExclusionProcess "node.exe"
```

### Path Issues

```powershell
# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### Port Conflicts

```powershell
# Check what's using ports 8000 and 3000
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill process if needed (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Firewall Configuration

```powershell
# Allow through Windows Firewall
netsh advfirewall firewall add rule name="CodeAnalysis Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="CodeAnalysis Frontend" dir=in action=allow protocol=TCP localport=3000
```

## 🔧 Windows Optimization Tips

### Performance Optimization

```powershell
# Set high performance power plan
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# Increase virtual memory if low on RAM
# System Properties > Advanced > Performance Settings > Advanced > Virtual Memory
```

### Development Environment

```powershell
# Install Windows Terminal for better experience
winget install Microsoft.WindowsTerminal

# Install Visual Studio Code (optional)
winget install Microsoft.VisualStudioCode
```

### Enterprise GitHub Configuration

If your organization uses enterprise GitHub:

```powershell
# Configure Git for enterprise
git config --global url."https://github.company.com/".insteadOf "https://github.com/"

# Set up authentication token in backend/.env
# GITHUB_TOKEN=ghp_your_enterprise_token_here
# GITHUB_BASE_URL=https://github.company.com/api/v3
```

## 📁 Directory Structure

After successful deployment:

```
graphiti/
├── backend/               # Python FastAPI application
├── frontend/             # React TypeScript application  
├── docs/                 # Documentation
├── venv/                 # Python virtual environment
├── start_backend.bat     # Backend startup script
├── start_frontend.bat    # Frontend startup script
└── deploy.py            # Deployment automation
```

## 🆘 Getting Help

### Debug Information Collection

```powershell
# Collect system information for troubleshooting
python --version > debug_info.txt
node --version >> debug_info.txt  
npm --version >> debug_info.txt
git --version >> debug_info.txt
echo %PATH% >> debug_info.txt

# Include this file when reporting issues
```

### Common Windows Issues

1. **"python is not recognized"** - Restart PowerShell after Python installation
2. **"npm install fails"** - Run as Administrator or check antivirus exclusions  
3. **"Port 8000 in use"** - Another application is using the port, check with netstat
4. **"Docker container fails"** - Ensure Docker Desktop is running and Hyper-V is enabled

### Enterprise Environment Notes

- VPN connections may interfere with Docker networking
- Corporate firewalls may block npm/pip installations
- Group policies may prevent software installation
- Contact IT for exceptions if needed

This Windows 11 guide provides the fastest path to a working CodeAnalysis system with all verified fixes included.