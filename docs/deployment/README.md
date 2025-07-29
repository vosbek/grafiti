# Deployment Guide

## Overview

The CodeAnalysis-MultiAgent-MVP can be deployed in various environments, from local development to enterprise Kubernetes clusters. This guide covers all deployment scenarios with specific configurations for different scales.

## Quick Start

### Local Development

The fastest way to get started is using the provided startup scripts:

```bash
# Linux/macOS/AWS
./startup.sh

# Windows
startup.bat
```

This will automatically:

1. Detect your hardware (CPU/GPU/Memory)
2. Install dependencies
3. Configure services based on available resources
4. Start all components
5. Open the web interface

### Docker Compose (Recommended for Testing)

```bash
# Clone the repository
git clone https://github.com/your-org/codeanalysis-multiagent-mvp.git
cd codeanalysis-multiagent-mvp

# Start services
docker-compose -f docker/development/docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Kubernetes (Production)

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/
```

## System Requirements

### Minimum Requirements (Development/Testing)

- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 100GB SSD
- **Network**: 10 Mbps
- **OS**: Linux, macOS, Windows 10+

### Recommended Requirements (Production)

- **CPU**: 16+ cores
- **Memory**: 64GB+ RAM
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for CodeBERT acceleration)
- **Storage**: 1TB+ NVMe SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 20.04 LTS, RHEL 8+, or equivalent

### Enterprise Scale Requirements

- **CPU**: 32+ cores per node
- **Memory**: 128GB+ RAM per node
- **GPU**: Multiple NVIDIA A100 or V100 GPUs
- **Storage**: 10TB+ distributed storage
- **Network**: 10 Gbps with low latency
- **Nodes**: 3+ node Kubernetes cluster

## Pre-Deployment Setup

### 1. Environment Variables

Create a `.env` file based on your environment:

```bash
# Hardware Configuration
DEVICE=cuda  # or cpu
CPU_CORES=16
MEMORY_GB=64
GPU_AVAILABLE=true

# Database Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
POSTGRES_HOST=postgres
POSTGRES_USER=codeanalysis
POSTGRES_PASSWORD=your-postgres-password
REDIS_URL=redis://redis:6379

# Application Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-very-secure-secret-key
ENABLE_AUTH=true

# Performance Tuning
EMBEDDING_BATCH_SIZE=32
THREAD_POOL_SIZE=20
MAX_CONCURRENT_CLONES=8
MAX_CONCURRENT_AGENTS=6

# Enterprise Features
ENABLE_METRICS=true
ENABLE_TRACING=true
LOG_LEVEL=INFO
```

### 2. SSL/TLS Certificates

For production deployments, configure SSL certificates:

```bash
# Generate self-signed certificates (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt
certbot certonly --dns-cloudflare --dns-cloudflare-credentials ~/.secrets/certbot/cloudflare.ini -d api.yourdomain.com
```

### 3. External Dependencies

Ensure these services are available:

- **Neo4j 5.15+**: Graph database for knowledge storage
- **PostgreSQL 13+**: Metadata and job tracking
- **Redis 6+**: Caching and message queuing
- **NVIDIA Docker Runtime**: For GPU support (if using GPUs)

## Deployment Methods

## Method 1: Docker Compose

### Development Environment

```yaml
# docker/development/docker-compose.yml
version: '3.8'

services:
  app:
    build: 
      context: ../../
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
    volumes:
      - ../../:/app
      - repositories:/app/repositories
    depends_on:
      - neo4j
      - postgres
      - redis

  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=codeanalysis
      - POSTGRES_USER=codeanalysis
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  frontend:
    build:
      context: ../../
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

volumes:
  neo4j_data:
  postgres_data:
  redis_data:
  repositories:
```

Start the development environment:

```bash
docker-compose -f docker/development/docker-compose.yml up -d
```

### Production Environment

```yaml
# docker/production/docker-compose.yml
version: '3.8'

services:
  app:
    image: codeanalysis-mvp:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    volumes:
      - /data/repositories:/app/repositories
      - /data/embeddings:/app/embeddings
    depends_on:
      - neo4j
      - postgres
      - redis

  worker:
    image: codeanalysis-mvp:latest
    command: celery -A app.main.celery worker --loglevel=info
    deploy:
      replicas: 5
    environment:
      - ENVIRONMENT=production
    volumes:
      - /data/repositories:/app/repositories
    depends_on:
      - redis
      - postgres

  neo4j:
    image: neo4j:5.15-enterprise
    deploy:
      replicas: 3
    environment:
      - NEO4J_AUTH=neo4j/production-password
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    volumes:
      - neo4j_data:/data
    ports:
      - "7687:7687"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
```

## Method 2: Kubernetes

### Namespace and RBAC

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: codeanalysis
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: codeanalysis
  namespace: codeanalysis
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: codeanalysis
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: codeanalysis
subjects:
- kind: ServiceAccount
  name: codeanalysis
  namespace: codeanalysis
roleRef:
  kind: ClusterRole
  name: codeanalysis
  apiGroup: rbac.authorization.k8s.io
