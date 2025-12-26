#!/bin/bash

# Development Helper Script

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_menu() {
    clear
    cat << EOF
${BLUE}╔════════════════════════════════════════════════════════════════╗
║              NWU Protocol - Development Menu                   ║
╚════════════════════════════════════════════════════════════════╝${NC}

${GREEN}Select an option:${NC}

  ${YELLOW}1)${NC} Start all services
  ${YELLOW}2)${NC} Stop all services
  ${YELLOW}3)${NC} Restart specific service
  ${YELLOW}4)${NC} View logs
  ${YELLOW}5)${NC} Check service status
  ${YELLOW}6)${NC} Open API documentation
  ${YELLOW}7)${NC} Run database migrations
  ${YELLOW}8)${NC} Execute tests
  ${YELLOW}9)${NC} Clean and reset
  ${YELLOW}0)${NC} Exit

EOF
    read -p "Enter choice: " choice
    echo ""
}

while true; do
    show_menu
    
    case $choice in
        1)
            echo -e "${GREEN}Starting all services...${NC}"
            docker-compose up -d
            read -p "Press Enter to continue..."
            ;;
        2)
            echo -e "${YELLOW}Stopping all services...${NC}"
            docker-compose down
            read -p "Press Enter to continue..."
            ;;
        3)
            docker-compose ps --services
            read -p "Enter service name: " service
            docker-compose restart "$service"
            read -p "Press Enter to continue..."
            ;;
        4)
            docker-compose ps --services
            read -p "Enter service name (or press Enter for all): " service
            if [ -z "$service" ]; then
                docker-compose logs --tail=50
            else
                docker-compose logs -f --tail=100 "$service"
            fi
            ;;
        5)
            ./status.sh
            read -p "Press Enter to continue..."
            ;;
        6)
            echo -e "${GREEN}Opening API docs in browser...${NC}"
            if command -v xdg-open > /dev/null; then
                xdg-open http://localhost:8000/docs
            elif command -v open > /dev/null; then
                open http://localhost:8000/docs
            else
                echo "Visit: http://localhost:8000/docs"
            fi
            read -p "Press Enter to continue..."
            ;;
        7)
            echo -e "${BLUE}Running database migrations...${NC}"
            docker-compose exec backend alembic upgrade head
            read -p "Press Enter to continue..."
            ;;
        8)
            echo -e "${BLUE}Running tests...${NC}"
            docker-compose exec backend pytest
            read -p "Press Enter to continue..."
            ;;
        9)
            ./clean.sh
            read -p "Press Enter to continue..."
            ;;
        0)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            read -p "Press Enter to continue..."
            ;;
    esac
done
