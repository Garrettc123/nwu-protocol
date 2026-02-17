# Production Deployment Guide

## Prerequisites

Before deploying to production, ensure you have:

- [ ] Docker 20.10+ and Docker Compose 2.0+ installed
- [ ] Server with at least 4GB RAM and 20GB disk space
- [ ] Domain name configured (optional but recommended)
- [ ] SSL/TLS certificates (Let's Encrypt recommended)
- [ ] OpenAI API key for AI verification
- [ ] Strong passwords for all services

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
```

### 2. Configure Production Environment

```bash
# Copy production environment template
cp .env.production.example .env

# Generate strong passwords and secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "MONGO_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "RABBITMQ_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Add your OpenAI API key
nano .env  # Add OPENAI_API_KEY=sk-your-key-here
```

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","checks":{"database":true,"ipfs":true,"rabbitmq":true,"redis":true}}
```

## Service URLs (Default)

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Backend API | http://localhost:8000 | N/A |
| API Documentation | http://localhost:8000/docs | N/A |
| RabbitMQ Management | http://localhost:15672 | See .env file |
| PostgreSQL | localhost:5432 | See .env file |
| MongoDB | localhost:27017 | See .env file |
| Redis | localhost:6379 | See .env file |
| IPFS Gateway | http://localhost:8080 | N/A |

## Production Configuration

### Environment Variables

All required environment variables are defined in `.env.production.example`. Copy this file to `.env` and update the following:

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key for AI verification
- `POSTGRES_PASSWORD` - Strong password for PostgreSQL
- `MONGO_PASSWORD` - Strong password for MongoDB
- `REDIS_PASSWORD` - Strong password for Redis
- `RABBITMQ_PASSWORD` - Strong password for RabbitMQ
- `JWT_SECRET_KEY` - Random 64-character hex string

**Optional:**
- `ETHEREUM_RPC_URL` - Blockchain RPC endpoint (for smart contracts)
- `PRIVATE_KEY` - Private key for contract deployment

### Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong JWT secret key
- [ ] Configured firewall rules (allow only necessary ports)
- [ ] Set up SSL/TLS certificates
- [ ] Enabled log rotation
- [ ] Configured backup strategy
- [ ] Set up monitoring and alerts
- [ ] Reviewed and hardened Docker configurations
- [ ] Limited exposed ports
- [ ] Configured rate limiting
- [ ] Set up automatic security updates

### Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow backend API (or proxy through nginx)
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable
```

## SSL/TLS Configuration (with Nginx)

### 1. Install Nginx

```bash
sudo apt-get update
sudo apt-get install nginx certbot python3-certbot-nginx
```

### 2. Configure Nginx

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

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/nwu-protocol /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Get SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

## Database Management

### Backups

Automated backup script:

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/var/backups/nwu-protocol"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec nwu-postgres-prod pg_dump -U nwu_user nwu_db > $BACKUP_DIR/postgres_$DATE.sql

# MongoDB backup
docker exec nwu-mongodb-prod mongodump --out $BACKUP_DIR/mongodb_$DATE

# Compress backups
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*_$DATE*

# Clean up old backups (keep last 7 days)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
```

Add to crontab for daily backups:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### Database Migrations

```bash
# Apply migrations
docker exec nwu-backend-prod alembic upgrade head

# Create new migration
docker exec nwu-backend-prod alembic revision --autogenerate -m "Description"

# Rollback migration
docker exec nwu-backend-prod alembic downgrade -1
```

## Monitoring

### Health Checks

Set up a monitoring service to check these endpoints:

```bash
# Backend health
curl -f http://localhost:8000/health || alert

# RabbitMQ
curl -f http://localhost:15672 || alert

# PostgreSQL
docker exec nwu-postgres-prod pg_isready || alert
```

### Log Monitoring

View logs:

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df
```

## Scaling

### Horizontal Scaling

To add more backend instances, edit `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    replicas: 3
```

Add a load balancer (nginx) in front:

```nginx
upstream backend {
    least_conn;
    server backend:8000;
    server backend-2:8000;
    server backend-3:8000;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### Vertical Scaling

Increase resource limits in `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Verify environment variables
docker-compose -f docker-compose.prod.yml config

# Test database connection
docker exec nwu-postgres-prod pg_isready -U nwu_user
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Clear unused images/volumes
docker system prune -a
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker exec nwu-backend-prod psql -h postgres -U nwu_user -d nwu_db -c "SELECT 1"
```

## Updating the Application

### Zero-Downtime Update

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.prod.yml up -d --no-deps agent-alpha

# Verify health
curl http://localhost:8000/health
```

## Disaster Recovery

### Backup Strategy

1. **Database backups** - Daily automated backups
2. **Volume backups** - Weekly snapshots of Docker volumes
3. **Configuration backups** - Version control for all configs

### Recovery Process

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore PostgreSQL
docker exec -i nwu-postgres-prod psql -U nwu_user nwu_db < backup.sql

# Restore MongoDB
docker exec nwu-mongodb-prod mongorestore /backup/mongodb_backup

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Performance Optimization

### Database Optimization

```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Redis Configuration

```bash
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### IPFS Optimization

```bash
# Increase storage limit
docker exec nwu-ipfs-prod ipfs config Datastore.StorageMax 50GB
```

## Maintenance

### Regular Tasks

**Daily:**
- Check logs for errors
- Verify health checks
- Monitor resource usage

**Weekly:**
- Review security alerts
- Check backup integrity
- Update dependencies

**Monthly:**
- Security audit
- Performance review
- Capacity planning

### System Updates

```bash
# Update Docker images
docker-compose -f docker-compose.prod.yml pull

# Update application
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

## Support

For production issues:

1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Health check: `curl http://localhost:8000/health`
3. GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
4. Documentation: See DEPLOYMENT.md and README.md

## Production Deployment Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Strong passwords set for all services
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Backups configured and tested
- [ ] Monitoring and alerts set up
- [ ] Log rotation configured
- [ ] Documentation reviewed
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Domain name configured
- [ ] DNS records updated
- [ ] Health checks passing
- [ ] API documentation accessible
- [ ] Smart contracts deployed (if applicable)

## License

MIT
