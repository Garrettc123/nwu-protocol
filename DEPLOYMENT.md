# Deployment Guide for NWU Protocol

This guide provides step-by-step instructions for deploying the NWU Protocol to production.

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ and npm
- Python 3.11+
- MetaMask or compatible Web3 wallet
- OpenAI API key (for AI verification)
- Infura or Alchemy account (for blockchain interaction)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
# OpenAI API Key (Required for AI verification)
OPENAI_API_KEY=sk-your-openai-api-key

# Blockchain Configuration
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your-private-key-for-deployment

# JWT Secret (Change in production)
JWT_SECRET_KEY=your-secure-random-secret-key

# Database Credentials (Change in production)
POSTGRES_PASSWORD=your-secure-password
MONGODB_PASSWORD=your-secure-password
```

### 3. Frontend Environment

Create `.env.local` in the frontend directory:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit with your backend API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Local Development

### Using Docker Compose (Recommended)

Start all services:

```bash
docker-compose up -d
```

This will start:

- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Redis (port 6379)
- RabbitMQ (port 5672, Management UI: 15672)
- IPFS (port 5001, Gateway: 8080)
- Backend API (port 8000)
- Agent-Alpha (background service)

### Manual Setup

#### Backend API

```bash
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Agent-Alpha

```bash
cd agent-alpha
pip install -r requirements.txt

# Start the agent
python -m app.main
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Smart Contracts

```bash
cd contracts
npm install

# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy to localhost
npx hardhat node  # In one terminal
npx hardhat run scripts/deploy.js --network localhost  # In another

# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia
```

## Production Deployment

### 1. Build Docker Images

```bash
# Build backend
docker build -f Dockerfile.backend -t nwu-backend:latest .

# Build agent
docker build -f Dockerfile.agent -t nwu-agent:latest .
```

### 2. Deploy Smart Contracts to Mainnet

```bash
cd contracts

# Verify environment variables
echo $ETHEREUM_RPC_URL
echo $PRIVATE_KEY

# Deploy to mainnet (be careful!)
npx hardhat run scripts/deploy.js --network mainnet

# Save contract addresses
# Update backend and frontend with deployed addresses
```

### 3. Configure Production Environment

Update `.env` for production:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:password@production-db:5432/nwu_db
REDIS_URL=redis://production-redis:6379
# ... other production settings
```

### 4. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f agent-alpha
```

### 5. Frontend Deployment (Vercel)

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Or use the Vercel dashboard:

1. Connect your GitHub repository
2. Configure environment variables
3. Deploy

## Database Migrations

### Create a New Migration

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```

## Health Checks

### Backend API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "nwu-protocol-backend",
  "version": "1.0.0",
  "checks": {
    "database": true,
    "ipfs": true,
    "rabbitmq": true,
    "redis": true
  }
}
```

### RabbitMQ Management UI

Visit: http://localhost:15672

- Username: guest
- Password: guest

### API Documentation

Visit: http://localhost:8000/docs

## Monitoring

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

### Service Status

```bash
docker-compose ps
```

## Troubleshooting

### Backend Won't Start

1. Check database connection:

   ```bash
   docker-compose logs postgres
   ```

2. Check if port 8000 is available:

   ```bash
   lsof -i :8000
   ```

3. Verify environment variables:
   ```bash
   docker-compose config
   ```

### Agent Not Processing Tasks

1. Check RabbitMQ:

   ```bash
   docker-compose logs rabbitmq
   ```

2. Verify OpenAI API key is set
3. Check agent logs:
   ```bash
   docker-compose logs agent-alpha
   ```

### Frontend Can't Connect to Backend

1. Verify NEXT_PUBLIC_API_URL in frontend/.env.local
2. Check CORS settings in backend/app/main.py
3. Ensure backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

### Smart Contract Deployment Fails

1. Verify you have enough ETH for gas
2. Check RPC URL is correct
3. Verify private key format
4. Try with a higher gas price:
   ```bash
   npx hardhat run scripts/deploy.js --network sepolia --verbose
   ```

## Security Considerations

### Production Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT secret key
- [ ] Enable SSL/TLS for all services
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Enable rate limiting on API
- [ ] Implement proper access controls
- [ ] Regular backups of database
- [ ] Audit smart contracts before mainnet deployment

### Secrets Management

Never commit secrets to git. Use:

- Environment variables
- Docker secrets
- AWS Secrets Manager / Azure Key Vault
- HashiCorp Vault

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U nwu_user nwu_db > backup.sql

# MongoDB
docker-compose exec mongodb mongodump --out /backup
```

### Restore Database

```bash
# PostgreSQL
docker-compose exec -T postgres psql -U nwu_user nwu_db < backup.sql

# MongoDB
docker-compose exec mongodb mongorestore /backup
```

## Scaling

### Horizontal Scaling

Add more backend instances:

```yaml
backend:
  deploy:
    replicas: 3
  # ... rest of config
```

Add load balancer (nginx):

```yaml
nginx:
  image: nginx:alpine
  ports:
    - '80:80'
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - backend
```

### Database Scaling

Consider:

- Read replicas for PostgreSQL
- MongoDB sharding
- Redis cluster
- Connection pooling

## Support

For issues and questions:

- GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
- Documentation: See README.md
- API Docs: http://localhost:8000/docs

## License

MIT
