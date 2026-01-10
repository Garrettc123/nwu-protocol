# 🚀 NWU Protocol - Quick Deployment Guide

## One-Command Deployment

```bash
./deploy.sh
```

That's it! The deployment script will handle everything automatically.

## What the Deployment Script Does

1. ✅ Checks all prerequisites (Docker, Docker Compose)
2. ✅ Sets up environment variables from `.env.example`
3. ✅ Builds Docker images for backend and agent
4. ✅ Starts infrastructure services (PostgreSQL, MongoDB, Redis, RabbitMQ, IPFS)
5. ✅ Waits for all services to be healthy
6. ✅ Starts application services (Backend API, Agent-Alpha)
7. ✅ Runs database migrations automatically
8. ✅ Sets up frontend dependencies
9. ✅ Performs comprehensive health checks
10. ✅ Displays all service URLs and useful commands

## Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Node.js** (version 18+, for frontend)
- **npm** (for frontend dependencies)

### Install Prerequisites

**Ubuntu/Debian:**
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop

# Node.js via Homebrew
brew install node
```

## Step-by-Step Manual Deployment

If you prefer manual control:

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Or start step by step:
docker-compose up -d postgres mongodb redis rabbitmq ipfs
docker-compose up -d backend agent-alpha
```

### 3. Check Health

```bash
# View all services status
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## Production Deployment

For production deployment with enhanced security:

```bash
# Copy production environment template
cp .env.production.example .env

# Edit and add strong passwords and real API keys
nano .env

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong JWT secret: `openssl rand -hex 32`
- [ ] Add real OpenAI API key
- [ ] Configure blockchain RPC URL (Infura/Alchemy)
- [ ] Set up SSL/TLS certificates (use nginx or Traefik)
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Configure backup strategy for databases
- [ ] Review and adjust Docker resource limits

## Service URLs

After deployment, access these URLs:

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| Frontend | http://localhost:3000 | - |
| RabbitMQ Management | http://localhost:15672 | guest/guest |
| IPFS Gateway | http://localhost:8080 | - |
| PostgreSQL | localhost:5432 | nwu_user/rocket69! |
| MongoDB | localhost:27017 | admin/rocket69! |
| Redis | localhost:6379 | - |

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f agent-alpha

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### Database Operations
```bash
# Access PostgreSQL
docker exec -it nwu-postgres psql -U nwu_user -d nwu_db

# Access MongoDB
docker exec -it nwu-mongodb mongosh -u admin -p rocket69!

# Backup PostgreSQL
docker exec nwu-postgres pg_dump -U nwu_user nwu_db > backup.sql

# Restore PostgreSQL
docker exec -i nwu-postgres psql -U nwu_user nwu_db < backup.sql
```

### Run Migrations
```bash
# Apply migrations
docker exec nwu-backend alembic upgrade head

# Create new migration
docker exec nwu-backend alembic revision --autogenerate -m "Description"

# Rollback one version
docker exec nwu-backend alembic downgrade -1
```

## Troubleshooting

### Backend Won't Start

1. Check logs: `docker-compose logs backend`
2. Verify database is running: `docker-compose ps postgres`
3. Check environment variables: `docker-compose config`

### Agent Not Processing Tasks

1. Check logs: `docker-compose logs agent-alpha`
2. Verify RabbitMQ is running: `curl http://localhost:15672`
3. Check OpenAI API key is set in `.env`

### Frontend Can't Connect

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `frontend/.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Check CORS settings in backend

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

## Deploy Smart Contracts

```bash
cd contracts

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Test contracts
npx hardhat test

# Deploy to localhost (for testing)
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost

# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia

# Verify on Etherscan
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```

## Monitoring

### Health Check Endpoint

```bash
# Check system health
curl http://localhost:8000/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": true,
#     "ipfs": true,
#     "rabbitmq": true,
#     "redis": true
#   }
# }
```

### Service Metrics

```bash
# Container stats
docker stats

# Specific container
docker stats nwu-backend
```

## Scaling

### Add More Backend Instances

```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
```

### Add Load Balancer

Use nginx or Traefik to distribute load across multiple backend instances.

## Support

- **Documentation**: See `DEPLOYMENT.md` for detailed guide
- **API Reference**: See `API_REFERENCE.md`
- **Issues**: https://github.com/Garrettc123/nwu-protocol/issues

## Next Steps

1. ✅ Deploy the system
2. 📝 Create a user account via frontend
3. 🔐 Connect your MetaMask wallet
4. 📤 Upload your first contribution
5. 🤖 Watch Agent-Alpha verify it
6. 💰 Earn NWU tokens based on quality

---

**Made with ❤️ for decentralized intelligence and verified truth**
