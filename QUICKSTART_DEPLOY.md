# Deployment Quickstart

This guide provides the fastest path to deploying the NWU Protocol application.

## Prerequisites

- Docker & Docker Compose installed
- 4GB RAM minimum
- 20GB disk space

## Deploy in 3 Steps

### 1. Clone & Configure

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
cp .env.example .env
```

### 2. Deploy

```bash
./deploy.sh
```

OR

```bash
make deploy
```

### 3. Verify

```bash
curl http://localhost:8000/health
```

## Service URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ**: http://localhost:15672 (guest/guest)
- **IPFS**: http://localhost:8080

## Production Deployment

For production deployment with proper security:

```bash
# 1. Configure production environment
cp .env.production.example .env

# 2. Generate strong passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "MONGO_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "RABBITMQ_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 3. Add OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 4. Deploy with production config
docker-compose -f docker-compose.prod.yml up -d
```

## Verification

Run the deployment verification script:

```bash
./verify-deployment.sh
```

## Troubleshooting

**Services not starting?**
```bash
docker-compose logs -f
```

**Port already in use?**
```bash
docker-compose down
sudo lsof -i :8000  # Find process
```

**Need to reset everything?**
```bash
docker-compose down -v
./deploy.sh
```

## Documentation

- **Complete Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Production Guide**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)

## Support

- GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
- Documentation: See README.md