```

### ConfigMap

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: codeanalysis-config
  namespace: codeanalysis
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  NEO4J_URI: "bolt://neo4j:7687"
  POSTGRES_HOST: "postgres"
  REDIS_URL: "redis://redis:6379"
  EMBEDDING_BATCH_SIZE: "32"
  THREAD_POOL_SIZE: "20"
  MAX_CONCURRENT_CLONES: "8"
  ENABLE_METRICS: "true"
```

### Secrets

```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: codeanalysis-secrets
  namespace: codeanalysis
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  NEO4J_PASSWORD: <base64-encoded-password>
  POSTGRES_PASSWORD: <base64-encoded-password>
```

### Backend Deployment

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeanalysis-backend
  namespace: codeanalysis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codeanalysis-backend
  template:
    metadata:
      labels:
        app: codeanalysis-backend
    spec:
      serviceAccountName: codeanalysis
      containers:
      - name: backend
        image: codeanalysis-mvp:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: codeanalysis-config
        - secretRef:
            name: codeanalysis-secrets
        resources:
          limits:
            cpu: 4
            memory: 8Gi
            nvidia.com/gpu: 1
          requests:
            cpu: 2
            memory: 4Gi
        volumeMounts:
        - name: repositories
          mountPath: /app/repositories
        - name: embeddings
          mountPath: /app/embeddings
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: repositories
        persistentVolumeClaim:
          claimName: repositories-pvc
      - name: embeddings
        persistentVolumeClaim:
          claimName: embeddings-pvc
      nodeSelector:
        accelerator: nvidia-tesla-v100
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

### Worker Deployment

```yaml
# kubernetes/worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeanalysis-worker
  namespace: codeanalysis
spec:
  replicas: 5
  selector:
    matchLabels:
      app: codeanalysis-worker
  template:
    metadata:
      labels:
        app: codeanalysis-worker
    spec:
      containers:
      - name: worker
        image: codeanalysis-mvp:latest
        command: ["celery", "-A", "app.main.celery", "worker", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: codeanalysis-config
        - secretRef:
            name: codeanalysis-secrets
        resources:
          limits:
            cpu: 2
            memory: 4Gi
          requests:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: repositories
          mountPath: /app/repositories
      volumes:
      - name: repositories
        persistentVolumeClaim:
          claimName: repositories-pvc
```

### Services

```yaml
# kubernetes/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: codeanalysis-backend
  namespace: codeanalysis
spec:
  selector:
    app: codeanalysis-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: codeanalysis
spec:
  selector:
    app: neo4j
  ports:
  - port: 7687
    targetPort: 7687
  type: ClusterIP
```

### Ingress

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codeanalysis-ingress
  namespace: codeanalysis
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: codeanalysis-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: codeanalysis-backend
            port:
              number: 8000
```

### Horizontal Pod Autoscaler

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codeanalysis-backend-hpa
  namespace: codeanalysis
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codeanalysis-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods -n codeanalysis

# View logs
kubectl logs -f deployment/codeanalysis-backend -n codeanalysis

# Port forward for testing
kubectl port-forward service/codeanalysis-backend 8000:8000 -n codeanalysis
```

## Method 3: Cloud Platforms

### AWS EKS

```bash
# Create EKS cluster with mixed node groups
eksctl create cluster \
  --name codeanalysis-cluster \
  --region us-west-2 \
  --with-oidc \
  --managed \
  --node-groups-cpu-only \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --instance-types c5.2xlarge,c5.4xlarge

# Add GPU node group for CodeBERT
eksctl create nodegroup \
  --cluster codeanalysis-cluster \
  --region us-west-2 \
  --name gpu-nodes \
  --instance-types g4dn.xlarge,g4dn.2xlarge \
  --nodes 2 \
  --nodes-min 0 \
  --nodes-max 5 \
  --managed

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/main/nvidia-device-plugin.yml

# Deploy application
kubectl apply -f kubernetes/
```

### Azure AKS

```bash
# Create AKS cluster
az aks create \
  --resource-group codeanalysis-rg \
  --name codeanalysis-cluster \
  --location eastus \
  --enable-addons monitoring \
  --kubernetes-version 1.27.0 \
  --generate-ssh-keys

# Add GPU node pool
az aks nodepool add \
  --resource-group codeanalysis-rg \
  --cluster-name codeanalysis-cluster \
  --name gpunodes \
  --node-count 2 \
  --node-vm-size Standard_NC6s_v3 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 5

# Get credentials
az aks get-credentials --resource-group codeanalysis-rg --name codeanalysis-cluster

# Deploy application
kubectl apply -f kubernetes/
```

### Google GKE

```bash
# Create GKE cluster with GPU support
gcloud container clusters create codeanalysis-cluster \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade

# Add GPU node pool
gcloud container node-pools create gpu-pool \
  --cluster codeanalysis-cluster \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --num-nodes 2 \
  --enable-autoscaling \
  --min-nodes 0 \
  --max-nodes 5

# Install NVIDIA drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

# Deploy application
kubectl apply -f kubernetes/
```

