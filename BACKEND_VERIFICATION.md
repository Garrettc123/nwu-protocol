# Backend Services Verification Guide

This document describes all the "invisible" backend components and how to verify they're working correctly.

## 🔍 What Gets Verified

The NWU Protocol includes extensive backend validation to ensure ALL invisible components are working:

### 1. Infrastructure Services

- **PostgreSQL Database** - Relational data storage
- **MongoDB** - NoSQL document storage
- **Redis** - Caching and session management
- **RabbitMQ** - Message queue for async processing
- **IPFS** - Decentralized file storage

### 2. Application Services

- **Backend API** - FastAPI application
- **Agent-Alpha** - AI verification service

### 3. API Endpoints

All REST API endpoints are tested:

- Authentication endpoints
- Contribution management
- User management
- Verification endpoints
- Health checks

### 4. Service Connectivity

- Container-to-container networking
- Database connections
- Queue connections
- File storage access

## 🚀 Running Validation

### Automatic Validation

When you deploy with `./deploy.sh`, comprehensive validation runs automatically at the end.

### Manual Validation

Run validation anytime with these commands:

```bash
# Full backend validation (infrastructure + services)
make validate

# API endpoints only
make test-api

# Complete validation (backend + API)
make test-all
```

Or run scripts directly:

```bash
# Comprehensive backend validation
./validate-backend.sh

# API endpoint testing
./test-api-endpoints.sh
```

## ✅ What Gets Tested

### Container Health

- All 7 containers running
- Container health status
- Restart policies working

### PostgreSQL Database

- Database server accepting connections
- Database 'nwu_db' exists
- Tables created (via migrations)
- Read/write operations
- Connection from backend

### MongoDB

- MongoDB server running
- Authentication working
- Database operations
- Connection pooling

### Redis

- Redis server responding
- Write operations (SET)
- Read operations (GET)
- Expiration/TTL
- Session storage

### RabbitMQ

- RabbitMQ service running
- Management API accessible
- Queues created
- Message publishing
- Message consumption

### IPFS

- IPFS daemon running
- API accessible (port 5001)
- Gateway accessible (port 8080)
- File add operations
- File retrieval (cat)
- Content addressing

### Backend API

- Health endpoint responding
- All service connections healthy
- Database connection OK
- IPFS connection OK
- RabbitMQ connection OK
- Redis connection OK
- API documentation accessible
- Root endpoint working
- All API routes registered

### Agent-Alpha

- Container running
- Startup successful
- RabbitMQ connection established
- IPFS connection established
- Queue consumer active
- OpenAI integration (if API key provided)

### Database Migrations

- Alembic migrations applied
- Schema at correct version
- All tables created
- Indexes in place

### Environment Configuration

- .env file exists
- Required variables set
- API keys configured
- Secrets properly set

### Network Connectivity

- Backend → PostgreSQL
- Backend → MongoDB
- Backend → Redis
- Backend → RabbitMQ
- Backend → IPFS
- Agent → Backend
- Agent → RabbitMQ
- Agent → IPFS

## 📊 Test Results

After validation, you'll see a detailed report:

```
╔═══════════════════════════════════════════════════════════════╗
║                     VALIDATION SUMMARY                        ║
╚═══════════════════════════════════════════════════════════════╝

  Tests Passed:    45
  Tests Failed:    0
  Warnings:        2

✓ ALL BACKEND SERVICES ARE WORKING CORRECTLY!
```

### Success Indicators

- ✓ Green checkmarks = Test passed
- ⚠ Yellow warnings = Non-critical issues (like missing OpenAI key)
- ✗ Red X marks = Test failed

## 🔧 Troubleshooting

### If Validation Fails

1. **Check container status:**

   ```bash
   docker-compose ps
   ```

2. **View logs:**

   ```bash
   docker-compose logs [service-name]
   # Examples:
   docker-compose logs backend
   docker-compose logs postgres
   docker-compose logs agent-alpha
   ```

3. **Restart specific service:**

   ```bash
   docker-compose restart [service-name]
   ```

4. **Full restart:**

   ```bash
   docker-compose restart
   ```

5. **Check network connectivity:**
   ```bash
   docker network ls
   docker network inspect nwu-network
   ```

### Common Issues

#### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is ready
docker exec nwu-postgres pg_isready -U nwu_user

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

#### Redis Connection Failed

```bash
# Test Redis directly
docker exec nwu-redis redis-cli ping

# Should return: PONG
```

#### RabbitMQ Not Accessible

```bash
# Check RabbitMQ status
docker exec nwu-rabbitmq rabbitmq-diagnostics ping

# Access management UI
open http://localhost:15672
# Credentials: guest/guest
```

#### IPFS Not Responding

```bash
# Check IPFS daemon
docker exec nwu-ipfs ipfs id

# Test IPFS API
curl http://localhost:5001/api/v0/id
```

#### Backend API Not Responding

```bash
# Check if backend is running
docker-compose ps backend

# View backend logs
docker-compose logs backend --tail=50

# Test health endpoint
curl http://localhost:8000/health | jq
```

#### Agent Not Processing Tasks

```bash
# Check agent logs
docker-compose logs agent-alpha --tail=50

# Verify RabbitMQ connection
docker-compose logs agent-alpha | grep "RabbitMQ"

# Check if OpenAI key is set
docker exec nwu-agent-alpha env | grep OPENAI
```

## 🎯 Validation Coverage

### What's Tested

- ✅ All 7 Docker containers
- ✅ 5 infrastructure services
- ✅ 2 application services
- ✅ 10+ API endpoints
- ✅ Database connectivity
- ✅ Queue messaging
- ✅ File storage
- ✅ Authentication flow
- ✅ Service health
- ✅ Network routing

### What's NOT Tested (Yet)

- Smart contract deployment
- Frontend functionality
- End-to-end workflows
- Load testing
- Security penetration testing

## 📈 Continuous Validation

Run validation regularly:

```bash
# Every hour (cron example)
0 * * * * cd /path/to/nwu-protocol && make validate

# Or use a monitoring script
while true; do
  make health
  sleep 300  # 5 minutes
done
```

## 🔐 Security Checks

Validation includes security checks:

- ✅ Database authentication working
- ✅ Redis password (if set)
- ✅ RabbitMQ credentials
- ✅ HTTPS/TLS (production)
- ✅ JWT token generation
- ✅ API key protection

## 📚 Additional Resources

- **Health Endpoint**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **RabbitMQ Management**: `http://localhost:15672`
- **IPFS Gateway**: `http://localhost:8080`

## 🎉 Success Criteria

Your backend is fully operational when:

- ✅ All validation tests pass
- ✅ No containers in restart loop
- ✅ Health endpoint returns "healthy"
- ✅ All API endpoints respond
- ✅ Database migrations applied
- ✅ Agent processing messages
- ✅ Files can be uploaded to IPFS

---

**Remember**: Backend validation ensures that everything "not visible" (databases, queues, caches, APIs) is working perfectly before users interact with the frontend.
