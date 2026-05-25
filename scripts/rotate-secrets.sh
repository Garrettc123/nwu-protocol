#!/usr/bin/env bash
# =============================================================================
# NWU Protocol — Secret Rotation Script
# =============================================================================
# Rotates auto-generated secrets (JWT_SECRET_KEY, SECRET_KEY, NSR_OVERRIDE_SECRET).
# External secrets (Stripe, Perplexity, etc.) must be rotated on their provider
# dashboards, then this script updates .env / Railway / GitHub.
#
# Schedule: Run quarterly or whenever a secret is suspected of compromise.
#
# Usage:
#   bash scripts/rotate-secrets.sh             # rotate all auto-gen secrets
#   bash scripts/rotate-secrets.sh --jwt-only  # rotate JWT keys only
#   bash scripts/rotate-secrets.sh --nsr-only  # rotate NSR override secret only
#   bash scripts/rotate-secrets.sh --all       # rotate + prompt for external secrets
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
AUDIT_LOG="$ROOT_DIR/logs/secret-rotations.log"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
log()  { echo -e "${CYAN}[rotate]${NC} $*"; }

# Flags
JWT_ONLY=false
NSR_ONLY=false
ROTATE_EXTERNAL=false

for arg in "$@"; do
  case $arg in
    --jwt-only)  JWT_ONLY=true ;;
    --nsr-only)  NSR_ONLY=true ;;
    --all)       ROTATE_EXTERNAL=true ;;
  esac
done

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [[ ! -f "$ENV_FILE" ]]; then
  err ".env not found. Run: bash scripts/setup-secrets.sh first."
  exit 1
fi

echo -e "${BOLD}${YELLOW}"
echo "╔══════════════════════════════════════════════╗"
echo "║   NWU Protocol — Secret Rotation             ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"
warn "This will replace secrets in .env and push to Railway/GitHub."
echo -en "${BOLD}Continue?${NC} [y/N]: "
read -r ans
[[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]] || { log "Aborted."; exit 0; }

# ---------------------------------------------------------------------------
# Backup .env
# ---------------------------------------------------------------------------

BACKUP="${ENV_FILE}.bak.$(date +%s)"
cp "$ENV_FILE" "$BACKUP"
ok "Backed up .env → $BACKUP"

mkdir -p "$(dirname "$AUDIT_LOG")" 2>/dev/null || true

generate_secret() {
  python3 -c "import secrets; print(secrets.token_urlsafe(48))"
}

update_env_var() {
  local var="$1"
  local new_val="$2"
  # Replace VAR=anything with VAR=new_val
  if grep -q "^${var}=" "$ENV_FILE"; then
    sed -i "s|^${var}=.*|${var}=${new_val}|" "$ENV_FILE"
  else
    echo "${var}=${new_val}" >> "$ENV_FILE"
  fi
}

audit_entry() {
  local var="$1"
  echo "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"action\":\"rotated\",\"var\":\"$var\"}" \
    >> "$AUDIT_LOG" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Rotate JWT / SECRET_KEY
# ---------------------------------------------------------------------------

if [[ "$NSR_ONLY" == "false" ]]; then
  echo
  log "Rotating JWT_SECRET_KEY and SECRET_KEY…"
  warn "⚠  All existing sessions will be invalidated immediately."

  NEW_JWT=$(generate_secret)
  NEW_SK=$(generate_secret)

  update_env_var "JWT_SECRET_KEY" "$NEW_JWT"
  update_env_var "SECRET_KEY" "$NEW_SK"

  audit_entry "JWT_SECRET_KEY"
  audit_entry "SECRET_KEY"

  ok "JWT_SECRET_KEY rotated (${#NEW_JWT} chars)"
  ok "SECRET_KEY rotated (${#NEW_SK} chars)"
fi

# ---------------------------------------------------------------------------
# Rotate NSR_OVERRIDE_SECRET
# ---------------------------------------------------------------------------

if [[ "$JWT_ONLY" == "false" ]]; then
  echo
  log "Rotating NSR_OVERRIDE_SECRET…"
  warn "⚠  Any pending dual-override sessions will be invalidated."

  NEW_NSR=$(generate_secret)
  update_env_var "NSR_OVERRIDE_SECRET" "$NEW_NSR"
  audit_entry "NSR_OVERRIDE_SECRET"
  ok "NSR_OVERRIDE_SECRET rotated (${#NEW_NSR} chars)"
fi

# ---------------------------------------------------------------------------
# Prompt for external secrets
# ---------------------------------------------------------------------------

if [[ "$ROTATE_EXTERNAL" == "true" ]]; then
  echo
  log "External secret rotation — paste new values (leave blank to keep current)"
  echo

  rotate_external() {
    local var="$1"
    local desc="$2"
    echo -en "${YELLOW}  $var${NC} ($desc): "
    read -rs new_val
    echo
    if [[ -n "$new_val" ]]; then
      update_env_var "$var" "$new_val"
      audit_entry "$var"
      ok "  $var updated"
    else
      log "  $var unchanged"
    fi
  }

  echo "Stripe keys (https://dashboard.stripe.com/apikeys):"
  rotate_external "STRIPE_SECRET_KEY" "sk_live_... or sk_test_..."
  rotate_external "STRIPE_WEBHOOK_SECRET" "whsec_... from Stripe webhook endpoint"
  rotate_external "STRIPE_PUBLISHABLE_KEY" "pk_live_... or pk_test_..."

  echo
  echo "AI / Research APIs:"
  rotate_external "PERPLEXITY_API_KEY" "pplx-... from perplexity.ai"
  rotate_external "OPENAI_API_KEY" "sk-... from openai.com (optional)"
fi

# ---------------------------------------------------------------------------
# Push to Railway
# ---------------------------------------------------------------------------

echo
if command -v railway &>/dev/null; then
  echo -en "${BOLD}Push rotated secrets to Railway?${NC} [y/N]: "
  read -r ans
  if [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
    bash "$SCRIPT_DIR/push-to-railway.sh" "$ENV_FILE"
  fi
else
  warn "railway CLI not found — push manually: bash scripts/push-to-railway.sh .env"
fi

# ---------------------------------------------------------------------------
# Push to GitHub
# ---------------------------------------------------------------------------

echo
if command -v gh &>/dev/null; then
  echo -en "${BOLD}Push rotated secrets to GitHub?${NC} [y/N]: "
  read -r ans
  if [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
    bash "$SCRIPT_DIR/push-to-github.sh" "$ENV_FILE"
  fi
else
  warn "gh CLI not found — push manually: bash scripts/push-to-github.sh .env"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo
echo -e "${GREEN}${BOLD}✅ Rotation complete.${NC}"
echo "  Audit log: $AUDIT_LOG"
echo "  Backup:    $BACKUP"
echo
echo "  Next rotation: $(date -d '+90 days' '+%Y-%m-%d' 2>/dev/null || date -v+90d '+%Y-%m-%d' 2>/dev/null || echo 'in 90 days')"
