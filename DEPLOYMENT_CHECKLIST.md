# NWU Protocol - Deployment Checklist

## Pre-Deployment Requirements

### 1. Environment Configuration ✓

- [x] `.env.example` exists with all required variables
- [x] `.env.production.example` exists for production deployments
- [x] Environment variables properly documented
- [x] Sensitive values use placeholders (not committed to repo)

### 2. Docker Configuration ✓

- [x] `docker-compose.yml` configured for development
- [x] `docker-compose.prod.yml` configured for production
- [x] Dockerfile.backend exists and is functional
- [x] Dockerfile.agent exists and is functional
- [x] All services have health checks
- [x] Volumes properly configured for data persistence
- [x] Networks properly isolated

### 3. Database Setup ✓

- [x] PostgreSQL configured (port 5432)
- [x] MongoDB configured (port 27017)
- [x] Redis configured (port 6379)
- [x] Database migrations ready (Alembic)
- [x] Backup strategy documented

### 4. API Configuration ✓

- [x] Backend API runs on port 8000
- [x] Health check endpoint available at `/health`
- [x] API documentation at `/docs`
- [x] CORS properly configured
- [x] Error handling implemented

### 5. Message Queue ✓

- [x] RabbitMQ configured (ports 5672, 15672)
- [x] Default credentials set
- [x] Management UI accessible
- [x] Queue health checks implemented

### 6. Storage ✓

- [x] IPFS configured (ports 5001, 8080)
- [x] Gateway URL configured
- [x] Volume persistence enabled

### 7. CI/CD ✓

- [x] GitHub Actions workflows configured
- [x] Deploy workflow exists (`.github/workflows/deploy.yml`)
- [x] CI/CD workflow exists
- [x] Automated testing configured
- [x] Quality checks enabled

## Deployment Options

### Option 1: Local Development Deployment

```bash
# Quick start
./deploy.sh

# Or using Make
make deploy

# Or using Docker Compose directly
docker-compose up -d
```

**Status**: ✅ Ready

### Option 2: Production Docker Deployment

```bash
# Setup production environment
cp .env.production.example .env
# Edit .env with production credentials

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl http://localhost:8000/health
```

**Status**: ✅ Ready

**Requirements**:
- Change all default passwords in `.env`
- Generate JWT secret: `openssl rand -hex 32`
- Add OpenAI API key
- Configure blockchain RPC URL
- Set up SSL/TLS certificates
- Configure firewall rules
- Enable monitoring and alerts

### Option 3: Vercel Deployment (API Only)

Configured via `vercel.json`:
- Python 3.11 runtime
- Routes to `app.py`
- Environment variables need to be configured in Vercel dashboard

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Status**: ⚠️ Requires environment variables setup in Vercel dashboard

**Note**: This deploys only the FastAPI application. Full infrastructure (databases, queues) requires separate deployment.

### Option 4: Cloud Platform Deployment

#### AWS ECS/Fargate
- Use `docker-compose.prod.yml` as reference
- Configure RDS for PostgreSQL
- Configure DocumentDB for MongoDB
- Configure ElastiCache for Redis
- Configure Amazon MQ for RabbitMQ

#### Google Cloud Run
- Build container images
- Deploy each service separately
- Configure Cloud SQL, Memorystore, Cloud Pub/Sub

#### Azure Container Instances
- Use Azure Container Registry
- Configure Azure Database for PostgreSQL
- Configure Azure Cosmos DB
- Configure Azure Cache for Redis

**Status**: 📋 Configuration templates available

## Security Checklist

### Production Security Requirements

- [ ] Change all default passwords
- [ ] Use strong JWT secret (64+ character hex string)
- [ ] Enable SSL/TLS for all services
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Set up monitoring and alerts
- [ ] Enable log rotation
- [ ] Configure backup strategy
- [ ] Review and adjust resource limits
- [ ] Implement rate limiting on API
- [ ] Configure proper access controls
- [ ] Audit smart contracts before mainnet deployment
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)

### Environment Variables for Production

**Critical - Must Change**:
```env
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_123!
MONGO_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_456!
REDIS_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_789!
RABBITMQ_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_ABC!
JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_64_CHARACTER_HEX_STRING
```

