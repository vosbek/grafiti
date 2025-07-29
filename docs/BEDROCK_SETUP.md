# AWS Bedrock Integration Setup Guide

## Overview

This guide provides detailed instructions for integrating AWS Bedrock with the CodeAnalysis MultiAgent MVP system. Since Graphiti doesn't natively support AWS Bedrock, we use OpenAI-compatible proxy solutions to bridge the gap.

## Prerequisites

### AWS Configuration
- AWS account with Bedrock access enabled
- IAM permissions for Bedrock inference
- AWS CLI configured with appropriate credentials
- Bedrock model access enabled (Claude, etc.)

### Required Dependencies
```bash
pip install litellm boto3 awscli
```

## Setup Options

### Option 1: LiteLLM Proxy (Recommended)

LiteLLM provides the simplest OpenAI-compatible proxy for AWS Bedrock.

#### 1. Install LiteLLM
```bash
pip install litellm[proxy]
```

#### 2. Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

#### 3. Start LiteLLM Proxy
```bash
# Basic setup with Claude 3 Sonnet
litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

# With custom configuration
litellm --config bedrock_config.yaml
```

#### 4. Environment Configuration
Create/update your `.env` file:
```env
# Enable AWS Bedrock Proxy
AWS_BEDROCK_PROXY=true
GRAPHITI_BASE_URL=http://localhost:8001
GRAPHITI_API_KEY=dummy

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# LLM Provider (use openai for proxy compatibility)
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=bedrock/anthropic.claude-3-sonnet
```

#### 5. LiteLLM Configuration File (Optional)
Create `bedrock_config.yaml`:
```yaml
model_list:
  - model_name: claude-3-sonnet
    litellm_params:
      model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
      aws_region_name: us-east-1

  - model_name: claude-3-haiku
    litellm_params:
      model: bedrock/anthropic.claude-3-haiku-20240307-v1:0
      aws_region_name: us-east-1

litellm_settings:
  set_verbose: true
  drop_params: true
```

### Option 2: AWS Bedrock Access Gateway (Enterprise)

For production deployments, use AWS's official Bedrock Access Gateway.

#### 1. Clone and Deploy
```bash
git clone https://github.com/aws-samples/bedrock-access-gateway
cd bedrock-access-gateway

# Install dependencies
npm install

# Configure AWS CDK
npm run cdk bootstrap

# Deploy to AWS
npm run cdk deploy
```

#### 2. Environment Configuration
```env
# Enable AWS Bedrock Proxy
AWS_BEDROCK_PROXY=true
GRAPHITI_BASE_URL=https://your-alb-endpoint.amazonaws.com
GRAPHITI_API_KEY=your-api-key

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# LLM Provider
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

### Option 3: Custom Serverless Proxy

For cost-optimized deployments, use a serverless proxy.

#### 1. Deploy Serverless Proxy
```bash
git clone https://github.com/jparkerweb/bedrock-proxy-endpoint
cd bedrock-proxy-endpoint

# Configure serverless
npm install -g serverless
npm install

# Deploy
serverless deploy
```

#### 2. Environment Configuration
```env
# Enable AWS Bedrock Proxy
AWS_BEDROCK_PROXY=true
GRAPHITI_BASE_URL=https://abc123.lambda-url.us-east-1.on.aws
GRAPHITI_API_KEY=your-lambda-key

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## Complete Environment Configuration

### Production .env File
```env
# Application Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000

# AWS Bedrock Configuration
AWS_BEDROCK_PROXY=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Graphiti LLM Configuration (for Bedrock proxy)
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=bedrock/anthropic.claude-3-sonnet
GRAPHITI_BASE_URL=http://localhost:8001
GRAPHITI_API_KEY=dummy

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=codeanalysis123

# CodeBERT Configuration
CODEBERT_MODEL=microsoft/codebert-base
USE_GPU=true

# Workspace Configuration
WORKSPACE_DIR=./workspace
MAX_REPOSITORIES=100
```

## Available Bedrock Models

### Claude Models (Recommended)
```bash
# Claude 3 Sonnet (balanced performance)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Claude 3 Haiku (fastest, cost-effective)
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Claude 3 Opus (highest capability)
BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0

# Claude 3.5 Sonnet (latest)
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

### Other Supported Models
```bash
# Meta Llama
BEDROCK_MODEL_ID=meta.llama2-70b-chat-v1

# Amazon Titan
BEDROCK_MODEL_ID=amazon.titan-text-express-v1

# Cohere Command
BEDROCK_MODEL_ID=cohere.command-text-v14
```

## Startup Instructions

### 1. Start Proxy Service
```bash
# Terminal 1: Start LiteLLM proxy
litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

# Wait for "LiteLLM: Proxy running on http://0.0.0.0:8001"
```

### 2. Start Application
```bash
# Terminal 2: Start main application
cd backend
python main.py

# Or use bootstrap script
python bootstrap.py --bedrock
```

### 3. Verify Connection
```bash
# Test proxy endpoint
curl http://localhost:8001/v1/models

# Test application health
curl http://localhost:8000/api/v1/health/detailed
```

## Verification and Testing

### 1. Test Bedrock Connectivity
```python
# test_bedrock.py
import boto3

def test_bedrock_access():
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}]
            })
        )
        print("✓ Bedrock access working")
        return True
    except Exception as e:
        print(f"✗ Bedrock access failed: {e}")
        return False

if __name__ == "__main__":
    test_bedrock_access()
