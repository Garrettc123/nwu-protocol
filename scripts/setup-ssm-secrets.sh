#!/usr/bin/env bash
# Store all nwu-protocol production secrets into AWS SSM Parameter Store.
# Run once from your local machine (never in CI).
# Prerequisites: aws cli configured, pip install boto3 botocore
set -euo pipefail

export AWS_REGION="${AWS_REGION:-us-east-1}"
export SECRETOPS_PREFIX="${SECRETOPS_PREFIX:-/garcar}"
export SECRETOPS_ENV="${SECRETOPS_ENV:-prod}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETOPS="$SCRIPT_DIR/secretops.py"

echo "=== NWU Protocol — SSM Secret Setup ==="
echo "Region:  $AWS_REGION"
echo "Prefix:  $SECRETOPS_PREFIX"
echo "Env:     $SECRETOPS_ENV"
echo "Service: nwu-protocol"
echo ""
echo "You will be prompted for each secret. Values will not echo."
echo ""

store() {
  local key="$1"
  local prompt="${2:-$key}"
  echo -n "[$prompt]: "
  python "$SECRETOPS" \
    --prefix "$SECRETOPS_PREFIX" \
    --env    "$SECRETOPS_ENV" \
    --service nwu-protocol \
    put "$key" --stdin < /dev/tty || {
      printf "\nSkipping %s\n" "$key"
    }
}

store STRIPE_API_KEY         "Stripe Secret Key (sk_live_...)"
store STRIPE_WEBHOOK_SECRET  "Stripe Webhook Secret (whsec_...)"
store STRIPE_PUBLISHABLE_KEY "Stripe Publishable Key (pk_live_...)"
store STRIPE_PRICE_ID_PRO    "Stripe Pro Price ID (price_...)"
store STRIPE_PRICE_ID_ENTERPRISE "Stripe Enterprise Price ID (price_...)"
store DATABASE_URL           "PostgreSQL DATABASE_URL"
store REDIS_URL              "Redis URL"
store JWT_SECRET_KEY         "JWT Secret Key (random string)"

echo ""
echo "=== Auditing stored secrets ==="
python "$SECRETOPS" \
  --prefix "$SECRETOPS_PREFIX" \
  --env    "$SECRETOPS_ENV" \
  --service nwu-protocol \
  list

echo ""
echo "Done. Set these GitHub repo variables (non-sensitive):"
echo "  AWS_REGION=$AWS_REGION"
echo "  AWS_ROLE_ARN=<from: cd terraform/aws-github-oidc && terraform output role_arn>"
echo "  SECRETOPS_PREFIX=$SECRETOPS_PREFIX"
echo "  SECRETOPS_ENV=$SECRETOPS_ENV"
echo "  NEXT_PUBLIC_API_URL=https://your-backend.railway.app"
echo "  NEXT_PUBLIC_APP_URL=https://your-frontend.vercel.app"
