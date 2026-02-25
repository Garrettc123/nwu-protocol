# 🚀 NWU Protocol - 3-Step Quick Deployment

## The Fastest Way to Deploy

### Step 1: Clone and Setup (30 seconds)

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
cp .env.example .env
```

### Step 2: Deploy (1 command)

```bash
./deploy.sh
```

That's it! The deployment script handles everything:
- ✅ Checks prerequisites (Docker, Docker Compose)
- ✅ Builds Docker images
- ✅ Starts all 8 services
- ✅ Runs database migrations
- ✅ Performs health checks
- ✅ Shows you all service URLs

### Step 3: Verify (10 seconds)

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "nwu-protocol"}
```

## What Gets Deployed?

### 8 Services Running

1. **Backend API** (Port 8000)
   - FastAPI application
   - REST API endpoints
   - Interactive docs at `/docs`

2. **Agent-Alpha** (Background)
   - AI verification agent
   - LangChain integration
   - Automated processing

3. **PostgreSQL** (Port 5432)
   - Primary database
   - User data, contributions

4. **MongoDB** (Port 27017)
   - Document storage
   - Metadata, logs

5. **Redis** (Port 6379)
   - Caching layer
   - Session management

6. **RabbitMQ** (Ports 5672, 15672)
   - Message queue
   - Management UI available

7. **IPFS** (Ports 5001, 8080)
   - Decentralized storage
   - Content addressing

8. **Network & Volumes**
   - Isolated network
   - Persistent data volumes

## Access Your Services

After deployment:

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| RabbitMQ UI | http://localhost:15672 | guest/guest |
| IPFS Gateway | http://localhost:8080 | - |

## Alternative Deployment Methods

### Using Make

```bash
make deploy
```

### Using Docker Compose Directly

```bash
docker-compose up -d
```

### Production Deployment

```bash
cp .env.production.example .env
# Edit .env with production credentials
docker-compose -f docker-compose.prod.yml up -d
```

## Useful Commands

```bash
# Check status
make status

# View logs
make logs

# Stop services
make stop

# Restart services
make restart

# Full validation
make validate

# Health check
make health
```

## Troubleshooting

### Docker not installed?

**Ubuntu/Debian**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**macOS**:
```bash
# Install Docker Desktop from:
# https://www.docker.com/products/docker-desktop
```

### Port already in use?

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Services not starting?

```bash
# Check logs
docker-compose logs backend

# Check all services
docker-compose ps

# Restart specific service
docker-compose restart backend
```

### Need to reset everything?

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Redeploy
./deploy.sh
```

## Next Steps

After deployment:

1. **Configure OpenAI API Key** (for AI features)
   ```bash
   # Edit .env
   nano .env
   # Add: OPENAI_API_KEY=sk-your-key-here

   # Restart services
   docker-compose restart backend agent-alpha
   ```

2. **Test the API**
   ```bash
   # Check health
   curl http://localhost:8000/health

   # View API docs
   open http://localhost:8000/docs
   ```

3. **Start Frontend** (optional)
   ```bash
   cd frontend
   npm install
   npm run dev
   # Visit http://localhost:3000
   ```

4. **Deploy Smart Contracts** (optional)
   ```bash
   cd contracts
   npm install
   npx hardhat compile
   npx hardhat test
   ```

## Production Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate strong JWT secret: `openssl rand -hex 32`
- [ ] Add real OpenAI API key
- [ ] Configure blockchain RPC URL
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable monitoring and alerts
- [ ] Configure backup strategy
- [ ] Review security settings

See `DEPLOYMENT_CHECKLIST.md` for complete production guide.

## Need Help?

- 📖 **Full Documentation**: `DEPLOYMENT.md`
- 📋 **Detailed Checklist**: `DEPLOYMENT_CHECKLIST.md`
- 🐛 **Issues**: https://github.com/Garrettc123/nwu-protocol/issues
- 📊 **Status**: `DEPLOYMENT_STATUS.md`

## Deployment Time

- **Setup**: 30 seconds
- **First Build**: 5-10 minutes (downloads images, builds containers)
- **Subsequent Deploys**: 1-2 minutes (uses cached images)
- **Verification**: 10 seconds

**Total Time for First Deployment**: ~10 minutes
**Total Time for Updates**: ~2 minutes

---

**Made simple. Made fast. Made right.**

NWU Protocol Team
