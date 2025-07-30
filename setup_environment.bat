@echo off
REM CodeAnalysis MultiAgent MVP - Environment Setup Script for Windows
REM Run this BEFORE running setup.py to ensure proper environment configuration

echo.
echo ========================================
echo  CodeAnalysis Environment Setup
echo ========================================
echo.

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS CLI not found. Please install AWS CLI first.
    echo Download from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
    pause
    exit /b 1
)

REM Check if AWS is configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS credentials not configured.
    echo Please run: aws configure
    echo Then run this script again.
    pause
    exit /b 1
)

REM Get AWS credentials from AWS CLI
echo Extracting AWS credentials...
for /f "tokens=2 delims= " %%i in ('aws configure get aws_access_key_id') do set AWS_ACCESS_KEY_ID=%%i
for /f "tokens=2 delims= " %%i in ('aws configure get aws_secret_access_key') do set AWS_SECRET_ACCESS_KEY=%%i
for /f "tokens=2 delims= " %%i in ('aws configure get region') do set AWS_DEFAULT_REGION=%%i

REM Set default region if not configured
if "%AWS_DEFAULT_REGION%"=="" (
    set AWS_DEFAULT_REGION=us-east-1
    echo Setting default region to us-east-1
)

REM Export environment variables for current session
set AWS_REGION=%AWS_DEFAULT_REGION%

echo.
echo Environment variables set:
echo AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID:~0,8%...
echo AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY:~0,8%...
echo AWS_DEFAULT_REGION=%AWS_DEFAULT_REGION%
echo AWS_REGION=%AWS_REGION%

REM Test Bedrock access
echo.
echo Testing AWS Bedrock access...
aws bedrock list-foundation-models --region %AWS_REGION% --query "modelSummaries[?contains(modelId, 'claude-3-sonnet')].modelId" --output text >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Cannot access AWS Bedrock. Check your permissions.
    echo Required permissions: bedrock:ListFoundationModels, bedrock:InvokeModel
) else (
    echo SUCCESS: AWS Bedrock access confirmed.
)

echo.
echo ========================================
echo  Environment Setup Complete!
echo ========================================
echo.
echo You can now run: python setup.py
echo.
pause