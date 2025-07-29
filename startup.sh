#!/bin/bash

# CodeAnalysis-MultiAgent-MVP Startup Script (Linux/macOS/AWS)
# Universal startup script that detects hardware and configures system appropriately

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/startup.log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Parse command line arguments
DISCOVER_FROM=""
REPOS=""
ENVIRONMENT="development"
SKIP_DEPENDENCIES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --discover-from=*)
            DISCOVER_FROM="${1#*=}"
            shift
            ;;
        --repos=*)
            REPOS="${1#*=}"
            shift
            ;;
        --environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --skip-dependencies)
            SKIP_DEPENDENCIES=true
            shift
            ;;
        -h|--help)
            echo "CodeAnalysis-MultiAgent-MVP Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --discover-from=URL    Start repository discovery from this URL"
            echo "  --repos=repo1,repo2    Analyze specific repositories"
            echo "  --environment=ENV      Set environment (development/production)"
            echo "  --skip-dependencies    Skip dependency installation"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Banner
cat << 'EOF'
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ██████╗ ██████╗ ██████╗ ███████╗ █████╗ ███╗   ██╗ █████╗   │
│  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║██╔══██╗  │
│  ██║     ██║   ██║██║  ██║█████╗  ███████║██╔██╗ ██║███████║  │
│  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██║██║╚██╗██║██╔══██║  │
│  ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║██║  ██║  │
│   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝  │
│                                                                 │
│            Multi-Agent Java Code Analysis System               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
EOF

log "Starting CodeAnalysis-MultiAgent-MVP..."
log "Script directory: $SCRIPT_DIR"
log "Environment: $ENVIRONMENT"

# System detection
info "Detecting system capabilities..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    OS="unknown"
fi

log "Detected OS: $OS"

# Detect if running on AWS/Cloud
if curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-id > /dev/null 2>&1; then
    CLOUD_PROVIDER="aws"
    INSTANCE_TYPE=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-type)
    log "Running on AWS EC2: $INSTANCE_TYPE"
elif curl -s --max-time 2 -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/machine-type > /dev/null 2>&1; then
    CLOUD_PROVIDER="gcp"
    log "Running on Google Cloud Platform"
elif curl -s --max-time 2 -H "Metadata: true" http://169.254.169.254/metadata/instance?api-version=2021-02-01 > /dev/null 2>&1; then
    CLOUD_PROVIDER="azure"
    log "Running on Microsoft Azure"
else
    CLOUD_PROVIDER="local"
    log "Running on local machine"
fi

# Hardware detection
CPU_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "4")
MEMORY_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "8")

log "Hardware: ${CPU_CORES} CPU cores, ${MEMORY_GB}GB RAM"

# GPU detection
GPU_AVAILABLE=false
if command -v nvidia-smi > /dev/null 2>&1; then
    if nvidia-smi > /dev/null 2>&1; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
        GPU_AVAILABLE=true
        log "GPU detected: $GPU_INFO"
    else
        warn "NVIDIA driver found but GPU not accessible"
    fi
else
    warn "No NVIDIA GPU detected - will use CPU-only processing"
fi

# Python virtual environment setup
setup_python_env() {
    log "Setting up Python environment..."
    
    cd "$SCRIPT_DIR"
    
    # Check Python version
    if ! command -v python3 > /dev/null 2>&1; then
        error "Python 3 is required but not installed"
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log "Python version: $PYTHON_VERSION"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements based on hardware
    if [ "$GPU_AVAILABLE" = true ]; then
        log "Installing requirements with GPU support..."
        pip install -r backend/requirements.txt
        # Install CUDA-specific packages if needed
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        log "Installing CPU-only requirements..."
        pip install -r backend/requirements.txt
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
}

# Docker setup
setup_docker() {
    log "Setting up Docker services..."
    
    if ! command -v docker > /dev/null 2>&1; then
        error "Docker is required but not installed. Please install Docker first."
    fi
    
    if ! docker info > /dev/null 2>&1; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    # Start services based on environment
    cd "$SCRIPT_DIR"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Starting production services..."
        docker-compose -f docker/production/docker-compose.yml up -d
    else
        log "Starting development services..."
        docker-compose -f docker/development/docker-compose.yml up -d
    fi
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check Neo4j
    if ! curl -s http://localhost:7474 > /dev/null; then
        warn "Neo4j may not be ready yet. Services might take longer to start."
    fi
}

# Node.js frontend setup
setup_frontend() {
    log "Setting up frontend..."
    
    if ! command -v node > /dev/null 2>&1; then
        warn "Node.js not found. Frontend will not be available."
        return
    fi
    
    cd "$SCRIPT_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
        log "Installing frontend dependencies..."
        npm install
    fi
    
    # Build frontend
    npm run build
}

# Main setup function
main_setup() {
    if [ "$SKIP_DEPENDENCIES" = false ]; then
        setup_python_env
        setup_docker
        setup_frontend
    fi
    
    # Call Python bootstrap script for final configuration
    log "Running Python bootstrap..."
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    
    python3 scripts/bootstrap.py \
        --environment="$ENVIRONMENT" \
        --cpu-cores="$CPU_CORES" \
        --memory-gb="$MEMORY_GB" \
        --gpu-available="$GPU_AVAILABLE" \
        --cloud-provider="$CLOUD_PROVIDER" \
        ${DISCOVER_FROM:+--discover-from="$DISCOVER_FROM"} \
        ${REPOS:+--repos="$REPOS"}
}

# Cleanup function
cleanup() {
    log "Cleanup requested..."
    if [ -f "$SCRIPT_DIR/app.pid" ]; then
        kill $(cat "$SCRIPT_DIR/app.pid") 2>/dev/null || true
        rm -f "$SCRIPT_DIR/app.pid"
    fi
}

# Signal handlers
trap cleanup EXIT INT TERM

# Run main setup
main_setup

# Start the application
log "Starting application server..."
cd "$SCRIPT_DIR"
source venv/bin/activate

# Export configuration as environment variables
export ENVIRONMENT="$ENVIRONMENT"
export CPU_CORES="$CPU_CORES"
export MEMORY_GB="$MEMORY_GB"
export GPU_AVAILABLE="$GPU_AVAILABLE"

# Start FastAPI server
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
APP_PID=$!
echo $APP_PID > app.pid

log "Application started successfully!"
log "🌐 Web Interface: http://localhost:8000"
log "📖 API Documentation: http://localhost:8000/docs"
log "❤️  Health Check: http://localhost:8000/api/v1/health"

if [ "$DISCOVER_FROM" != "" ]; then
    log "🔍 Repository discovery will start automatically from: $DISCOVER_FROM"
fi

# Keep script running
wait $APP_PID