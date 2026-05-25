#!/usr/bin/env bash
# =============================================================================
# NWU Protocol — Secrets Validator
# =============================================================================
# Checks that all required secrets are set and have the expected format.
# Exit code 0 = all required secrets present; 1 = missing/invalid required.
#
# Usage:
#   bash scripts/validate-secrets.sh          # validates .env in project root
#   bash scripts/validate-secrets.sh /path/.env
#   bash scripts/validate-secrets.sh --env    # validates from current shell env
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

FROM_ENV=false
ENV_FILE="$ROOT_DIR/.env"

for arg in "$@"; do
  case $arg in
    --env) FROM_ENV=true ;;
    *)     ENV_FILE="$arg" ;;
  esac
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC}  $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "${RED}✗${NC}  $*"; }
log()  { echo -e "${CYAN}[validate]${NC} $*"; }

ERRORS=0
WARNINGS=0

# ---------------------------------------------------------------------------
# Load .env into associative array
# ---------------------------------------------------------------------------

declare -A VARS

if [[ "$FROM_ENV" == "true" ]]; then
  log "Reading secrets from shell environment"
  # Capture all env vars
  while IFS='=' read -r key val; do
    VARS["$key"]="$val"
  done < <(env)
else
  if [[ ! -f "$ENV_FILE" ]]; then
    err ".env not found at $ENV_FILE"
    echo "  Run: bash scripts/setup-secrets.sh"
    exit 1
  fi
  log "Validating $ENV_FILE"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    [[ "$line" != *"="* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    VARS["$key"]="$val"
  done < "$ENV_FILE"
fi

# ---------------------------------------------------------------------------
# Validator helpers
# ---------------------------------------------------------------------------

check_required() {
  local var="$1"
  local desc="${2:-}"
  local val="${VARS[$var]:-}"
  if [[ -z "$val" ]]; then
    err "MISSING (required): $var${desc:+ — $desc}"
    ((ERRORS++)) || true
    return 1
  fi
  ok "$var"
  return 0
}

check_optional() {
  local var="$1"
  local desc="${2:-}"
  local val="${VARS[$var]:-}"
  if [[ -z "$val" ]]; then
    warn "MISSING (optional): $var${desc:+ — $desc}"
    ((WARNINGS++)) || true
  else
    ok "$var"
  fi
}

check_format() {
  local var="$1"
  local pattern="$2"
  local desc="${3:-}"
  local val="${VARS[$var]:-}"
  if [[ -z "$val" ]]; then return; fi  # already caught by check_required
  if [[ ! "$val" =~ $pattern ]]; then
    err "BAD FORMAT: $var — expected $desc, got: ${val:0:12}…"
    ((ERRORS++)) || true
  fi
}

check_min_length() {
  local var="$1"
  local min_len="$2"
  local val="${VARS[$var]:-}"
  if [[ -z "$val" ]]; then return; fi
  if [[ ${#val} -lt $min_len ]]; then
    err "TOO SHORT: $var — expected ≥${min_len} chars, got ${#val}"
    ((ERRORS++)) || true
  fi
}

# ---------------------------------------------------------------------------
# SECTION 1 — Authentication (required)
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── Authentication ──────────────────────────────────────${NC}"
check_required "JWT_SECRET_KEY" "JWT signing secret"
check_min_length "JWT_SECRET_KEY" 32
check_required "SECRET_KEY" "App secret key"
check_min_length "SECRET_KEY" 32

# Guard against weak defaults
for var in "JWT_SECRET_KEY" "SECRET_KEY"; do
  val="${VARS[$var]:-}"
  if [[ "$val" == *"your-secret"* || "$val" == *"change-in-production"* || "$val" == "secret" ]]; then
    err "WEAK VALUE: $var — still using placeholder. Run: bash scripts/setup-secrets.sh"
    ((ERRORS++)) || true
  fi
done

# ---------------------------------------------------------------------------
# SECTION 2 — NSR (required)
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── NSR / UEEP ───────────────────────────────────────────${NC}"
check_required "NSR_OVERRIDE_SECRET" "Dual-override HMAC secret"
check_min_length "NSR_OVERRIDE_SECRET" 32

val="${VARS[NSR_OVERRIDE_SECRET]:-}"
if [[ "$val" == "change-me-use-kms" ]]; then
  err "WEAK VALUE: NSR_OVERRIDE_SECRET — still using default. Run setup-secrets.sh"
  ((ERRORS++)) || true
fi

# ---------------------------------------------------------------------------
# SECTION 3 — Database (required)
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── Database ─────────────────────────────────────────────${NC}"
check_required "DATABASE_URL" "PostgreSQL connection string"
check_format "DATABASE_URL" "^postgresql://" "postgresql://..."
check_optional "MONGO_URL" "MongoDB connection (optional feature)"

# ---------------------------------------------------------------------------
# SECTION 4 — Stripe (required for payments)
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── Stripe ───────────────────────────────────────────────${NC}"
check_required "STRIPE_SECRET_KEY"      "Stripe secret key (payments)"
check_required "STRIPE_PUBLISHABLE_KEY" "Stripe publishable key"
check_required "STRIPE_WEBHOOK_SECRET"  "Stripe webhook signing secret"

check_format "STRIPE_SECRET_KEY"      "^sk_(test|live)_" "sk_test_... or sk_live_..."
check_format "STRIPE_PUBLISHABLE_KEY" "^pk_(test|live)_" "pk_test_... or pk_live_..."
check_format "STRIPE_WEBHOOK_SECRET"  "^whsec_"          "whsec_..."

# Warn if test keys in non-debug env
env_val="${VARS[ENVIRONMENT]:-development}"
sk="${VARS[STRIPE_SECRET_KEY]:-}"
if [[ "$env_val" == "production" && "$sk" =~ ^sk_test_ ]]; then
  warn "STRIPE_SECRET_KEY is a TEST key but ENVIRONMENT=production — update before going live"
  ((WARNINGS++)) || true
fi

check_optional "STRIPE_PRICE_ID_BASIC"      "Stripe price ID for Basic tier"
check_optional "STRIPE_PRICE_ID_PREMIUM"    "Stripe price ID for Pro tier"
check_optional "STRIPE_PRICE_ID_ENTERPRISE" "Stripe price ID for Enterprise tier"

# ---------------------------------------------------------------------------
# SECTION 5 — AI / Research APIs
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── AI / Research APIs ───────────────────────────────────${NC}"
check_required "PERPLEXITY_API_KEY" "Perplexity AI (NSR research features)"
check_format "PERPLEXITY_API_KEY" "^pplx-" "pplx-..."
check_optional "OPENAI_API_KEY" "OpenAI (optional — for legacy agents)"

# ---------------------------------------------------------------------------
# SECTION 6 — Infrastructure
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── Infrastructure ───────────────────────────────────────${NC}"
check_required "REDIS_URL"    "Redis connection string"
check_required "RABBITMQ_URL" "RabbitMQ connection string"

# ---------------------------------------------------------------------------
# SECTION 7 — Blockchain (optional)
# ---------------------------------------------------------------------------

echo -e "\n${BOLD}── Blockchain (optional) ────────────────────────────────${NC}"
check_optional "ETH_RPC_URL"       "Ethereum RPC (Infura/Alchemy)"
check_optional "SEPOLIA_RPC_URL"   "Sepolia testnet RPC"
check_optional "PRIVATE_KEY"       "Deployer wallet private key"
check_optional "ETHERSCAN_API_KEY" "Etherscan API key"

# Private key sanity check
pk="${VARS[PRIVATE_KEY]:-}"
if [[ -n "$pk" && ${#pk} -lt 64 ]]; then
  warn "PRIVATE_KEY looks short (${#pk} chars) — Ethereum private keys are 64 hex chars"
  ((WARNINGS++)) || true
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
echo "─────────────────────────────────────────────────────"
if [[ $ERRORS -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}✅ All required secrets are valid.${NC} ${WARNINGS} warning(s)."
  exit 0
else
  echo -e "${RED}${BOLD}❌ Validation failed: ${ERRORS} error(s), ${WARNINGS} warning(s).${NC}"
  echo "   Run: bash scripts/setup-secrets.sh"
  exit 1
fi
