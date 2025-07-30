# CodeAnalysis MultiAgent MVP - Demo Setup

## Quick Start (No AWS Required)

This demo setup allows you to run the entire CodeAnalysis system without AWS credentials to see all the core functionality working.

### Prerequisites

- Docker or Podman installed
- Python 3.7+ 
- 8GB+ RAM recommended

### One-Command Demo

```bash
# Install demo requirements
pip install -r demo-requirements.txt

# Start everything
python start-demo.py

# Check status
python start-demo.py --status

# Stop everything
python start-demo.py --stop
```

### What You'll Get

✅ **Frontend Dashboard** - http://localhost:3000
- Repository management interface
- Code analysis visualization
- Search functionality
- Network graphs

✅ **Backend API** - http://localhost:8000
- Full REST API with 8 specialized agents
- Java code parsing and analysis
- CodeBERT embeddings (CPU mode)
- Knowledge graph operations

✅ **Neo4j Graph Database** - http://localhost:7474
- Temporal knowledge graph
- Code relationships and entities
- Query interface (neo4j / codeanalysis123)

✅ **Core Services**
- Redis caching
- Repository management
- Multi-agent analysis system

### What's Limited in Demo Mode

⚠️ **No AWS Bedrock Integration**
- Graphiti LLM features disabled
- Some advanced AI analysis limited
- Core parsing and graph features work fully

### Demo Workflow

1. **Access Frontend**: http://localhost:3000
2. **Upload/Analyze Java Code**: Use repository management
3. **View Results**: See parsed classes, methods, relationships
4. **Explore Graph**: Use Neo4j browser to query knowledge graph
5. **Test API**: Use http://localhost:8000/docs for API testing

### Troubleshooting

**Services won't start?**
```bash
# Check what's running
python start-demo.py --status

# Stop everything and retry
python start-demo.py --stop
python start-demo.py
```

**Port conflicts?**
- Default ports: 3000, 7474, 7687, 6379, 8000
- Stop other services using these ports

**Memory issues?**
- Ensure 8GB+ RAM available
- Close other applications

### Next Steps

Once you see the demo working:
1. Configure AWS credentials for full Bedrock integration
2. Use the full `setup.py` script for production deployment
3. Analyze real enterprise Java repositories

### Demo Architecture

```
Frontend (3000) ──► Backend (8000) ──► Neo4j (7687)
                           │
                           └──► Redis (6379)
```

**Ready to explore enterprise Java code analysis!**