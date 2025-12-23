# 🚀 NWU Protocol - Quickstart Guide

## Prerequisites

- Docker & Docker Compose installed
- Git
- OpenAI API key (for AI agents)
- 8GB RAM minimum
- 20GB disk space

---

## ⚡ Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required for AI agents
OPENAI_API_KEY=sk-your-key-here
HUGGINGFACE_TOKEN=hf_your-token-here

# Optional: Blockchain (for production)
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_private_key_here
```

### 3. Start All Services

```bash
docker-compose up -d
```

This starts:
- 📦 **PostgreSQL** (port 5432) - Database
- 🔴 **Redis** (port 6379) - Cache
- 🌐 **IPFS** (ports 4001, 5001, 8080) - Decentralized storage
- 🐇 **RabbitMQ** (ports 5672, 15672) - Message queue
- 🔌 **Backend API** (port 8000) - REST API
- 🤖 **Agent-Alpha** - AI verification agent
- 🎨 **Frontend** (port 3000) - Next.js UI
- 🌀 **NGINX** (ports 80, 443) - Reverse proxy

### 4. Verify Services

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Check specific service
docker-compose logs backend
```

### 5. Access Applications

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main UI |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **RabbitMQ UI** | http://localhost:15672 | Queue management |
| **IPFS Gateway** | http://localhost:8080 | IPFS access |
| **IPFS API** | http://localhost:5001 | IPFS API |

**Default Credentials:**
- RabbitMQ: `nwu_admin` / `nwu_rabbitmq_pass`
- PostgreSQL: `nwu_user` / `nwu_password`

---

## 🏗️ Development Workflow

### Create Backend API Structure

```bash
mkdir -p backend/app
touch backend/app/__init__.py
touch backend/app/main.py
```

**backend/app/main.py:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NWU Protocol API",
    description="Decentralized AI Verification Platform",
    version="1.0.0-alpha"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "NWU Protocol API",
        "version": "1.0.0-alpha",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "ipfs": "connected",
        "rabbitmq": "connected"
    }

@app.post("/contributions")
def create_contribution():
    return {"message": "Contribution endpoint - coming soon"}

@app.get("/contributions/{id}")
def get_contribution(id: str):
    return {"message": f"Get contribution {id} - coming soon"}
```

### Rebuild and Restart

```bash
# Rebuild specific service
docker-compose build backend

# Restart service
docker-compose restart backend

# Or rebuild and restart everything
docker-compose down
docker-compose up -d --build
```

---

## 🧪 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/

# Test with httpie (prettier)
http GET localhost:8000/health
```

### Test IPFS

```bash
# Add file to IPFS
echo "Hello NWU Protocol" | curl -X POST -F file=@- http://localhost:5001/api/v0/add

# Get file from IPFS (use hash from above)
curl "http://localhost:8080/ipfs/YOUR_HASH_HERE"
```

### Test RabbitMQ

Visit http://localhost:15672 and login with:
- Username: `nwu_admin`
- Password: `nwu_rabbitmq_pass`

---

## 📊 Monitoring

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f agent-alpha
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U nwu_user -d nwu_protocol

# List tables
\dt

# Exit
\q
```

### Redis Access

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Test commands
PING
KEYS *
EXIT
```

---

## 🛠️ Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
sudo lsof -i :8000
sudo lsof -i :3000
sudo lsof -i :5432

# Free up ports or change in docker-compose.yml
```

### Database Connection Issues

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d
```

### IPFS Not Responding

```bash
# Restart IPFS
docker-compose restart ipfs

# Check IPFS status
docker-compose exec ipfs ipfs id
```

### Agent-Alpha Crashes

```bash
# Check logs
docker-compose logs agent-alpha

# Verify OpenAI API key in .env
cat .env | grep OPENAI

# Restart agent
docker-compose restart agent-alpha
```

### Reset Everything

```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d --build
```

---

## 💾 Data Persistence

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep nwu

# Inspect volume
docker volume inspect nwu-protocol_postgres_data

# Backup database
docker-compose exec postgres pg_dump -U nwu_user nwu_protocol > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U nwu_user nwu_protocol
```

---

## 🚀 Next Steps

1. **Implement Backend API:**
   - Contribution upload endpoint
   - IPFS integration
   - Database models
   - JWT authentication

2. **Build Agent-Alpha:**
   - LangChain integration
   - Code quality analysis
   - RabbitMQ consumer
   - Verification logic

3. **Create Frontend:**
   - File upload UI
   - Web3 wallet connection
   - Real-time status updates
   - Dashboard

4. **Add Smart Contracts:**
   - Reward distribution
   - Verification results
   - Token economics

---

## 📚 Resources

- [Architecture Overview](README.md)
- [Phase 1 Roadmap](https://github.com/Garrettc123/nwu-protocol/issues/1)
- [API Documentation](http://localhost:8000/docs)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## ❓ Get Help

- 🐛 Open an issue: [GitHub Issues](https://github.com/Garrettc123/nwu-protocol/issues)
- 💬 Join discussions: [GitHub Discussions](https://github.com/Garrettc123/nwu-protocol/discussions)
- 📧 Email: garrett@example.com

---

<div align="center">
  <b>⚡ Happy Building! ⚡</b>
</div>
