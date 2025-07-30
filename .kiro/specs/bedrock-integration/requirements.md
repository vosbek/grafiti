# Requirements Document

## Introduction

Configure the CodeAnalysis MultiAgent MVP to use AWS Bedrock inference profiles instead of OpenAI API, implementing LiteLLM as a proxy to provide OpenAI-compatible endpoints for the Graphiti knowledge graph system.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to configure AWS Bedrock as the LLM provider, so that the application can use enterprise-approved AI models without OpenAI dependency.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL connect to AWS Bedrock via LiteLLM proxy
2. WHEN Graphiti requests LLM inference THEN it SHALL route through LiteLLM to Bedrock
3. IF OpenAI API key is not available THEN system SHALL use Bedrock configuration
4. WHEN using Bedrock THEN system SHALL support Claude 3 Sonnet model

### Requirement 2

**User Story:** As a developer, I want LiteLLM proxy automatically configured, so that Graphiti can communicate with Bedrock using OpenAI-compatible API format.

#### Acceptance Criteria

1. WHEN system deploys THEN LiteLLM proxy SHALL start on port 8001
2. WHEN proxy starts THEN it SHALL authenticate with AWS credentials
3. WHEN Graphiti makes API calls THEN proxy SHALL translate to Bedrock format
4. IF proxy fails THEN system SHALL provide clear error messages
### Req
uirement 3

**User Story:** As a system operator, I want environment-based configuration, so that I can easily switch between development and production Bedrock setups.

#### Acceptance Criteria

1. WHEN environment variables are set THEN system SHALL use Bedrock configuration
2. WHEN AWS_BEDROCK_PROXY=true THEN system SHALL start LiteLLM proxy
3. WHEN BEDROCK_MODEL_ID is specified THEN system SHALL use that model
4. IF AWS credentials are missing THEN system SHALL fail with clear error

### Requirement 4

**User Story:** As a developer, I want Docker support for Bedrock, so that the entire stack can run in containers with proper AWS integration.

#### Acceptance Criteria

1. WHEN using Docker profile "bedrock" THEN LiteLLM container SHALL start
2. WHEN containers start THEN AWS credentials SHALL be properly mounted
3. WHEN backend connects THEN it SHALL use proxy endpoint for LLM calls
4. IF Docker deployment fails THEN system SHALL provide troubleshooting guidance