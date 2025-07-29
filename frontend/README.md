# CodeAnalysis MultiAgent MVP - Frontend

Enterprise React TypeScript dashboard for Java code analysis with AI-powered insights.

## Features

- **Dashboard**: System health monitoring and statistics
- **Repository Management**: Discovery, cloning, and status tracking
- **Semantic Search**: Natural language code search with CodeBERT
- **AI Agent Management**: Execute and monitor specialized analysis agents
- **Analysis Results**: Comprehensive visualization of findings and recommendations
- **Settings**: System configuration and AWS Bedrock integration

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Development

```bash
# Install dependencies
npm install

# Start development server (connects to backend at localhost:8000)
npm start

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint

# Format code
npm run format
```

## Environment Configuration

Create `.env.local` file for environment-specific settings:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Development settings
REACT_APP_DEBUG=true
```

## Architecture

### Components Structure
```
src/
├── components/          # Reusable UI components
│   └── NetworkGraph.tsx # Code relationship visualization
├── pages/              # Main application pages
│   ├── Dashboard.tsx   # System overview and health
│   ├── RepositoryManagement.tsx # Repository operations
│   ├── SemanticSearch.tsx # Code search interface
│   ├── AgentManagement.tsx # AI agent controls
│   ├── AnalysisResults.tsx # Results visualization
│   └── Settings.tsx    # System configuration
├── services/           # API integration
│   └── api.ts         # Centralized API client
├── types/             # TypeScript definitions
│   └── api.ts        # API response types
└── App.tsx           # Main application component
```

### Key Technologies

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type safety and enhanced development experience
- **Material-UI v5** - Enterprise-grade UI components
- **Recharts** - Data visualization and charting
- **Vis-Network** - Interactive network graphs for code relationships
- **Axios** - HTTP client with interceptors and error handling

### API Integration

The frontend communicates with the FastAPI backend through a centralized API service:

```typescript
// Example API usage
import apiService from '../services/api';

// Get system health
const health = await apiService.getHealth(true);

// Perform semantic search
const results = await apiService.semanticSearch({
  query: "payment processing logic",
  options: { max_results: 20 }
});

// Execute AI agent
const response = await apiService.executeAgent('security_analyzer', {
  repositories: ['repo1', 'repo2'],
  parameters: { detailed_analysis: true }
});
```

## Features Overview

### Dashboard
- Real-time system health monitoring
- Service status indicators (Graphiti, CodeBERT, Repository)
- Resource utilization (CPU, memory, GPU)
- Analysis statistics and quick actions

### Repository Management
- Automated repository discovery from enterprise GitHub
- Bulk repository cloning with progress tracking
- Repository status and statistics display
- Job monitoring with real-time updates

### Semantic Search
- Natural language code search using CodeBERT embeddings
- Advanced filtering (repositories, entity types, frameworks)
- Search suggestions and result highlighting
- Export functionality for search results

### AI Agent Management
- 8 specialized analysis agents (architecture, security, legacy detection)
- Agent execution with parameter customization
- Real-time job monitoring and results display
- Performance metrics and success rates

### Analysis Results
- Comprehensive findings visualization with charts
- Tabbed interface for findings, recommendations, code references
- Interactive finding details with impact assessment
- Export capabilities for analysis reports

### Settings
- AWS Bedrock configuration (models, regions, proxy settings)
- CodeBERT optimization (GPU usage, batch sizes)
- Performance tuning (concurrent operations, cache sizes)
- System information display

## Production Deployment

### Docker Build
```bash
# Build production image
docker build -t codeanalysis-frontend .

# Run container
docker run -p 3000:80 -e REACT_APP_API_URL=http://your-api-server codeanalysis-frontend
```

### Environment Variables
```env
# Production API endpoint
REACT_APP_API_URL=https://api.yourcompany.com

# Optional: Enable/disable features
REACT_APP_ENABLE_EXPORT=true
REACT_APP_ENABLE_DEBUG=false
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-frontend-domain.com;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://your-backend-server:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Considerations

- **Code Splitting**: Components are lazy-loaded for optimal bundle size
- **API Caching**: Intelligent caching of API responses
- **Virtual Scrolling**: Large datasets are virtualized for performance
- **Debounced Search**: Search queries are debounced to reduce API calls
- **Image Optimization**: All images are optimized for web delivery

## Contributing

1. Follow TypeScript strict mode guidelines
2. Use Material-UI components consistently
3. Implement proper error handling and loading states
4. Add JSDoc comments for complex functions
5. Write unit tests for utility functions
6. Follow the established folder structure

## Troubleshooting

### Common Issues

**API Connection Errors**:
```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Verify CORS configuration
# Check browser network tab for CORS errors
```

**Build Errors**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run build 2>&1 | grep error
```

**Performance Issues**:
- Enable production build: `npm run build`
- Check React DevTools Profiler
- Monitor network requests in browser DevTools
- Verify API response times

### Development Tips

- Use React DevTools for component debugging
- Enable Redux DevTools for state management
- Use the Network tab to monitor API calls
- Test responsive design with device emulation