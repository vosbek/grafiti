# Legacy Banking Application

## Overview

This is a sample enterprise banking application that demonstrates typical patterns found in legacy Java systems. It combines multiple frameworks and technologies commonly seen in large-scale financial services applications built in the early 2000s.

## Technology Stack

### Core Frameworks
- **Struts 1.3.10**: Web framework for MVC architecture
- **Spring 4.3.30**: Dependency injection and transaction management
- **Hibernate 4.3.11**: Object-relational mapping
- **CORBA (JacORB 3.9)**: Distributed computing middleware

### Infrastructure
- **Oracle Database**: Primary data storage
- **Apache Tomcat**: Application server
- **Log4j**: Logging framework
- **Spring Security**: Authentication and authorization

## Architecture Patterns

### 1. Struts MVC Pattern
- **Actions**: Handle HTTP requests and coordinate business logic
- **Forms**: Data transfer objects for request/response
- **JSPs**: Presentation layer with custom tag libraries
- **Configuration**: XML-based action mappings and validation rules

### 2. Spring Integration
- **Dependency Injection**: Service layer components managed by Spring
- **Transaction Management**: Declarative transactions with @Transactional
- **Security**: Spring Security integration for authentication

### 3. CORBA Distributed Services
- **POA Servants**: Server-side implementation of CORBA interfaces
- **IDL Definitions**: Interface definitions for distributed services
- **Remote Calls**: Cross-system communication via CORBA

### 4. Data Access Layer
- **DAO Pattern**: Data access objects with Hibernate
- **Entity Mapping**: JPA annotations for object-relational mapping
- **Connection Pooling**: Database connection management

## Business Domain

### Core Entities
- **Customer**: Bank customer with personal and account information
- **Account**: Bank accounts (checking, savings, premium)
- **Transaction**: Financial transactions (deposits, withdrawals, transfers)
- **Security**: Authentication, authorization, and audit trail

### Business Rules
1. **Account Management**
   - Minimum balance requirements ($100 for checking accounts)
   - Daily withdrawal limits ($5,000)
   - Overdraft protection and fees ($35)

2. **Authentication & Security**
   - Multi-factor authentication for high-risk customers
   - Account lockout after 3 failed login attempts
   - Session timeout after 15 minutes of inactivity
   - IP address validation and geolocation checks

3. **Interest Calculations**
   - Checking accounts: 0.01% APY on balances > $1,000
   - Savings accounts: 0.05% APY on all balances
   - Premium accounts: Additional 0.02% bonus APY

4. **Compliance Requirements**
   - SOX: All transactions logged for audit
   - BSA: Customer identification for transactions > $10,000
   - PCI: Secure handling of payment card data

## Code Analysis Opportunities

This sample application provides excellent examples for demonstrating the capabilities of the CodeAnalysis-MultiAgent-MVP system:

### 1. Legacy Framework Analysis
- **Struts Actions**: Complex action classes with business logic
- **Configuration Mapping**: XML-based configuration analysis
- **JSP Flow Analysis**: Page flow and navigation patterns

### 2. Business Rule Extraction
- **Validation Logic**: Password complexity, account eligibility
- **Calculation Rules**: Interest rates, fees, limits
- **Workflow Patterns**: Transaction processing, authentication flows

### 3. Security Pattern Analysis
- **Authentication Mechanisms**: Multi-factor authentication
- **Authorization Controls**: Role-based access control
- **Audit Trail**: Security event logging

### 4. CORBA Integration Patterns
- **Distributed Services**: Remote service calls
- **Interface Definitions**: IDL specifications
- **Error Handling**: Distributed exception management

### 5. Technical Debt Identification
- **Code Complexity**: Methods with high cyclomatic complexity
- **Framework Coupling**: Tight coupling to legacy frameworks
- **Security Vulnerabilities**: Potential security issues

## Migration Opportunities

### Spring Boot Modernization
- **Struts → Spring MVC**: Convert actions to REST controllers
- **XML Configuration → Annotations**: Replace XML with annotation-based config
- **JSPs → Thymeleaf**: Modern template engine integration

### Microservices Decomposition
- **Account Service**: Customer account management
- **Transaction Service**: Payment processing
- **Security Service**: Authentication and authorization
- **Reporting Service**: Financial reporting and analytics

### Cloud-Native Patterns
- **Configuration Management**: External configuration
- **Service Discovery**: Dynamic service registration
- **Circuit Breakers**: Fault tolerance patterns
- **Observability**: Distributed tracing and metrics

## Analysis Scenarios

When analyzing this application with CodeAnalysis-MultiAgent-MVP, you can explore:

1. **"Find all authentication and security validation logic"**
   - Identifies LoginAction, SecurityContext, validation methods
   - Maps security patterns across the application

2. **"What are the business rules for account withdrawals?"**
   - Extracts withdrawal limits, validation rules, overdraft logic
   - Documents compliance requirements

3. **"How complex would it be to migrate from Struts to Spring Boot?"**
   - Analyzes action mappings, form beans, JSP dependencies
   - Provides effort estimates and migration roadmap

4. **"Map all CORBA interfaces and their usage patterns"**
   - Identifies distributed service boundaries
   - Analyzes remote call patterns and dependencies

5. **"Find all embedded business calculations and validation rules"**
   - Extracts interest calculations, fee structures, limits
   - Documents domain-specific business logic

## Usage with CodeAnalysis System

### Repository Discovery
```bash
./startup.sh --discover-from=./sample-repos/legacy-banking-app
```

This will:
1. Clone the sample repository
2. Analyze Maven dependencies
3. Parse Java source code and Struts configuration
4. Generate semantic embeddings for all code components
5. Populate the knowledge graph with entities and relationships
6. Enable intelligent querying through the multi-agent system

### Expected Analysis Results
- **Classes Detected**: ~50+ Java classes
- **Struts Actions**: 15+ action classes with mappings
- **Business Rules**: 20+ validation and calculation rules
- **Security Patterns**: Authentication, authorization, audit patterns
- **CORBA Interfaces**: Distributed service definitions
- **Technical Debt**: Complexity metrics and improvement opportunities

This sample application serves as an excellent demonstration of the system's capabilities for analyzing complex enterprise Java applications with mixed legacy frameworks.