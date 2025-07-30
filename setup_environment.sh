#!/bin/bash
# CodeAnalysis MultiAgent MVP - Environment Setup Script for Linux/Mac
# Run this BEFORE running setup.py to ensure proper environment configuration

echo ""
echo "========================================"
echo "  CodeAnalysis Environment Setup"
echo "========================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found. Please install AWS CLI first."
    echo "Download from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured."
    echo "Please run: aws configure"
    echo "Then run this script again."
    exit 1
fi

# Get AWS credentials from AWS CLI
echo "Extracting AWS credentials..."
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
export AWS_DEFAULT_REGION=$(aws configure get region)

# Set default region if not configured
if [ -z "$AWS_DEFAULT_REGION" ]; then
    export AWS_DEFAULT_REGION="us-east-1"
    echo "Setting default region to us-east-1"
fi

# Set AWS_REGION for consistency
export AWS_REGION=$AWS_DEFAULT_REGION

echo ""
echo "Environment variables set:"
echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:0:8}..."
echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:0:8}..."
echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"
echo "AWS_REGION=$AWS_REGION"

# Test Bedrock access
echo ""
echo "Testing AWS Bedrock access..."
if aws bedrock list-foundation-models --region $AWS_REGION --query "modelSummaries[?contains(modelId, 'claude-3-sonnet')].modelId" --output text &> /dev/null; then
    echo "SUCCESS: AWS Bedrock access confirmed."
else
    echo "WARNING: Cannot access AWS Bedrock. Check your permissions."
    echo "Required permissions: bedrock:ListFoundationModels, bedrock:InvokeModel"
fi

echo ""
echo "========================================"
echo "  Environment Setup Complete!"
echo "========================================"
echo ""
echo "You can now run: python setup.py"
echo ""

# Export variables for the current shell session
echo "# Run this command to export variables in your current shell:"
echo "export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
echo "export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
echo "export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"
echo "export AWS_REGION=$AWS_REGION"