## Post-Deployment Configuration

### 1. Database Initialization

```bash
# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=neo4j -n codeanalysis --timeout=300s

# Initialize Neo4j
kubectl exec -it deployment/neo4j -n codeanalysis -- cypher-shell -u neo4j -p password "CREATE INDEX ON :JavaClass(qualified_name);"

# Initialize PostgreSQL
kubectl exec -it deployment/postgres -n codeanalysis -- psql -U codeanalysis -d codeanalysis -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

### 2. Load Balancer Configuration

For production deployments, configure a load balancer:

```yaml
# kubernetes/load-balancer.yaml
apiVersion: v1
kind: Service
metadata:
  name: codeanalysis-lb
  namespace: codeanalysis
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
spec:
  type: LoadBalancer
  selector:
    app: codeanalysis-backend
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  - port: 443
    targetPort: 8000
    protocol: TCP
```

### 3. Monitoring Setup

Deploy Prometheus and Grafana:

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin

# Access Grafana
kubectl port-forward service/prometheus-grafana 3000:80 -n monitoring
```

### 4. Backup Configuration

Set up automated backups:

```yaml
# kubernetes/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: neo4j-backup
  namespace: codeanalysis
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: neo4j:5.15
            command:
            - /bin/bash
            - -c
            - |
              neo4j-admin database dump --to-path=/backup neo4j
              aws s3 cp /backup/neo4j.dump s3://your-backup-bucket/$(date +%Y%m%d)/
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir: {}
          restartPolicy: OnFailure
```

## Monitoring and Logging

### Health Checks

The application provides comprehensive health checks:

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed system status
curl http://localhost:8000/api/v1/health/detailed
```

### Metrics

Prometheus metrics are available at `/metrics`:

- `codeanalysis_repositories_total`: Total repositories analyzed
- `codeanalysis_embeddings_generated_total`: Total embeddings generated
- `codeanalysis_analysis_duration_seconds`: Analysis duration histogram
- `codeanalysis_gpu_memory_usage_bytes`: GPU memory usage
- `codeanalysis_agent_execution_time_seconds`: Agent execution time

### Logs

Structured JSON logs are output to stdout:

```bash
# View application logs
kubectl logs -f deployment/codeanalysis-backend -n codeanalysis

# Search logs with jq
kubectl logs deployment/codeanalysis-backend -n codeanalysis | jq '.level="ERROR"'
```

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check NVIDIA drivers
   kubectl exec -it pod-name -- nvidia-smi
   
   # Verify device plugin
   kubectl get nodes -o json | jq '.items[].status.capacity'
   ```

2. **Neo4j Connection Issues**
   ```bash
   # Check Neo4j status
   kubectl logs deployment/neo4j -n codeanalysis
   
   # Test connection
   kubectl exec -it deployment/neo4j -n codeanalysis -- cypher-shell -u neo4j -p password "RETURN 1;"
   ```

3. **Out of Memory Errors**
   ```bash
   # Check resource usage
   kubectl top pods -n codeanalysis
   
   # Increase memory limits
   kubectl patch deployment codeanalysis-backend -n codeanalysis -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"16Gi"}}}]}}}}'
   ```

4. **Slow Performance**
   ```bash
   # Check CPU usage
   kubectl top nodes
   
   # Scale up replicas
   kubectl scale deployment codeanalysis-backend --replicas=5 -n codeanalysis
   ```

### Performance Tuning

1. **GPU Optimization**
   - Use mixed precision (FP16) for larger batch sizes
   - Implement gradient checkpointing for memory efficiency
   - Use multiple GPUs with DataParallel

2. **Database Tuning**
   - Create appropriate indices in Neo4j
   - Tune PostgreSQL connection pooling
   - Use Redis clustering for high availability

3. **Network Optimization**
   - Use persistent connections
   - Implement connection pooling
   - Enable HTTP/2 for API endpoints

## Security Considerations

### Network Security

- Use network policies to restrict pod-to-pod communication
- Enable mTLS for service-to-service communication
- Use private subnets for database services

### Authentication & Authorization

- Enable RBAC in Kubernetes
- Use service accounts with minimal permissions
- Implement API key rotation

### Data Protection

- Encrypt data at rest
- Use secrets management (Vault, AWS Secrets Manager)
- Enable audit logging

## Scaling Guidelines

### Horizontal Scaling

- Backend API: Scale based on CPU/memory usage (HPA)
- Workers: Scale based on queue depth
- Database: Use read replicas for read-heavy workloads

### Vertical Scaling

- Increase resource limits gradually
- Monitor resource utilization
- Use node auto-scaling for dynamic workloads

### Auto-scaling Configuration

```yaml
# kubernetes/cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.27.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/codeanalysis-cluster
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

This deployment guide provides comprehensive coverage for all deployment scenarios, from local development to enterprise-scale Kubernetes clusters. Choose the method that best fits your requirements and scale.