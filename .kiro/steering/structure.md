# Project Structure & Organization

## Root Directory Layout

```
codeanalysis-multiagent-mvp/
├── backend/                    # Python FastAPI application
├── frontend/                   # React TypeScript interface
├── docker/                     # Container configurations
├── docs/                       # Comprehensive documentation
├── kubernetes/                 # K8s manifests and configs
├── scripts/                    # Utility and bootstrap scripts
├── sample-repos/               # Sample Java applications for testing
├── tests/                      # Test suites (unit, integration, e2e)
├── startup.sh/.bat            # Cross-platform startup scripts
├── deploy.py                  # Automated deployment script
└── validate_deployment.py     # Deployment validation
```

## Backend Structure (`backend/`)

```
backend/
├── app/
│   ├── services/              # Core analysis services
│   │   ├── java_parser_service.py
│   │   ├── codebert_service.py
│   │   ├── graphiti_service.py
│   │   └── repository_service.py
│   ├── api/
│   │   └── routes/            # API endpoint definitions
│   ├── models/                # Data models and entities
│   ├── utils/                 # Utility functions
│   └── config/                # Configuration management
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── .env                       # Environment configuration
```

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── components/            # React components
│   ├── pages/                 # Page-level components
│   ├── services/              # API service layer
│   ├── utils/                 # Utility functions
│   ├── types/                 # TypeScript type definitions
│   └── App.tsx                # Main application component
├── public/                    # Static assets
├── build/                     # Production build output
├── package.json               # Node.js dependencies
├── tsconfig.json              # TypeScript configuration
└── .env.local                 # Environment variables
```

## Docker Structure (`docker/`)

```
docker/
├── development/               # Development environment configs
├── production/                # Production deployment configs
├── nginx/                     # Nginx reverse proxy configs
├── Dockerfile.backend         # Backend container definition
└── Dockerfile.frontend        # Frontend container definition
```

## Documentation Structure (`docs/`)

```
docs/
├── api/                       # API documentation
├── architecture/              # System architecture guides
├── deployment/                # Deployment instructions
├── user-guide/                # User documentation
├── BEDROCK_SETUP.md          # AWS Bedrock integration guide
├── DEPLOYMENT_GUIDE.md       # Comprehensive deployment guide
├── QUICK_START_LINUX.md      # Linux-specific setup
├── QUICK_START_WINDOWS.md    # Windows-specific setup
├── STARTUP.md                # Complete setup instructions
└── TROUBLESHOOTING.md        # Common issues and solutions
```

## Key Configuration Files

### Environment Files
- `backend/.env` - Backend configuration (database, AI services)
- `frontend/.env.local` - Frontend configuration (API endpoints)

### Docker Files
- `docker-compose.verified.yml` - Main Docker Compose configuration
- `podman-compose.verified.yml` - Podman alternative

### Build Files
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `frontend/tsconfig.json` - TypeScript compiler settings

## Naming Conventions

### Files & Directories
- **Python**: snake_case for files and modules
- **TypeScript/React**: PascalCase for components, camelCase for utilities
- **Configuration**: lowercase with hyphens (docker-compose.yml)
- **Documentation**: UPPERCASE.md for main docs, lowercase.md for specific guides

### Code Structure
- **Services**: End with `_service.py` (e.g., `java_parser_service.py`)
- **Models**: Descriptive names (e.g., `JavaClass`, `BusinessRule`)
- **Components**: PascalCase React components (e.g., `NetworkGraph.tsx`)
- **API Routes**: RESTful naming with version prefix (`/api/v1/`)

## Import Patterns

### Backend Python
```python
# Relative imports within app
from app.services.java_parser_service import JavaParserService
from app.models.java_entities import JavaClass

# External dependencies
from fastapi import FastAPI, HTTPException
from graphiti_core import Graphiti
```

### Frontend TypeScript
```typescript
// Relative imports
import { ApiService } from '../services/ApiService';
import { JavaClass } from '../types/JavaTypes';

// External dependencies
import React from 'react';
import { Button } from '@mui/material';
```

## Data Flow Architecture

### Repository Analysis Flow
1. **Repository Service** - Clone and discover repositories
2. **Java Parser Service** - Parse Java code into AST
3. **CodeBERT Service** - Generate semantic embeddings
4. **Graphiti Service** - Store in knowledge graph
5. **Multi-Agent System** - Analyze with specialized agents

### API Layer Organization
- `/api/v1/health` - System health and monitoring
- `/api/v1/repositories` - Repository management
- `/api/v1/analysis` - Code analysis operations
- `/api/v1/search` - Semantic search functionality
- `/api/v1/agents` - Multi-agent system control

## Storage Organization

### File System Layout
```
workspace/
├── repositories/              # Cloned Git repositories
├── analysis-results/          # Analysis output files
├── embeddings/                # Cached CodeBERT embeddings
├── logs/                      # Application logs
└── temp/                      # Temporary processing files
```

### Database Schema (Neo4j)
- **Nodes**: JavaClass, JavaMethod, BusinessRule, StrutsAction, CORBAInterface
- **Relationships**: CALLS, EXTENDS, IMPLEMENTS, CONTAINS, DEPENDS_ON
- **Temporal**: Time-based relationship tracking for code evolution

## Development Workflow

### Adding New Features
1. Backend: Add service in `backend/app/services/`
2. API: Add routes in `backend/app/api/routes/`
3. Frontend: Add components in `frontend/src/components/`
4. Tests: Add tests in appropriate `tests/` subdirectory
5. Documentation: Update relevant docs in `docs/`

### Configuration Management
- Environment-specific configs in `.env` files
- Docker configurations in `docker/` directory
- Kubernetes manifests in `kubernetes/` directory
- Deployment scripts handle cross-platform differences