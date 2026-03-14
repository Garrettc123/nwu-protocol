#!/bin/bash

################################################################################
# NWU Protocol - Automation Setup Script
# Installs and configures all automation scripts
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

print_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}║          NWU Protocol - Automation Setup                      ║${NC}"
    echo -e "${CYAN}║         Installing All Automation Scripts                     ║${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_fail() {
    echo -e "${RED}[✗]${NC} $1"
}

# Make all scripts executable
setup_permissions() {
    log_info "Setting up script permissions..."
    
    chmod +x "$SCRIPT_DIR"/*.sh
    chmod +x "$REPO_ROOT"/*.sh
    
    log_success "All scripts are now executable"
}

# Install pre-commit hooks
setup_git_hooks() {
    log_info "Installing Git hooks..."
    
    HOOKS_DIR="$REPO_ROOT/.git/hooks"
    
    if [ ! -d "$HOOKS_DIR" ]; then
        log_warning "Not a Git repository, skipping hooks installation"
        return 0
    fi
    
    # Install pre-commit hook
    if [ -f "$HOOKS_DIR/pre-commit" ]; then
        log_warning "Pre-commit hook already exists"
        read -p "Overwrite existing pre-commit hook? [y/N]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing hook"
            return 0
        fi
        mv "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit.backup"
        log_info "Backed up existing hook to pre-commit.backup"
    fi
    
    cp "$SCRIPT_DIR/pre-commit-hook.sh" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    
    log_success "Pre-commit hook installed"
}

# Create convenient aliases
setup_aliases() {
    log_info "Creating convenient command aliases..."
    
    # Create symlinks in root for easy access
    ln -sf "scripts/test-runner.sh" "$REPO_ROOT/test-all.sh" 2>/dev/null || true
    ln -sf "scripts/config-wizard.sh" "$REPO_ROOT/configure.sh" 2>/dev/null || true
    
    log_success "Created convenience scripts:"
    echo "  - test-all.sh     -> Unified test runner"
    echo "  - configure.sh    -> Configuration wizard"
}

# Test scripts
test_scripts() {
    log_info "Testing automation scripts..."
    
    # Test service registry
    if source "$SCRIPT_DIR/service-registry.sh" 2>/dev/null; then
        log_success "Service registry loads correctly"
    else
        log_warning "Service registry has issues"
    fi
    
    # Test if test runner syntax is valid
    if bash -n "$SCRIPT_DIR/test-runner.sh" 2>/dev/null; then
        log_success "Test runner syntax is valid"
    else
        log_warning "Test runner has syntax errors"
    fi
    
    # Test config wizard syntax
    if bash -n "$SCRIPT_DIR/config-wizard.sh" 2>/dev/null; then
        log_success "Config wizard syntax is valid"
    else
        log_warning "Config wizard has syntax errors"
    fi
}

# Show usage information
show_usage() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}                  Available Automation                         ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}Configuration${NC}"
    echo "  ./configure.sh              - Interactive environment setup wizard"
    echo "  ./scripts/config-wizard.sh  - Same as above"
    echo ""
    echo -e "${BLUE}Testing${NC}"
    echo "  ./test-all.sh               - Unified test runner with smart caching"
    echo "  ./test-all.sh --no-cache    - Force run all tests"
    echo "  ./test-all.sh api health    - Run specific test categories"
    echo "  ./scripts/test-runner.sh    - Same as test-all.sh"
    echo ""
    echo -e "${BLUE}Service Management${NC}"
    echo "  ./deploy.sh                 - Deploy all services"
    echo "  ./status.sh                 - Check service status"
    echo "  ./logs.sh                   - View service logs"
    echo "  make deploy                 - Alternative deployment"
    echo ""
    echo -e "${BLUE}Pre-Commit Automation${NC}"
    echo "  Automatically runs on 'git commit':"
    echo "  - Code formatting (Prettier, Black)"
    echo "  - Secret detection"
    echo "  - Debug statement warnings"
    echo "  - File size checks"
    echo "  - Commit message validation"
    echo ""
    echo -e "${BLUE}Shared Utilities${NC}"
    echo "  scripts/service-registry.sh - Central service definitions"
    echo "  scripts/pre-commit-hook.sh  - Enhanced pre-commit checks"
    echo ""
}

# Main setup
main() {
    print_banner
    
    cd "$REPO_ROOT"
    
    log_info "Repository root: $REPO_ROOT"
    log_info "Scripts directory: $SCRIPT_DIR"
    echo ""
    
    setup_permissions
    setup_git_hooks
    setup_aliases
    test_scripts
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Automation Setup Complete!                       ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    
    show_usage
    
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run configuration wizard: ${CYAN}./configure.sh${NC}"
    echo "  2. Deploy services: ${CYAN}./deploy.sh${NC}"
    echo "  3. Run tests: ${CYAN}./test-all.sh${NC}"
    echo ""
}

main "$@"
