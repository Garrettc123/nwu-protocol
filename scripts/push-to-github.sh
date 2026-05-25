#!/usr/bin/env bash
# =============================================================================
# NWU Protocol — Push secrets from .env to GitHub repository secrets
# =============================================================================
# Usage:
#   bash scripts/push-to-github.sh            # uses .env in project root
#   bash scripts/push-to-github.sh /path/.env
#
# Requires: gh CLI (https://cli.github.com) authenticated with repo access
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/.env}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
log()  { echo -e "${CYAN}[github]${NC} $*"; }

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [[ ! -f "$ENV_FILE" ]]; then
  err ".env not found at $ENV_FILE"; exit 1
fi

if ! command -v gh &>/dev/null; then
  err "gh CLI not installed."
  echo "  Install: https://cli.github.com"
  echo "  Then run: gh auth login"
  exit 1
fi

# ---------------------------------------------------------------------------
# Auth check
# ---------------------------------------------------------------------------

log "Checking GitHub auth…"
GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "")
if [[ -z "$GH_USER" ]]; then
  warn "Not authenticated. Running gh auth login…"
  gh auth login
  GH_USER=$(gh api user --jq '.login')
fi
ok "Logged in as: $GH_USER"

# Detect repo
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo "")
if [[ -z "$REPO" ]]; then
  err "Could not detect GitHub repo. Run from inside the repo directory."
  exit 1
fi
log "Target repo: $REPO"

# ---------------------------------------------------------------------------
# Skip list — not needed in GitHub secrets (CI uses them differently)
# ---------------------------------------------------------------------------

SKIP_VARS=(
  "NODE_ENV"
  "DEBUG"
  "APP_NAME"
  "APP_VERSION"
  "API_PORT"
  "DASHBOARD_PORT"
  "SUBSCRIPTION_TIER_FREE_RATE_LIMIT"
  "SUBSCRIPTION_TIER_PRO_RATE_LIMIT"
  "SUBSCRIPTION_TIER_ENTERPRISE_RATE_LIMIT"
  "IPFS_HOST"
  "IPFS_PORT"
  "IPFS_API_URL"
  "IPFS_GATEWAY_URL"
  "JWT_ALGORITHM"
  "ALGORITHM"
  "ACCESS_TOKEN_EXPIRE_MINUTES"
  "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
)

is_skip() {
  local v="$1"
  for skip in "${SKIP_VARS[@]}"; do
    [[ "$v" == "$skip" ]] && return 0
  done
  return 1
}

# ---------------------------------------------------------------------------
# Parse .env and push secrets
# ---------------------------------------------------------------------------

log "Pushing secrets to $REPO…"
echo

PUSHED=0
SKIPPED=0
EMPTY=0

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line// }" ]] && continue
  [[ "$line" != *"="* ]] && continue

  VAR="${line%%=*}"
  VAL="${line#*=}"

  if [[ -z "$VAL" ]]; then
    warn "  SKIP (empty): $VAR"
    ((EMPTY++)) || true
    continue
  fi

  if is_skip "$VAR"; then
    log "  SKIP (not needed in CI): $VAR"
    ((SKIPPED++)) || true
    continue
  fi

  if echo -n "$VAL" | gh secret set "$VAR" --repo "$REPO" 2>/dev/null; then
    ok "  SECRET SET: $VAR"
    ((PUSHED++)) || true
  else
    err "  FAILED: $VAR — check gh permissions (need 'repo' scope)"
  fi

done < "$ENV_FILE"

echo
ok "GitHub secrets push complete — ${PUSHED} set, ${SKIPPED} skipped, ${EMPTY} empty."
log "View at: https://github.com/$REPO/settings/secrets/actions"
