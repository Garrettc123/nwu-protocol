#!/usr/bin/env bash
# =============================================================================
# NWU Protocol — Push secrets from .env to Railway
# =============================================================================
# Usage:
#   bash scripts/push-to-railway.sh            # uses .env in project root
#   bash scripts/push-to-railway.sh /path/.env
#   RAILWAY_TOKEN=xxx bash scripts/push-to-railway.sh   # non-interactive
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/.env}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
log()  { echo -e "${CYAN}[railway]${NC} $*"; }

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [[ ! -f "$ENV_FILE" ]]; then
  err ".env not found at $ENV_FILE"; exit 1
fi

if ! command -v railway &>/dev/null; then
  err "railway CLI not installed."
  echo "  Install: npm install -g @railway/cli"
  echo "  Docs:    https://docs.railway.app/develop/cli"
  exit 1
fi

# ---------------------------------------------------------------------------
# Login check
# ---------------------------------------------------------------------------

log "Checking Railway auth…"
if ! railway whoami &>/dev/null 2>&1; then
  if [[ -n "${RAILWAY_TOKEN:-}" ]]; then
    log "Using RAILWAY_TOKEN from environment"
    export RAILWAY_TOKEN
  else
    warn "Not logged in to Railway. Running login…"
    railway login
  fi
fi

RAILWAY_USER=$(railway whoami 2>/dev/null || echo "unknown")
ok "Logged in as: $RAILWAY_USER"

# ---------------------------------------------------------------------------
# Skip list — infrastructure-level vars managed by Railway itself
# ---------------------------------------------------------------------------

SKIP_VARS=(
  "NODE_ENV"
  "ENVIRONMENT"
  "API_PORT"
  "DASHBOARD_PORT"
  "IPFS_HOST"
  "IPFS_PORT"
  "IPFS_API_URL"
  "IPFS_GATEWAY_URL"
)

is_skip() {
  local v="$1"
  for skip in "${SKIP_VARS[@]}"; do
    [[ "$v" == "$skip" ]] && return 0
  done
  return 1
}

# ---------------------------------------------------------------------------
# Parse .env and push each var
# ---------------------------------------------------------------------------

log "Pushing secrets from $ENV_FILE to Railway…"
echo

PUSHED=0
SKIPPED=0
EMPTY=0

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip comments and blank lines
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line// }" ]] && continue
  # Must contain =
  [[ "$line" != *"="* ]] && continue

  VAR="${line%%=*}"
  VAL="${line#*=}"

  # Skip empty values
  if [[ -z "$VAL" ]]; then
    warn "  SKIP (empty): $VAR"
    ((EMPTY++)) || true
    continue
  fi

  # Skip infra vars managed by Railway
  if is_skip "$VAR"; then
    log "  SKIP (railway-managed): $VAR"
    ((SKIPPED++)) || true
    continue
  fi

  # Push
  if railway variables --set "${VAR}=${VAL}" &>/dev/null 2>&1; then
    ok "  SET: $VAR"
    ((PUSHED++)) || true
  else
    err "  FAILED: $VAR"
  fi

done < "$ENV_FILE"

echo
ok "Railway push complete — ${PUSHED} vars set, ${SKIPPED} skipped, ${EMPTY} empty."

# ---------------------------------------------------------------------------
# Trigger redeploy
# ---------------------------------------------------------------------------

echo
echo -en "${YELLOW}Trigger a Railway redeploy now?${NC} [y/N]: "
read -r ans
if [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
  log "Redeploying…"
  railway up --detach && ok "Redeploy queued." || warn "Redeploy command failed — trigger manually in Railway dashboard."
else
  log "Skipped redeploy. Trigger manually or push a commit to redeploy."
fi
