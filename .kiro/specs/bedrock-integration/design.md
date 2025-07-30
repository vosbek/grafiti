# Design Document

## Overview

The AWS Bedrock integration replaces OpenAI API dependency by implementing LiteLLM as a proxy service that translates OpenAI-compatible requests to AWS Bedrock inference calls. This allows Graphiti to continue using its existing OpenAI client while routing requests to Bedrock models.

## Architecture

### Component Interaction Flow
```
Graphiti Service → LiteLLM Proxy (port 8001) → AWS Bedrock → Claude 3 Sonnet
```

### LiteLLM Proxy Configuration
- **Service**: LiteLLM proxy running as separate container/process
- **Port**: 8001 (configurable via LITELLM_PORT)
- **Model Mapping**: OpenAI format → Bedrock model IDs
- **Authentication**: AWS credentials via environment or IAM roles

## Components and Interfaces

### 1. LiteLLM Proxy Service
**Purpose**: Translate OpenAI API calls to Bedrock format

**Configuration**:
- Model: `bedrock/anthropic.claude-3-sonnet-20240229-v1:0`
- Base URL: `http://localhost:8001/v1`
- API Key: `bedrock-proxy` (placeholder for proxy auth)

### 2. Graphiti Service Updates
**Purpose**: Configure Graphiti to use LiteLLM proxy instead of OpenAI

**Changes**:
- Set `OPENAI_API_BASE=http://localhost:8001/v1`
- Set `OPENAI_API_KEY=bedrock-proxy`
- Add Bedrock-specific configuration parameters### 3. En
vironment Configuration
**Purpose**: Centralized configuration for Bedrock integration

**Variables**:
```bash
# Bedrock Configuration
AWS_BEDROCK_PROXY=true
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
LITELLM_PORT=8001

# Graphiti Configuration (when using Bedrock)
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=bedrock-proxy
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=gpt-4
```

## Data Models

### LiteLLM Configuration File
```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
      aws_region_name: us-east-1
```

### AWS Credentials Structure
- **Method 1**: Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- **Method 2**: IAM roles (for EC2/ECS deployment)
- **Method 3**: AWS credentials file (~/.aws/credentials)

## Error Handling

### Proxy Connection Failures
- **Detection**: Health check on LiteLLM proxy endpoint
- **Fallback**: Clear error message with setup instructions
- **Retry Logic**: Exponential backoff for temporary failures

### AWS Authentication Errors
- **Detection**: AWS credential validation on startup
- **Response**: Detailed error with credential setup guidance
- **Logging**: Structured logs for troubleshooting

## Testing Strategy

### Integration Tests
1. **Proxy Startup**: Verify LiteLLM proxy starts correctly
2. **API Translation**: Test OpenAI → Bedrock request translation
3. **Graphiti Integration**: Verify knowledge graph operations work
4. **Error Scenarios**: Test credential failures and network issues