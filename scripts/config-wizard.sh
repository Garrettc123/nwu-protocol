#!/bin/bash

################################################################################
# NWU Protocol - Interactive Configuration Wizard
# Automates environment setup with validation and helpful guidance
################################################################################

set -e

# Source service registry for colors
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/service-registry.sh"

CONFIG_FILE="${1:-.env}"
FRONTEND_CONFIG="${2:-frontend/.env.local}"

print_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}║          NWU Protocol - Configuration Wizard                  ║${NC}"
    echo -e "${CYAN}║           Automated Environment Setup                         ║${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Validate OpenAI API key format
validate_openai_key() {
    local key=$1
    if [[ $key =~ ^sk-[a-zA-Z0-9]{32,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Generate secure random secret
generate_secret() {
    openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | base64 | tr -d '=+/' | cut -c1-64
}

# Test OpenAI API key
test_openai_key() {
    local key=$1
    log_info "Testing OpenAI API key..."
    
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $key" \
        https://api.openai.com/v1/models 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        log_success "OpenAI API key is valid!"
        return 0
    else
        log_warning "Could not verify OpenAI API key (HTTP $http_code)"
        return 1
    fi
}

# Prompt for input with default value
prompt_with_default() {
    local prompt=$1
    local default=$2
    local value
    
    if [ -n "$default" ]; then
        read -p "$(echo -e "${BLUE}$prompt${NC} [${CYAN}$default${NC}]: ")" value
        echo "${value:-$default}"
    else
        read -p "$(echo -e "${BLUE}$prompt${NC}: ")" value
        echo "$value"
    fi
}

# Prompt for secret input (hidden)
prompt_secret() {
    local prompt=$1
    local value
    
    read -s -p "$(echo -e "${BLUE}$prompt${NC}: ")" value
    echo ""
    echo "$value"
}

# Check if config file exists
check_existing_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_warning "Configuration file already exists: $CONFIG_FILE"
        echo ""
        read -p "Do you want to overwrite it? [y/N]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing configuration"
            return 1
        fi
        log_info "Creating backup: ${CONFIG_FILE}.backup"
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    fi
    return 0
}

# Load existing configuration values
load_existing_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_info "Loading existing configuration..."
        source "$CONFIG_FILE"
    fi
}

# Main configuration wizard
run_wizard() {
    print_banner
    
    if ! check_existing_config; then
        exit 0
    fi
    
    load_existing_config
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}                  Core Configuration                          ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Database Configuration
    log_info "Database Configuration"
    POSTGRES_USER=$(prompt_with_default "PostgreSQL username" "${POSTGRES_USER:-nwu_user}")
    POSTGRES_PASSWORD=$(prompt_with_default "PostgreSQL password" "${POSTGRES_PASSWORD:-nwu_password}")
    POSTGRES_DB=$(prompt_with_default "PostgreSQL database" "${POSTGRES_DB:-nwu_db}")
    POSTGRES_HOST=$(prompt_with_default "PostgreSQL host" "${POSTGRES_HOST:-localhost}")
    POSTGRES_PORT=$(prompt_with_default "PostgreSQL port" "${POSTGRES_PORT:-5432}")
    echo ""
    
    # MongoDB Configuration
    log_info "MongoDB Configuration"
    MONGODB_USER=$(prompt_with_default "MongoDB username" "${MONGODB_USER:-admin}")
    MONGODB_PASSWORD=$(prompt_with_default "MongoDB password" "${MONGODB_PASSWORD:-rocket69!}")
    MONGODB_HOST=$(prompt_with_default "MongoDB host" "${MONGODB_HOST:-localhost}")
    MONGODB_PORT=$(prompt_with_default "MongoDB port" "${MONGODB_PORT:-27017}")
    echo ""
    
    # Redis Configuration
    log_info "Redis Configuration"
    REDIS_HOST=$(prompt_with_default "Redis host" "${REDIS_HOST:-localhost}")
    REDIS_PORT=$(prompt_with_default "Redis port" "${REDIS_PORT:-6379}")
    echo ""
    
    # RabbitMQ Configuration
    log_info "RabbitMQ Configuration"
    RABBITMQ_USER=$(prompt_with_default "RabbitMQ username" "${RABBITMQ_USER:-guest}")
    RABBITMQ_PASSWORD=$(prompt_with_default "RabbitMQ password" "${RABBITMQ_PASSWORD:-guest}")
    RABBITMQ_HOST=$(prompt_with_default "RabbitMQ host" "${RABBITMQ_HOST:-localhost}")
    RABBITMQ_PORT=$(prompt_with_default "RabbitMQ port" "${RABBITMQ_PORT:-5672}")
    echo ""
    
    # IPFS Configuration
    log_info "IPFS Configuration"
    IPFS_HOST=$(prompt_with_default "IPFS host" "${IPFS_HOST:-localhost}")
    IPFS_PORT=$(prompt_with_default "IPFS port" "${IPFS_PORT:-5001}")
    echo ""
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}                  API Configuration                           ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # OpenAI API Key
    log_info "OpenAI API Key (required for AI verification)"
    echo -e "${YELLOW}Get your API key from: https://platform.openai.com/api-keys${NC}"
    
    if [ -n "$OPENAI_API_KEY" ]; then
        log_info "Current key: ${OPENAI_API_KEY:0:10}...${OPENAI_API_KEY: -4}"
        read -p "Keep existing key? [Y/n]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            NEW_OPENAI_KEY="$OPENAI_API_KEY"
        fi
    fi
    
    while [ -z "$NEW_OPENAI_KEY" ]; do
        NEW_OPENAI_KEY=$(prompt_secret "Enter OpenAI API key")
        
        if [ -z "$NEW_OPENAI_KEY" ]; then
            log_warning "OpenAI API key is required for AI verification"
            read -p "Skip OpenAI configuration? [y/N]: " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                NEW_OPENAI_KEY="sk-REPLACE-WITH-YOUR-OPENAI-API-KEY"
                log_warning "Using placeholder. Update later in $CONFIG_FILE"
                break
            fi
            continue
        fi
        
        if ! validate_openai_key "$NEW_OPENAI_KEY"; then
            log_warning "Invalid API key format (should start with 'sk-')"
            NEW_OPENAI_KEY=""
            continue
        fi
        
        if ! test_openai_key "$NEW_OPENAI_KEY"; then
            log_warning "API key validation failed"
            read -p "Use this key anyway? [y/N]: " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                NEW_OPENAI_KEY=""
                continue
            fi
        fi
    done
    OPENAI_API_KEY="$NEW_OPENAI_KEY"
    echo ""
    
    # Security Configuration
    log_info "Security Configuration"
    if [ -z "$JWT_SECRET_KEY" ]; then
        log_info "Generating secure JWT secret..."
        JWT_SECRET_KEY=$(generate_secret)
        log_success "Generated JWT secret"
    else
        log_info "Using existing JWT secret"
    fi
    echo ""
    
    # Application Configuration
    log_info "Application Configuration"
    BACKEND_PORT=$(prompt_with_default "Backend API port" "${BACKEND_PORT:-8000}")
    FRONTEND_PORT=$(prompt_with_default "Frontend port" "${FRONTEND_PORT:-3000}")
    ENVIRONMENT=$(prompt_with_default "Environment (development/production)" "${ENVIRONMENT:-development}")
    echo ""
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}                  Writing Configuration                       ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Write main configuration
    log_info "Writing configuration to $CONFIG_FILE..."
    cat > "$CONFIG_FILE" << EOF
