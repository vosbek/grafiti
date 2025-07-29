@echo off
REM CodeAnalysis-MultiAgent-MVP Startup Script (Windows)
REM Universal startup script that detects hardware and configures system appropriately

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set LOG_FILE=%SCRIPT_DIR%startup.log

REM Parse command line arguments
set DISCOVER_FROM=
set REPOS=
set ENVIRONMENT=development
set SKIP_DEPENDENCIES=false

:parse_args
if "%~1"=="" goto args_done
if "%~1"=="-h" goto show_help
if "%~1"=="--help" goto show_help
if "%~1"=="--skip-dependencies" (
    set SKIP_DEPENDENCIES=true
    shift
    goto parse_args
)
for /f "tokens=1,2 delims==" %%a in ("%~1") do (
    if "%%a"=="--discover-from" set DISCOVER_FROM=%%b
    if "%%a"=="--repos" set REPOS=%%b
    if "%%a"=="--environment" set ENVIRONMENT=%%b
)
shift
goto parse_args

:show_help
echo CodeAnalysis-MultiAgent-MVP Startup Script
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --discover-from=URL    Start repository discovery from this URL
echo   --repos=repo1,repo2    Analyze specific repositories
echo   --environment=ENV      Set environment (development/production)
echo   --skip-dependencies    Skip dependency installation
echo   -h, --help            Show this help message
exit /b 0

:args_done

REM Banner
echo.
echo ┌─────────────────────────────────────────────────────────────────┐
echo │                                                                 │
echo │   ██████╗ ██████╗ ██████╗ ███████╗ █████╗ ███╗   ██╗ █████╗   │
echo │  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║██╔══██╗  │
echo │  ██║     ██║   ██║██║  ██║█████╗  ███████║██╔██╗ ██║███████║  │
echo │  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██║██║╚██╗██║██╔══██║  │
echo │  ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║██║  ██║  │
echo │   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝  │
echo │                                                                 │
echo │            Multi-Agent Java Code Analysis System               │
echo │                                                                 │
echo └─────────────────────────────────────────────────────────────────┘
echo.

call :log "Starting CodeAnalysis-MultiAgent-MVP..."
call :log "Script directory: %SCRIPT_DIR%"
call :log "Environment: %ENVIRONMENT%"

REM System detection
call :info "Detecting system capabilities..."

REM Detect Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
call :log "Windows version: %VERSION%"

REM Detect if running on cloud
set CLOUD_PROVIDER=local
curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-id >nul 2>&1
if %errorlevel% equ 0 (
    set CLOUD_PROVIDER=aws
    for /f %%i in ('curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-type') do set INSTANCE_TYPE=%%i
    call :log "Running on AWS EC2: !INSTANCE_TYPE!"
) else (
    call :log "Running on local Windows machine"
)

REM Hardware detection
for /f %%i in ('wmic cpu get NumberOfCores /value ^| find "="') do set %%i
for /f %%i in ('wmic computersystem get TotalPhysicalMemory /value ^| find "="') do set %%i
set /a MEMORY_GB=TotalPhysicalMemory/1024/1024/1024

call :log "Hardware: %NumberOfCores% CPU cores, %MEMORY_GB%GB RAM"

REM GPU detection
set GPU_AVAILABLE=false
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits') do (
        set GPU_INFO=%%i
        set GPU_AVAILABLE=true
        call :log "GPU detected: !GPU_INFO!"
        goto gpu_done
    )
) else (
    call :warn "No NVIDIA GPU detected - will use CPU-only processing"
)
:gpu_done

REM Check for required software
call :check_requirements

if "%SKIP_DEPENDENCIES%"=="false" (
    call :setup_python_env
    call :setup_docker
    call :setup_frontend
)

REM Call Python bootstrap script
call :log "Running Python bootstrap..."
cd /d "%SCRIPT_DIR%"
call venv\Scripts\activate.bat

set BOOTSTRAP_ARGS=--environment=%ENVIRONMENT% --cpu-cores=%NumberOfCores% --memory-gb=%MEMORY_GB% --gpu-available=%GPU_AVAILABLE% --cloud-provider=%CLOUD_PROVIDER%
if not "%DISCOVER_FROM%"=="" set BOOTSTRAP_ARGS=%BOOTSTRAP_ARGS% --discover-from=%DISCOVER_FROM%
if not "%REPOS%"=="" set BOOTSTRAP_ARGS=%BOOTSTRAP_ARGS% --repos=%REPOS%

python scripts\bootstrap.py %BOOTSTRAP_ARGS%

REM Start the application
call :log "Starting application server..."

REM Export configuration as environment variables
set ENVIRONMENT=%ENVIRONMENT%
set CPU_CORES=%NumberOfCores%
set MEMORY_GB=%MEMORY_GB%
set GPU_AVAILABLE=%GPU_AVAILABLE%

REM Start FastAPI server
start /b python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

call :log "Application started successfully!"
call :log "🌐 Web Interface: http://localhost:8000"
call :log "📖 API Documentation: http://localhost:8000/docs"
call :log "❤️  Health Check: http://localhost:8000/api/v1/health"

if not "%DISCOVER_FROM%"=="" (
    call :log "🔍 Repository discovery will start automatically from: %DISCOVER_FROM%"
)

REM Keep command prompt open
pause
exit /b 0

REM Functions
:log
echo [%date% %time%] %~1 >> "%LOG_FILE%"
echo [%date% %time%] %~1
exit /b 0

:error
echo [ERROR] %~1 >> "%LOG_FILE%"
echo [ERROR] %~1
exit /b 1

:warn
echo [WARNING] %~1 >> "%LOG_FILE%"
echo [WARNING] %~1
exit /b 0

:info
echo [INFO] %~1 >> "%LOG_FILE%"
echo [INFO] %~1
exit /b 0

:check_requirements
call :log "Checking requirements..."

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Python is required but not installed. Please install Python 3.10+ first."
    exit /b 1
)

REM Check Docker Desktop
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Docker is required but not installed. Please install Docker Desktop first."
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Docker Desktop is not running. Please start Docker Desktop first."
    exit /b 1
)

exit /b 0

:setup_python_env
call :log "Setting up Python environment..."

cd /d "%SCRIPT_DIR%"

REM Create virtual environment
if not exist "venv" (
    call :log "Creating Python virtual environment..."
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements based on hardware
if "%GPU_AVAILABLE%"=="true" (
    call :log "Installing requirements with GPU support..."
    pip install -r backend\requirements.txt
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    call :log "Installing CPU-only requirements..."
    pip install -r backend\requirements.txt
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

exit /b 0

:setup_docker
call :log "Setting up Docker services..."

cd /d "%SCRIPT_DIR%"

if "%ENVIRONMENT%"=="production" (
    call :log "Starting production services..."
    docker-compose -f docker\production\docker-compose.yml up -d
) else (
    call :log "Starting development services..."
    docker-compose -f docker\development\docker-compose.yml up -d
)

REM Wait for services to be ready
call :log "Waiting for services to be ready..."
timeout /t 10 /nobreak >nul

exit /b 0

:setup_frontend
call :log "Setting up frontend..."

where node >nul 2>&1
if %errorlevel% neq 0 (
    call :warn "Node.js not found. Frontend will not be available."
    exit /b 0
)

cd /d "%SCRIPT_DIR%\frontend"

if not exist "node_modules" (
    call :log "Installing frontend dependencies..."
    npm install
)

REM Build frontend
npm run build

cd /d "%SCRIPT_DIR%"
exit /b 0