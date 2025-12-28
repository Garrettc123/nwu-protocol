# 🚀 Easy Start Guide

## The Simplest Way to Get Started

### One Command Setup

```bash
chmod +x setup.sh && ./setup.sh
```

That's it! This single command will:
- ✅ Check your system has Docker installed
- ✅ Create your configuration file
- ✅ Ask for your OpenAI API key (optional)
- ✅ Pull all required images
- ✅ Start all 8 services
- ✅ Verify everything is healthy

### After Setup

**Visit these URLs:**
- 🌐 Frontend: http://localhost:3000
- 🔧 API Docs: http://localhost:8000/docs
- 📊 RabbitMQ: http://localhost:15672 (guest/guest)

### Daily Commands

```bash
./status.sh     # Check if everything is running
./logs.sh       # See what's happening
./apply.sh      # Submit a contribution
./restart.sh    # Restart if needed
./stop.sh       # Stop when done (keeps your data)
./help.sh       # Show all commands
```

### Interactive Menu

```bash
./dev.sh
```

Opens a user-friendly menu with all common tasks.

---

## Not Working?

### Don't have Docker?

**macOS:**
```bash
brew install --cask docker
```

**Windows:**
Download from: https://docs.docker.com/desktop/install/windows-install/

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Port Already in Use?

```bash
# Find what's using port 3000
lsof -i :3000

# Kill it
kill -9 <PID>
```

### Something Broken?

```bash
./clean.sh    # Complete reset
./setup.sh    # Fresh start
```

---

## What You Get

### Services Running
- **Backend API** - FastAPI with auto-docs
- **Agent-Alpha** - AI agent system
- **Frontend** - React interface
- **PostgreSQL** - Database
- **Redis** - Caching
- **RabbitMQ** - Message queue
- **IPFS** - Decentralized storage
- **NGINX** - Web server

### Everything Automated
- Health checks every 30 seconds
- Auto-restart if services crash
- Data persistence across restarts
- Log rotation and management
- Resource monitoring

---

## Next Steps

### 1. Submit Your First Contribution
```bash
./apply.sh    # Interactive mode
# Or: ./apply.sh code myfile.py "My Contribution"
```

### 2. Test the API
```bash
curl http://localhost:8000/health
```

### 3. Explore the Docs
Visit http://localhost:8000/docs to see all API endpoints

### 4. Check Logs
```bash
./logs.sh backend    # See backend activity
./logs.sh agent-alpha    # See agent activity
```

### 5. Monitor Health
```bash
watch -n 5 ./status.sh    # Auto-refresh every 5 seconds
```

---

## Common Tasks

### Add Your OpenAI Key Later

```bash
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
./restart.sh
```

### Update to Latest Version

```bash
git pull
docker-compose pull
./restart.sh
```

### Backup Your Data

```bash
docker-compose exec postgres pg_dump -U postgres nwu > backup.sql
```

### Restore from Backup

```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres nwu
```

---

## Tips

- 💡 Run `./help.sh` anytime you forget a command
- 💡 Use `./dev.sh` for an easy interactive menu
- 💡 Check `./status.sh` before debugging issues
- 💡 Always `./stop.sh` before shutting down your computer
- 💡 Your data survives restarts - only `./clean.sh` deletes it

---

## Still Need Help?

- 📖 Read [QUICKSTART.md](QUICKSTART.md) for detailed info
- 📖 Check [README.md](README.md) for architecture details
- 🐛 [Open an issue](https://github.com/Garrettc123/nwu-protocol/issues) if something's broken

---

**You're ready to go!** 🎉
