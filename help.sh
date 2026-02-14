#!/bin/bash

# Help and Documentation

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cat << EOF
${BLUE}╔════════════════════════════════════════════════════════════════╗
║              NWU Protocol - Quick Reference                    ║
╚════════════════════════════════════════════════════════════════╝${NC}

${GREEN}🚀 GETTING STARTED${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  ./setup.sh              One-command setup (first time)
  ./status.sh             Check all services
  ./logs.sh [service]     View logs (all or specific service)
  ./apply.sh              Submit a contribution (interactive)

${GREEN}🔧 MANAGEMENT${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  ./stop.sh               Stop all services (keeps data)
  ./restart.sh [service]  Restart all or specific service
  ./clean.sh              Delete everything and reset

${GREEN}🌐 SERVICE URLS${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  Frontend:       http://localhost:3000
  Backend API:    http://localhost:8000
  API Docs:       http://localhost:8000/docs
  RabbitMQ:       http://localhost:15672 (guest/guest)
  PostgreSQL:     localhost:5432
  Redis:          localhost:6379
  IPFS:           http://localhost:5001

${GREEN}🛠️ DOCKER COMMANDS${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  docker-compose ps                      List containers
  docker-compose logs -f backend         Follow backend logs
  docker-compose exec backend bash       Enter backend shell
  docker-compose restart agent-alpha     Restart specific service

${GREEN}🔍 TROUBLESHOOTING${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  1. Services won't start?
     → Check: docker-compose logs
     → Verify: .env file has OPENAI_API_KEY

  2. Port already in use?
     → Check: lsof -i :3000 (or other port)
     → Stop: kill -9 <PID>

  3. Out of disk space?
     → Clean: docker system prune -a
     → Check: df -h

  4. Reset everything?
     → Run: ./clean.sh
     → Then: ./setup.sh

${GREEN}📚 DOCUMENTATION${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  README.md          Full project documentation
  QUICKSTART.md      Quick setup guide
  SETUP_GUIDE.md     Detailed setup instructions
  CONTRIBUTING.md    Contribution guidelines

${GREEN}💡 TIPS${NC}
${YELLOW}──────────────────────────────────────────────────────────────${NC}
  • Run './status.sh' regularly to monitor health
  • Use './logs.sh backend' to debug API issues
  • Keep .env file secure (never commit it)
  • Check http://localhost:8000/docs for API testing

${BLUE}════════════════════════════════════════════════════════════════${NC}
${GREEN}Need more help? Check the docs or open an issue on GitHub${NC}
${BLUE}════════════════════════════════════════════════════════════════${NC}

EOF