**Required - Add Your Keys**:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your-private-key-for-contract-deployment
```

## Deployment Verification

### 1. Health Checks

```bash
# Backend API
curl http://localhost:8000/health
# Expected: {"status": "healthy", "service": "nwu-protocol"}

# API Status
curl http://localhost:8000/api/v1/status
# Expected: {"status": "operational", "api_version": "1.0.0", ...}

# RabbitMQ Management
curl http://localhost:15672
# Expected: RabbitMQ Management UI login page
```

### 2. Service Status

```bash
# Check all services
docker-compose ps

# Expected output: All services should show "Up (healthy)"
```

### 3. Database Connectivity

```bash
# PostgreSQL
docker exec nwu-postgres pg_isready -U nwu_user
# Expected: accepting connections

# MongoDB
docker exec nwu-mongodb mongosh --eval "db.adminCommand('ping')"
# Expected: { ok: 1 }

# Redis
docker exec nwu-redis redis-cli ping
# Expected: PONG
```

### 4. API Documentation

Visit: http://localhost:8000/docs

Expected: Interactive Swagger UI with API endpoints documented

### 5. Logs Verification

```bash
# View all logs
docker-compose logs -f

# Check for errors
docker-compose logs backend | grep -i error
docker-compose logs agent-alpha | grep -i error
```

## Rollback Procedure

### Docker Compose Deployment

```bash
# Stop current deployment
docker-compose down

# Restore from backup (if needed)
docker exec -i nwu-postgres psql -U nwu_user nwu_db < backup.sql

# Revert to previous version
git checkout <previous-commit>

# Redeploy
docker-compose up -d
```

### Vercel Deployment

```bash
# List deployments
vercel ls

# Rollback to previous deployment
vercel rollback
```

## Monitoring and Maintenance

### Log Management

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f agent-alpha

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Database Backups

```bash
# Create backups
make backup

# Manual backup
mkdir -p backups
docker exec nwu-postgres pg_dump -U nwu_user nwu_db > backups/postgres_$(date +%Y%m%d_%H%M%S).sql
docker exec nwu-mongodb mongodump --out backups/mongodb_$(date +%Y%m%d_%H%M%S)
```

### Performance Monitoring

```bash
# Container stats
docker stats

# Service health
make health

# Full validation
make validate
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Backend won't start**
   - Check database connectivity
   - Verify environment variables
   - Check logs: `docker-compose logs backend`

3. **Agent not processing tasks**
   - Check RabbitMQ is running
   - Verify OpenAI API key
   - Check logs: `docker-compose logs agent-alpha`

4. **Database connection issues**
   - Verify database is healthy
   - Check credentials in .env
   - Ensure databases started before backend

## Support

- **Documentation**: See `DEPLOYMENT.md` and `DEPLOY_NOW.md`
- **Scripts**: `deploy.sh`, `setup.sh`, `status.sh`
- **Makefile Commands**: `make help`
- **GitHub Issues**: https://github.com/Garrettc123/nwu-protocol/issues

## Deployment Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Docker Infrastructure | ✅ Ready | Development and production configs |
| Database Setup | ✅ Ready | PostgreSQL, MongoDB, Redis |
| Message Queue | ✅ Ready | RabbitMQ with management UI |
| Storage | ✅ Ready | IPFS configured |
| Backend API | ✅ Ready | FastAPI with docs |
| Agent System | ✅ Ready | Agent-Alpha configured |
| CI/CD | ✅ Ready | GitHub Actions workflows |
| Vercel Config | ⚠️ Partial | Requires env vars setup |
| Production Security | ⚠️ Action Required | Change default passwords |
| Smart Contracts | 📋 Planned | Deployment scripts ready |

## Quick Deployment Commands

```bash
# Full deployment (recommended)
./deploy.sh

# Using Make
make deploy

# Production deployment
make deploy-prod

# Check status
make status

# View logs
make logs

# Run validation
make validate

# Health check
make health
```

---

**Last Updated**: 2026-02-18
**Version**: 1.0.0
**Maintainer**: NWU Protocol Team
