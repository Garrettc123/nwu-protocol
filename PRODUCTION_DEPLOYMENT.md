# 🏭 NWU Protocol - Production Deployment Guide

## Production Deployment Overview

This guide covers deploying NWU Protocol to production environments with enterprise-grade security, reliability, and scalability.

## Prerequisites

### Infrastructure Requirements

- **Compute**: Docker-capable host (2+ CPU cores, 4GB+ RAM recommended)
- **Storage**: 20GB+ available disk space
- **Network**: Static IP address, DNS configured
- **SSL/TLS**: Valid SSL certificate (Let's Encrypt recommended)
- **Monitoring**: Logging and monitoring solution (optional but recommended)

### Required Accounts and Keys

- **OpenAI API Key**: For AI verification features
- **Blockchain RPC**: Infura, Alchemy, or self-hosted Ethereum node
- **Email Service**: For notifications (optional)
- **Monitoring Service**: DataDog, New Relic, or similar (optional)

## Security First Approach

### 1. Generate Secure Credentials

```bash
# Generate JWT secret (64 character hex string)
openssl rand -hex 32
# Example output: 8f7a9d2c1e4b3f6a8d9c7e5f3a1b2c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b

# Generate database passwords (32 character random)
openssl rand -base64 32
# Example output: xK9mNvL2wQp8YzRjFtHgBsA6dCeWqXkI

# Generate additional secrets as needed
openssl rand -hex 16  # For shorter secrets
```

### 2. Create Production Environment File

```bash
cp .env.production.example .env
```

Edit `.env` with your secure credentials:

```env
# Environment
ENVIRONMENT=production
DEBUG=false
NODE_ENV=production

# PostgreSQL Database
POSTGRES_USER=nwu_user
POSTGRES_PASSWORD=<STRONG_PASSWORD_FROM_STEP_1>
POSTGRES_DB=nwu_db
DATABASE_URL=postgresql://nwu_user:<PASSWORD>@postgres:5432/nwu_db

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=<STRONG_PASSWORD_FROM_STEP_1>
MONGO_URL=mongodb://admin:<PASSWORD>@mongodb:27017/nwu_db?authSource=admin

# Redis
REDIS_PASSWORD=<STRONG_PASSWORD_FROM_STEP_1>
REDIS_URL=redis://:<PASSWORD>@redis:6379

# RabbitMQ
RABBITMQ_USER=nwu_admin
RABBITMQ_PASSWORD=<STRONG_PASSWORD_FROM_STEP_1>
RABBITMQ_URL=amqp://nwu_admin:<PASSWORD>@rabbitmq:5672

# JWT Authentication
JWT_SECRET_KEY=<64_CHAR_HEX_FROM_STEP_1>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI API (Required for AI features)
OPENAI_API_KEY=sk-your-real-openai-api-key-here

# Blockchain
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
PRIVATE_KEY=your-private-key-for-contract-deployment

# IPFS
IPFS_HOST=ipfs
IPFS_PORT=5001
IPFS_API_URL=http://ipfs:5001
IPFS_GATEWAY_URL=https://gateway.ipfs.io

# Backend
BACKEND_URL=http://backend:8000

# Ports
API_PORT=8000
DASHBOARD_PORT=3000
```

### 3. Secure the Environment File

```bash
# Set strict permissions
chmod 600 .env

# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Never commit .env to version control
git status  # Verify .env is not staged
```

## Production Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Step 1: Build Production Images

```bash
# Build backend image
docker build -f Dockerfile.backend -t nwu-protocol/backend:latest -t nwu-protocol/backend:1.0.0 .

# Build agent image
docker build -f Dockerfile.agent -t nwu-protocol/agent:latest -t nwu-protocol/agent:1.0.0 .

# Verify images
docker images | grep nwu-protocol
```

#### Step 2: Deploy with Production Configuration

```bash
# Start all services with production config
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
sleep 30

# Check status
docker-compose -f docker-compose.prod.yml ps
```

#### Step 3: Verify Deployment

```bash
# Health check
curl -f http://localhost:8000/health || echo "Health check failed"

# Check API status
curl http://localhost:8000/api/v1/status

# Verify all containers are running
docker ps | grep nwu
```

#### Step 4: Run Database Migrations

```bash
# Apply latest migrations
docker exec nwu-backend-prod alembic upgrade head

# Verify migration
docker exec nwu-backend-prod alembic current
```

### Method 2: Cloud Platform Deployment

#### AWS ECS/Fargate

1. **Push Images to ECR**

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag nwu-protocol/backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/nwu-backend:latest
docker tag nwu-protocol/agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/nwu-agent:latest

# Push images
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/nwu-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/nwu-agent:latest
```

2. **Configure Managed Services**

- **RDS**: PostgreSQL database
- **DocumentDB**: MongoDB-compatible database
- **ElastiCache**: Redis cache
- **Amazon MQ**: RabbitMQ message broker
- **EFS**: Persistent storage for IPFS

3. **Deploy ECS Tasks**

Create task definitions from `docker-compose.prod.yml` and deploy to ECS.

#### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/nwu-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/nwu-agent

# Deploy to Cloud Run
gcloud run deploy nwu-backend \
  --image gcr.io/PROJECT_ID/nwu-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# Push to Azure Container Registry
az acr build --registry <registry-name> --image nwu-backend:latest .

# Deploy to ACI
az container create \
  --resource-group nwu-protocol \
  --name nwu-backend \
  --image <registry-name>.azurecr.io/nwu-backend:latest \
  --ports 8000
```

### Method 3: Kubernetes Deployment

#### Create Kubernetes Manifests

Convert `docker-compose.prod.yml` to Kubernetes manifests using kompose:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# Convert docker-compose to k8s manifests
kompose convert -f docker-compose.prod.yml

# Apply to cluster
kubectl apply -f .
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

1. **Install Nginx and Certbot**

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

2. **Configure Nginx**

Create `/etc/nginx/sites-available/nwu-protocol`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Enable Site and Get Certificate**

```bash
sudo ln -s /etc/nginx/sites-available/nwu-protocol /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

### Using Traefik (Alternative)

Add to `docker-compose.prod.yml`:

```yaml
traefik:
  image: traefik:v2.10
  command:
    - "--providers.docker=true"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
    - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - "/var/run/docker.sock:/var/run/docker.sock:ro"
    - "./letsencrypt:/letsencrypt"
```

## Firewall Configuration

### UFW (Ubuntu)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow only local access to databases
sudo ufw deny 5432/tcp
sudo ufw deny 27017/tcp
sudo ufw deny 6379/tcp

# Check status
sudo ufw status
```

### iptables

```bash
# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Drop everything else
iptables -P INPUT DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

## Monitoring and Logging

### Docker Logging

Configure log rotation in `docker-compose.prod.yml` (already included):

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor container stats
docker stats

# Monitor logs in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

### External Monitoring (Optional)

#### Prometheus + Grafana

```yaml
# Add to docker-compose.prod.yml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  depends_on:
    - prometheus
```

## Backup Strategy

### Automated Backups

Create `/etc/cron.daily/nwu-backup`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/nwu-protocol"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# PostgreSQL backup
docker exec nwu-postgres-prod pg_dump -U nwu_user nwu_db | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# MongoDB backup
docker exec nwu-mongodb-prod mongodump --archive | gzip > "$BACKUP_DIR/mongodb_$DATE.archive.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete

# Upload to S3 (optional)
# aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/nwu-protocol/
```

```bash
chmod +x /etc/cron.daily/nwu-backup
```

## Scaling

### Horizontal Scaling

Update `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    replicas: 3
    update_config:
      parallelism: 1
      delay: 10s
    restart_policy:
      condition: on-failure
```

### Load Balancer

Add Nginx as load balancer:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
  depends_on:
    - backend
```

## Health Checks and Monitoring

### Automated Health Checks

Create `/etc/cron.d/nwu-health-check`:

```bash
*/5 * * * * root curl -f http://localhost:8000/health || systemctl restart docker-compose
```

### Uptime Monitoring

Use services like:
- **UptimeRobot**: Free tier available
- **Pingdom**: Comprehensive monitoring
- **StatusCake**: Multiple check locations
- **Freshping**: Free for up to 50 checks

## Disaster Recovery

### Backup Verification

```bash
# Test PostgreSQL restore
gunzip < backup.sql.gz | docker exec -i nwu-postgres-prod psql -U nwu_user -d nwu_db_test

# Test MongoDB restore
gunzip < backup.archive.gz | docker exec -i nwu-mongodb-prod mongorestore --archive
```

### Recovery Procedure

1. Stop current deployment
2. Restore databases from backup
3. Redeploy application
4. Verify functionality
5. Update DNS if needed

## Performance Optimization

### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### Redis Optimization

```bash
# Add to docker-compose.prod.yml redis command
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### IPFS Optimization

```bash
# Configure IPFS garbage collection
docker exec nwu-ipfs-prod ipfs config --json Datastore.GCPeriod '"1h"'
```

## Production Checklist

- [ ] All default passwords changed
- [ ] JWT secret generated and set
- [ ] OpenAI API key configured
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Monitoring enabled
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Backup restoration tested
- [ ] Health checks configured
- [ ] Load balancer configured (if scaling)
- [ ] DNS configured
- [ ] Email notifications set up
- [ ] Security audit performed
- [ ] Performance testing completed
- [ ] Disaster recovery plan documented

## Post-Deployment Verification

```bash
# 1. Health check
curl -f https://your-domain.com/health

# 2. API documentation
curl https://your-domain.com/docs

# 3. Check all services
docker-compose -f docker-compose.prod.yml ps

# 4. Verify logs are clean
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error

# 5. Test database connections
docker exec nwu-postgres-prod pg_isready -U nwu_user
docker exec nwu-mongodb-prod mongosh --eval "db.adminCommand('ping')"
docker exec nwu-redis-prod redis-cli --pass "$REDIS_PASSWORD" ping

# 6. Performance test
ab -n 1000 -c 10 https://your-domain.com/health
```

## Support and Maintenance

### Regular Maintenance Tasks

- **Daily**: Check logs for errors
- **Weekly**: Review monitoring dashboards
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Security audit and performance review

### Getting Help

- **Documentation**: See `DEPLOYMENT.md` and `DEPLOYMENT_CHECKLIST.md`
- **Issues**: https://github.com/Garrettc123/nwu-protocol/issues
- **Emergency**: Check logs first, then rollback if needed

## Cost Estimation

### Cloud Costs (Approximate Monthly)

**AWS**:
- ECS Fargate (2 tasks): $50-100
- RDS PostgreSQL (db.t3.medium): $50-80
- DocumentDB: $60-100
- ElastiCache: $30-50
- Load Balancer: $20-30
- **Total**: $210-360/month

**Google Cloud**:
- Cloud Run: $30-60
- Cloud SQL: $50-80
- Memorystore: $30-50
- **Total**: $110-190/month

**Azure**:
- Container Instances: $40-80
- PostgreSQL: $50-80
- Cosmos DB: $60-100
- **Total**: $150-260/month

**Self-Hosted VPS** (DigitalOcean/Linode):
- 4GB RAM, 2 CPU: $24/month
- Backup storage: $5/month
- **Total**: $29/month (most economical)

---

**Production Ready. Enterprise Grade. Battle Tested.**

NWU Protocol Team