```

### 2. Test Proxy Integration
```bash
# Test LiteLLM proxy
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bedrock/anthropic.claude-3-sonnet",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

### 3. Test Graphiti Integration
```bash
# Test semantic search with Bedrock
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "payment processing logic",
    "options": {"max_results": 5}
  }'
```

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Found
```bash
# Error: NoCredentialsError
# Solution: Configure AWS credentials
aws configure
# or
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

#### 2. Bedrock Model Access Denied
```bash
# Error: AccessDeniedException
# Solution: Enable model access in AWS Console
# Go to Bedrock Console → Model Access → Request Access
```

#### 3. LiteLLM Proxy Connection Failed
```bash
# Error: Connection refused
# Solution: Ensure proxy is running
ps aux | grep litellm
# Restart if needed
litellm --model bedrock/anthropic.claude-3-sonnet --port 8001
```

#### 4. Graphiti Initialization Failed
```bash
# Error: Invalid API key or endpoint
# Solution: Check environment variables
echo $GRAPHITI_BASE_URL
echo $AWS_BEDROCK_PROXY

# Verify proxy is responding
curl http://localhost:8001/health
```

#### 5. High Latency Issues
```bash
# Problem: Slow response times
# Solutions:
# 1. Use Haiku model for faster responses
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# 2. Enable connection pooling
export LITELLM_POOL_SIZE=10

# 3. Use regional endpoints
export AWS_REGION=us-east-1  # Choose closest region
```

### Performance Optimization

#### 1. Model Selection
```bash
# For speed: Claude 3 Haiku
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# For balance: Claude 3 Sonnet
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# For quality: Claude 3 Opus (slower, more expensive)
BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
```

#### 2. Proxy Configuration
```yaml
# bedrock_config.yaml - optimized settings
litellm_settings:
  set_verbose: false
  drop_params: true
  success_callback: []
  failure_callback: []
  cache: true
  cache_ttl: 3600
  max_parallel_requests: 100
```

#### 3. Connection Pooling
```bash
# Start proxy with connection pooling
litellm --model bedrock/anthropic.claude-3-sonnet \
        --port 8001 \
        --num_workers 4 \
        --max_requests 1000
```

## Production Deployment

### Docker Compose Configuration
```yaml
# docker-compose.bedrock.yml
version: '3.8'
services:
  litellm-proxy:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "8001:8001"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=${AWS_REGION}
    command: --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

  codeanalysis-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_BEDROCK_PROXY=true
      - GRAPHITI_BASE_URL=http://litellm-proxy:8001
      - GRAPHITI_API_KEY=dummy
    depends_on:
      - litellm-proxy
      - neo4j

  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/codeanalysis123
```

### Kubernetes Deployment
```yaml
# k8s-bedrock.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: litellm-proxy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: litellm-proxy
  template:
    metadata:
      labels:
        app: litellm-proxy
    spec:
      containers:
      - name: litellm
        image: ghcr.io/berriai/litellm:main-latest
        ports:
        - containerPort: 8001
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret-access-key
        command: ["litellm", "--model", "bedrock/anthropic.claude-3-sonnet-20240229-v1:0", "--port", "8001"]
---
apiVersion: v1
kind: Service
metadata:
  name: litellm-proxy-service
spec:
  selector:
    app: litellm-proxy
  ports:
  - port: 8001
    targetPort: 8001
```

## Cost Optimization

### Model Cost Comparison (per 1K tokens)
```bash
# Input / Output tokens
Claude 3 Haiku:   $0.00025 / $0.00125
Claude 3 Sonnet:  $0.003   / $0.015
Claude 3 Opus:    $0.015   / $0.075

# Recommendation: Use Haiku for high-volume operations
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### Usage Monitoring
```bash
# Enable AWS CloudWatch metrics
export AWS_BEDROCK_METRICS=true

# Monitor costs with AWS CLI
aws bedrock get-model-invocation-logging-configuration
aws cloudwatch get-metric-statistics --namespace AWS/Bedrock
```

## Security Best Practices

### 1. IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
      ]
    }
  ]
}
```

### 2. Network Security
```bash
# Use VPC endpoints for Bedrock (production)
export AWS_BEDROCK_ENDPOINT_URL=https://vpce-xxxxx-bedrock.us-east-1.vpce.amazonaws.com

# Enable SSL/TLS for proxy
litellm --model bedrock/anthropic.claude-3-sonnet \
        --ssl-certfile cert.pem \
        --ssl-keyfile key.pem
```

### 3. Secrets Management
```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret --name codeanalysis/bedrock \
  --secret-string '{"api_key":"dummy","model_id":"anthropic.claude-3-sonnet-20240229-v1:0"}'

# Reference in application
export GRAPHITI_API_KEY=$(aws secretsmanager get-secret-value --secret-id codeanalysis/bedrock --query SecretString --output text | jq -r .api_key)
```

---

## Quick Start Summary

For immediate AWS Bedrock integration:

```bash
# 1. Install dependencies
pip install litellm boto3

# 2. Configure AWS
aws configure

# 3. Start proxy
litellm --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0 --port 8001

# 4. Set environment
export AWS_BEDROCK_PROXY=true
export GRAPHITI_BASE_URL=http://localhost:8001
export GRAPHITI_API_KEY=dummy

# 5. Start application
python bootstrap.py --bedrock
```

The system is now ready to use AWS Bedrock through Graphiti! 🚀