# NWU Protocol Configuration
# Generated by configuration wizard on $(date)

# Database Configuration
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=$POSTGRES_PORT

# MongoDB Configuration
MONGODB_USER=$MONGODB_USER
MONGODB_PASSWORD=$MONGODB_PASSWORD
MONGODB_HOST=$MONGODB_HOST
MONGODB_PORT=$MONGODB_PORT

# Redis Configuration
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT

# RabbitMQ Configuration
RABBITMQ_USER=$RABBITMQ_USER
RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD
RABBITMQ_HOST=$RABBITMQ_HOST
RABBITMQ_PORT=$RABBITMQ_PORT

# IPFS Configuration
IPFS_HOST=$IPFS_HOST
IPFS_PORT=$IPFS_PORT

# OpenAI Configuration
OPENAI_API_KEY=$OPENAI_API_KEY

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY

# Application Configuration
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
ENVIRONMENT=$ENVIRONMENT

# Database URLs (auto-generated)
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB
MONGODB_URL=mongodb://$MONGODB_USER:$MONGODB_PASSWORD@$MONGODB_HOST:$MONGODB_PORT
REDIS_URL=redis://$REDIS_HOST:$REDIS_PORT
RABBITMQ_URL=amqp://$RABBITMQ_USER:$RABBITMQ_PASSWORD@$RABBITMQ_HOST:$RABBITMQ_PORT
EOF
    
    log_success "Configuration written to $CONFIG_FILE"
    
    # Write frontend configuration if directory exists
    if [ -d "$(dirname "$FRONTEND_CONFIG")" ]; then
        log_info "Writing frontend configuration to $FRONTEND_CONFIG..."
        cat > "$FRONTEND_CONFIG" << EOF
# Frontend Configuration
# Generated by configuration wizard on $(date)

NEXT_PUBLIC_API_URL=http://localhost:$BACKEND_PORT
NEXT_PUBLIC_ENVIRONMENT=$ENVIRONMENT
EOF
        log_success "Frontend configuration written to $FRONTEND_CONFIG"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Configuration complete!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Review configuration: cat $CONFIG_FILE"
    echo "  2. Start services: ./deploy.sh"
    echo "  3. Check status: ./status.sh"
    echo ""
    echo -e "${YELLOW}Note:${NC} Configuration is stored in:"
    echo "  - $CONFIG_FILE"
    [ -f "$FRONTEND_CONFIG" ] && echo "  - $FRONTEND_CONFIG"
    echo ""
}

# Run the wizard
run_wizard
