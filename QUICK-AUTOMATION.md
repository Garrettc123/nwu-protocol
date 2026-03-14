# 🎯 Complete Automation - Quick Reference

## One-Command Solutions

### 🚀 Start Everything

```bash
./auto-start.sh
```

Configures, checks, builds, and starts the entire system automatically.

### 🔧 Fix Issues

```bash
./troubleshoot.sh
```

Diagnoses and automatically fixes common problems.

### 🏥 Monitor Health

```bash
./health-monitor.sh
```

Live dashboard showing all service status.

### 🔄 Recover Services

```bash
./auto-recovery.sh
```

Automatically restarts failed services.

## Complete Automation Suite

| Script               | Purpose                    | Auto-Fixes                                 |
| -------------------- | -------------------------- | ------------------------------------------ |
| `auto-configure.sh`  | Configure all environments | ✅ Creates .env files, generates secrets   |
| `auto-start.sh`      | Start everything           | ✅ Configures, builds, starts all services |
| `troubleshoot.sh`    | Diagnose & fix issues      | ✅ 10-point diagnostic, auto-repairs       |
| `auto-recovery.sh`   | Recover failed services    | ✅ Restarts unhealthy containers           |
| `preflight-check.sh` | Pre-flight checks          | ⚠️ Warns about issues                      |
| `health-monitor.sh`  | Live monitoring            | 📊 Real-time dashboard                     |

## What Gets Automated

✅ **Environment Configuration**

- Auto-generated secure JWT secrets
- All .env files created automatically
- Safe defaults for all services
- .gitignore updates

✅ **System Checks**

- Docker daemon status
- Port availability (3000, 5432, 6379, 8000, etc.)
- Disk space verification
- Dependency checks

✅ **Service Management**

- Docker container orchestration
- Health checks for all services
- Database connectivity
- API endpoint verification

✅ **Problem Resolution**

- Auto-recovery of failed services
- Dependency installation
- Permission fixes
- Container restarts

## Quick Start Scenarios

### First Time Setup

```bash
./auto-start.sh
# That's it! Everything is configured and running
```

### Something Broken?

```bash
./troubleshoot.sh
# Auto-diagnoses and fixes issues
```

### Want to Monitor?

```bash
./health-monitor.sh
# Live dashboard updates every 5 seconds
```

### Need to Restart?

```bash
./restart.sh
# Or use auto-recovery for failed services
./auto-recovery.sh
```

## Service Access (After Start)

| Service        | URL                          | Credentials        |
| -------------- | ---------------------------- | ------------------ |
| Frontend       | http://localhost:3000        | -                  |
| Backend API    | http://localhost:8000        | -                  |
| API Docs       | http://localhost:8000/docs   | -                  |
| Health Check   | http://localhost:8000/health | -                  |
| RabbitMQ Admin | http://localhost:15672       | guest/guest        |
| PostgreSQL     | localhost:5432               | nwu_user/rocket69! |
| MongoDB        | localhost:27017              | admin/rocket69!    |
| Redis          | localhost:6379               | -                  |
| IPFS           | http://localhost:5001        | -                  |

## Common Issues - Auto-Fixed

✅ Missing .env files → Auto-created with secure defaults
✅ Missing dependencies → Auto-installed
✅ Wrong permissions → Auto-corrected
✅ Unhealthy services → Auto-restarted
✅ Port conflicts → Detected and reported
✅ Docker not running → Clear error message
✅ Low disk space → Warning with cleanup suggestion

## Advanced Usage

### Custom Configuration

```bash
# Auto-configure creates the files, then edit if needed
./auto-configure.sh
nano .env
```

### Selective Service Control

```bash
# Restart specific service
docker-compose restart backend

# View specific logs
make logs-backend
```

### Development Workflow

```bash
# 1. Start system
./auto-start.sh

# 2. Monitor (optional)
./health-monitor.sh &

# 3. Develop...

# 4. Check health
curl http://localhost:8000/health

# 5. View logs if needed
./logs.sh
```

## CI/CD Integration

The automation works in CI/CD:

```yaml
- name: Auto-configure and start
  run: |
    ./auto-configure.sh
    ./auto-start.sh

- name: Check health
  run: ./troubleshoot.sh
```

## Documentation

- **AUTOMATION.md** - Complete automation guide
- **README.md** - Main project README
- **QUICKSTART.md** - Quick start guide
- **SETUP_GUIDE.md** - Detailed setup

## Support

If automation doesn't fix an issue:

1. Check logs: `./logs.sh`
2. View status: `./status.sh`
3. Read docs: `AUTOMATION.md`
4. Manual reset: `./stop.sh && ./clean.sh && ./auto-start.sh`

---

**Everything is automated. Just run the scripts!** 🚀
