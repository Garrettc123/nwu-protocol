#!/usr/bin/env bash
# =============================================================================
# NWU Protocol — Secrets Setup Wizard
# =============================================================================
# Usage:
#   bash scripts/setup-secrets.sh              # interactive (recommended)
#   bash scripts/setup-secrets.sh --non-interactive  # CI/automation mode
#   bash scripts/setup-secrets.sh --railway-only     # push existing .env to Railway
#   bash scripts/setup-secrets.sh --github-only      # push existing .env to GitHub secrets
#
# What it does:
#   1. Auto-generates strong values for JWT_SECRET_KEY, SECRET_KEY, NSR_OVERRIDE_SECRET
#   2. Prompts for external keys (Stripe, Perplexity, Infura, etc.)
#   3. Writes a .env file (never committed — in .gitignore)
#   4. If `railway` CLI is available: pushes all vars to Railway
#   5. If `gh` CLI is available: pushes all vars to GitHub secrets
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"
LOG_FILE="$ROOT_DIR/logs/secrets-setup.log"

# Colours
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# Flags
NON_INTERACTIVE=false
RAILWAY_ONLY=false
GITHUB_ONLY=false
SKIP_RAILWAY=false
SKIP_GITHUB=false

for arg in "$@"; do
  case $arg in
    --non-interactive) NON_INTERACTIVE=true ;;
    --railway-only)    RAILWAY_ONLY=true ;;
    --github-only)     GITHUB_ONLY=true ;;
    --skip-railway)    SKIP_RAILWAY=true ;;
    --skip-github)     SKIP_GITHUB=true ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { echo -e "${CYAN}[secrets]${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
head_section() { echo -e "\n${BOLD}${BLUE}── $* ──────────────────────────────────────${NC}"; }

mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

generate_secret() {
  # Generate a cryptographically strong URL-safe base64 secret (48 bytes → 64 chars)
  python3 -c "import secrets; print(secrets.token_urlsafe(48))"
}

prompt() {
  local var_name="$1"
  local description="$2"
  local default="${3:-}"
  local is_secret="${4:-true}"

  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    echo "$default"
    return
  fi

  if [[ "$is_secret" == "true" ]]; then
    echo -en "${YELLOW}  ${var_name}${NC} (${description}): " >&2
    read -rs value
    echo >&2
  else
    echo -en "${YELLOW}  ${var_name}${NC} (${description}) [${default}]: " >&2
    read -r value
    value="${value:-$default}"
  fi
  echo "$value"
}

prompt_confirm() {
  if [[ "$NON_INTERACTIVE" == "true" ]]; then return 0; fi
  echo -en "${BOLD}$1${NC} [y/N]: "
  read -r ans
  [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║   NWU Protocol — Secrets Setup Wizard        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ---------------------------------------------------------------------------
# Guard: --railway-only / --github-only modes
# ---------------------------------------------------------------------------

if [[ "$RAILWAY_ONLY" == "true" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    err ".env not found — run without --railway-only first."; exit 1
  fi
  log "Pushing existing .env to Railway…"
  source "$ENV_FILE" 2>/dev/null || true
  bash "$SCRIPT_DIR/push-to-railway.sh" "$ENV_FILE"
  exit 0
fi

if [[ "$GITHUB_ONLY" == "true" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    err ".env not found — run without --github-only first."; exit 1
  fi
  log "Pushing existing .env to GitHub secrets…"
  bash "$SCRIPT_DIR/push-to-github.sh" "$ENV_FILE"
  exit 0
fi

# ---------------------------------------------------------------------------
# Check existing .env
# ---------------------------------------------------------------------------

if [[ -f "$ENV_FILE" ]]; then
  warn ".env already exists at $ENV_FILE"
  if ! prompt_confirm "Overwrite it?"; then
    log "Keeping existing .env. Use --railway-only or --github-only to push."
    exit 0
  fi
  cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)"
  ok "Backed up old .env"
fi

# ---------------------------------------------------------------------------
# SECTION 1 — Auto-generated secrets
# ---------------------------------------------------------------------------

head_section "Auto-generated secrets (no input needed)"

JWT_SECRET_KEY=$(generate_secret)
SECRET_KEY=$(generate_secret)
NSR_OVERRIDE_SECRET=$(generate_secret)

ok "JWT_SECRET_KEY      generated (${#JWT_SECRET_KEY} chars)"
ok "SECRET_KEY          generated (${#SECRET_KEY} chars)"
ok "NSR_OVERRIDE_SECRET generated (${#NSR_OVERRIDE_SECRET} chars)"

# ---------------------------------------------------------------------------
# SECTION 2 — Stripe
# ---------------------------------------------------------------------------

head_section "Stripe (payments)"
log "Get your keys at: https://dashboard.stripe.com/apikeys"
log "Get webhook secret at: https://dashboard.stripe.com/webhooks"
echo

if [[ "$NON_INTERACTIVE" == "false" ]]; then
  STRIPE_ENV="test"
  echo -e "  Use ${YELLOW}test${NC} keys (sk_test_*) or ${RED}live${NC} keys (sk_live_*)?"
  echo -en "  [test/live, default=test]: "
  read -r STRIPE_ENV_INPUT
  STRIPE_ENV="${STRIPE_ENV_INPUT:-test}"
fi

STRIPE_SECRET_KEY=$(prompt "STRIPE_SECRET_KEY" "sk_${STRIPE_ENV:-test}_..." "")
STRIPE_PUBLISHABLE_KEY=$(prompt "STRIPE_PUBLISHABLE_KEY" "pk_${STRIPE_ENV:-test}_..." "")
STRIPE_WEBHOOK_SECRET=$(prompt "STRIPE_WEBHOOK_SECRET" "whsec_... (from Stripe webhook endpoint)" "")

# Stripe Price IDs (optional)
echo
log "Stripe Price IDs (optional — leave blank to skip)"
STRIPE_PRICE_ID_BASIC=$(prompt "STRIPE_PRICE_ID_BASIC" "price_... for Basic plan" "" false)
STRIPE_PRICE_ID_PREMIUM=$(prompt "STRIPE_PRICE_ID_PREMIUM" "price_... for Pro plan" "" false)
STRIPE_PRICE_ID_ENTERPRISE=$(prompt "STRIPE_PRICE_ID_ENTERPRISE" "price_... for Enterprise plan" "" false)

# ---------------------------------------------------------------------------
# SECTION 3 — AI / Research APIs
# ---------------------------------------------------------------------------

head_section "AI & Research APIs"

PERPLEXITY_API_KEY=$(prompt "PERPLEXITY_API_KEY" "pplx-... from https://www.perplexity.ai/settings/api" "")
OPENAI_API_KEY=$(prompt "OPENAI_API_KEY" "sk-... (optional)" "")

# ---------------------------------------------------------------------------
# SECTION 4 — Blockchain / Infura
# ---------------------------------------------------------------------------

head_section "Blockchain (optional)"
log "Leave blank to skip blockchain features"
echo

ETH_RPC_URL=$(prompt "ETH_RPC_URL / INFURA_PROJECT_ID" "https://mainnet.infura.io/v3/YOUR_ID" "" false)
SEPOLIA_RPC_URL=$(prompt "SEPOLIA_RPC_URL" "https://sepolia.infura.io/v3/YOUR_ID" "" false)
PRIVATE_KEY=$(prompt "PRIVATE_KEY" "0x... deployer wallet private key" "")
ETHERSCAN_API_KEY=$(prompt "ETHERSCAN_API_KEY" "from https://etherscan.io/apis" "")

# ---------------------------------------------------------------------------
# SECTION 5 — Infrastructure (optional overrides)
# ---------------------------------------------------------------------------

head_section "Infrastructure (defaults shown)"

DATABASE_URL=$(prompt "DATABASE_URL" "postgres connection string" \
  "postgresql://nwu_user:rocket69!@postgres:5432/nwu_db" false)
MONGO_URL=$(prompt "MONGO_URL" "mongodb connection string" \
  "mongodb://admin:rocket69!@mongodb:27017/nwu_db?authSource=admin" false)
REDIS_URL=$(prompt "REDIS_URL" "redis connection string" "redis://redis:6379" false)
RABBITMQ_URL=$(prompt "RABBITMQ_URL" "amqp connection string" "amqp://guest:guest@rabbitmq:5672" false)

# ---------------------------------------------------------------------------
# Write .env
# ---------------------------------------------------------------------------

head_section "Writing .env"

cat > "$ENV_FILE" << ENV
# =============================================================================
# NWU Protocol — Environment Variables
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# WARNING: Never commit this file. It is listed in .gitignore.
# =============================================================================

# ── Application ──────────────────────────────────────────────────────────────
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false
APP_NAME=NWU Protocol API
APP_VERSION=1.0.0

# ── Authentication ────────────────────────────────────────────────────────────
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=${DATABASE_URL}
MONGO_URL=${MONGO_URL}
MONGODB_URI=${MONGO_URL}

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=${REDIS_URL}

# ── RabbitMQ ──────────────────────────────────────────────────────────────────
RABBITMQ_URL=${RABBITMQ_URL}

# ── IPFS ─────────────────────────────────────────────────────────────────────
IPFS_HOST=ipfs
IPFS_PORT=5001
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=https://gateway.ipfs.io

# ── Stripe ───────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
STRIPE_API_KEY=${STRIPE_SECRET_KEY}
STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
STRIPE_PRICE_ID_BASIC=${STRIPE_PRICE_ID_BASIC}
STRIPE_PRICE_ID_PREMIUM=${STRIPE_PRICE_ID_PREMIUM}
STRIPE_PRICE_ID_ENTERPRISE=${STRIPE_PRICE_ID_ENTERPRISE}

# ── AI / Research ─────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

# ── NSR / UEEP ───────────────────────────────────────────────────────────────
# IMPORTANT: In production, move NSR_OVERRIDE_SECRET to AWS Secrets Manager
# or equivalent KMS. Rotate quarterly.
NSR_OVERRIDE_SECRET=${NSR_OVERRIDE_SECRET}

# ── Blockchain ───────────────────────────────────────────────────────────────
ETH_RPC_URL=${ETH_RPC_URL}
ETHEREUM_RPC_URL=${ETH_RPC_URL}
SEPOLIA_RPC_URL=${SEPOLIA_RPC_URL}
ETHEREUM_MAINNET_RPC_URL=${ETH_RPC_URL}
PRIVATE_KEY=${PRIVATE_KEY}
ETHERSCAN_API_KEY=${ETHERSCAN_API_KEY}
CONTRACT_ADDRESS=

# ── Subscription Rate Limits ──────────────────────────────────────────────────
SUBSCRIPTION_TIER_FREE_RATE_LIMIT=100
SUBSCRIPTION_TIER_PRO_RATE_LIMIT=10000
SUBSCRIPTION_TIER_ENTERPRISE_RATE_LIMIT=100000

# ── Ports ─────────────────────────────────────────────────────────────────────
API_PORT=8000
DASHBOARD_PORT=3000
ENV

ok ".env written to $ENV_FILE"
log "Sensitive fields: JWT_SECRET_KEY, SECRET_KEY, NSR_OVERRIDE_SECRET are auto-generated."

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

head_section "Validation"
bash "$SCRIPT_DIR/validate-secrets.sh" "$ENV_FILE" 2>/dev/null || warn "Some optional secrets are missing (see above)"

# ---------------------------------------------------------------------------
# Push to Railway
# ---------------------------------------------------------------------------

if [[ "$SKIP_RAILWAY" == "false" ]]; then
  head_section "Railway"
  if command -v railway &>/dev/null; then
    if prompt_confirm "Push all secrets to Railway now?"; then
      bash "$SCRIPT_DIR/push-to-railway.sh" "$ENV_FILE"
    else
      log "Skipping Railway push. Run: bash scripts/push-to-railway.sh .env"
    fi
  else
    warn "railway CLI not found. Install: npm install -g @railway/cli"
    log "Then run: bash scripts/push-to-railway.sh .env"
  fi
fi

# ---------------------------------------------------------------------------
# Push to GitHub secrets
# ---------------------------------------------------------------------------

if [[ "$SKIP_GITHUB" == "false" ]]; then
  head_section "GitHub Secrets"
  if command -v gh &>/dev/null; then
    if prompt_confirm "Push all secrets to GitHub repository secrets now?"; then
      bash "$SCRIPT_DIR/push-to-github.sh" "$ENV_FILE"
    else
      log "Skipping GitHub push. Run: bash scripts/push-to-github.sh .env"
    fi
  else
    warn "gh CLI not found. Install: https://cli.github.com"
    log "Then run: bash scripts/push-to-github.sh .env"
  fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo
echo -e "${GREEN}${BOLD}✅ Secrets setup complete!${NC}"
echo
echo "  📄 Local .env:  $ENV_FILE"
echo "  📋 To rotate:   bash scripts/rotate-secrets.sh"
echo "  ✔  To validate: bash scripts/validate-secrets.sh"
echo "  🚂 To Railway:  bash scripts/push-to-railway.sh .env"
echo "  🐙 To GitHub:   bash scripts/push-to-github.sh .env"
echo
