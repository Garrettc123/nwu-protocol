#!/usr/bin/env bash
# validate_business_agents.sh
# Validates the Business Cooperation Lead Agent system against a running backend.
#
# Usage:
#   ./validate_business_agents.sh [BASE_URL]
#
# Examples:
#   ./validate_business_agents.sh
#   ./validate_business_agents.sh http://localhost:8000

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0
CREATED_AGENT_ID=""
CREATED_TASK_ID=""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

green() { printf "\033[0;32m%s\033[0m\n" "$*"; }
red()   { printf "\033[0;31m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[0;33m%s\033[0m\n" "$*"; }

check() {
    local description="$1"
    local expected_status="$2"
    local actual_status="$3"
    local body="$4"

    if [ "$actual_status" = "$expected_status" ]; then
        green "  ✓ $description (HTTP $actual_status)"
        PASS=$((PASS + 1))
    else
        red "  ✗ $description — expected HTTP $expected_status, got $actual_status"
        red "    Response: $body"
        FAIL=$((FAIL + 1))
    fi
}

http_get() {
    curl -s -o /tmp/bav_body -w "%{http_code}" "$BASE_URL$1"
}

http_post() {
    curl -s -o /tmp/bav_body -w "%{http_code}" \
        -X POST -H "Content-Type: application/json" \
        -d "$2" "$BASE_URL$1"
}

http_patch() {
    curl -s -o /tmp/bav_body -w "%{http_code}" \
        -X PATCH -H "Content-Type: application/json" \
        -d "$2" "$BASE_URL$1"
}

http_delete() {
    curl -s -o /tmp/bav_body -w "%{http_code}" \
        -X DELETE "$BASE_URL$1"
}

body() { cat /tmp/bav_body 2>/dev/null || echo ""; }

json_field() {
    # $1 = field name, $2 = json string
    echo "$2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$1',''))" 2>/dev/null || echo ""
}

# ---------------------------------------------------------------------------
# 1. Backend health
# ---------------------------------------------------------------------------

echo ""
yellow "=== 1. Backend Health ==="

status=$(http_get "/health")
check "GET /health" "200" "$status" "$(body)"

# ---------------------------------------------------------------------------
# 2. Business Agents — list (empty baseline)
# ---------------------------------------------------------------------------

echo ""
yellow "=== 2. Business Agents — List ==="

status=$(http_get "/api/v1/business-agents/")
check "GET /api/v1/business-agents/ (list)" "200" "$status" "$(body)"

# ---------------------------------------------------------------------------
# 3. Business Agents — create one per type
# ---------------------------------------------------------------------------

echo ""
yellow "=== 3. Business Agents — Create (all 12 types) ==="

AGENT_TYPES=(
    sales marketing operations finance customer_service
    research development qa hr legal strategy project_management
)

for agent_type in "${AGENT_TYPES[@]}"; do
    payload="{\"agent_type\": \"$agent_type\", \"name\": \"Test $agent_type agent\"}"
    status=$(http_post "/api/v1/business-agents/" "$payload")
    check "POST /api/v1/business-agents/ (type=$agent_type)" "201" "$status" "$(body)"
    # Keep the last created agent_id for subsequent tests
    CREATED_AGENT_ID=$(json_field "agent_id" "$(body)")
done

# ---------------------------------------------------------------------------
# 4. Business Agents — get by ID
# ---------------------------------------------------------------------------

echo ""
yellow "=== 4. Business Agents — Get by ID ==="

if [ -n "$CREATED_AGENT_ID" ]; then
    status=$(http_get "/api/v1/business-agents/$CREATED_AGENT_ID")
    check "GET /api/v1/business-agents/$CREATED_AGENT_ID" "200" "$status" "$(body)"
else
    red "  ✗ Skipped get-by-id — no agent was created successfully"
    FAIL=$((FAIL + 1))
fi

# ---------------------------------------------------------------------------
# 5. Business Agents — update
# ---------------------------------------------------------------------------

echo ""
yellow "=== 5. Business Agents — Update ==="

if [ -n "$CREATED_AGENT_ID" ]; then
    payload='{"status": "active", "name": "Updated Agent Name"}'
    status=$(http_patch "/api/v1/business-agents/$CREATED_AGENT_ID" "$payload")
    check "PATCH /api/v1/business-agents/$CREATED_AGENT_ID" "200" "$status" "$(body)"
fi

# ---------------------------------------------------------------------------
# 6. Business Agents — filter by type
# ---------------------------------------------------------------------------

echo ""
yellow "=== 6. Business Agents — Filter by type ==="

status=$(http_get "/api/v1/business-agents/?agent_type=sales")
check "GET /api/v1/business-agents/?agent_type=sales" "200" "$status" "$(body)"

status=$(http_get "/api/v1/business-agents/?agent_type=invalid_type")
check "GET /api/v1/business-agents/?agent_type=invalid_type (expect 400)" "400" "$status" "$(body)"

# ---------------------------------------------------------------------------
# 7. Business Tasks — list (empty baseline)
# ---------------------------------------------------------------------------

echo ""
yellow "=== 7. Business Tasks — List ==="

status=$(http_get "/api/v1/business-tasks/")
check "GET /api/v1/business-tasks/ (list)" "200" "$status" "$(body)"

# ---------------------------------------------------------------------------
# 8. Business Tasks — create
# ---------------------------------------------------------------------------

echo ""
yellow "=== 8. Business Tasks — Create ==="

payload='{
  "title": "Qualify Acme Corp lead",
  "task_type": "qualify_lead",
  "required_agent_type": "sales",
  "priority": 2,
  "task_data": {"lead_id": "lead-001", "company": "Acme Corp", "lead_score": 78},
  "max_retries": 2
}'
status=$(http_post "/api/v1/business-tasks/" "$payload")
check "POST /api/v1/business-tasks/ (sales task)" "201" "$status" "$(body)"
CREATED_TASK_ID=$(json_field "task_id" "$(body)")

# Create tasks for several other types
for task_type in "plan_campaign" "review_contract" "plan_sprint"; do
    payload="{\"title\": \"Test $task_type\", \"task_type\": \"$task_type\", \"priority\": 5}"
    status=$(http_post "/api/v1/business-tasks/" "$payload")
    check "POST /api/v1/business-tasks/ (type=$task_type)" "201" "$status" "$(body)"
done

# ---------------------------------------------------------------------------
# 9. Business Tasks — get by ID
# ---------------------------------------------------------------------------

echo ""
yellow "=== 9. Business Tasks — Get by ID ==="

if [ -n "$CREATED_TASK_ID" ]; then
    status=$(http_get "/api/v1/business-tasks/$CREATED_TASK_ID")
    check "GET /api/v1/business-tasks/$CREATED_TASK_ID" "200" "$status" "$(body)"
else
    red "  ✗ Skipped get-by-id — no task was created successfully"
    FAIL=$((FAIL + 1))
fi

# ---------------------------------------------------------------------------
# 10. Business Tasks — update
# ---------------------------------------------------------------------------

echo ""
yellow "=== 10. Business Tasks — Update ==="

if [ -n "$CREATED_TASK_ID" ]; then
    payload='{"status": "in_progress"}'
    status=$(http_patch "/api/v1/business-tasks/$CREATED_TASK_ID" "$payload")
    check "PATCH /api/v1/business-tasks/$CREATED_TASK_ID (in_progress)" "200" "$status" "$(body)"

    payload='{"status": "completed", "result_data": {"score": 92}}'
    status=$(http_patch "/api/v1/business-tasks/$CREATED_TASK_ID" "$payload")
    check "PATCH /api/v1/business-tasks/$CREATED_TASK_ID (completed)" "200" "$status" "$(body)"
fi

# ---------------------------------------------------------------------------
# 11. Business Tasks — delegate
# ---------------------------------------------------------------------------

echo ""
yellow "=== 11. Business Tasks — Delegate ==="

# Create a fresh queued task to delegate
payload='{"title": "Task to delegate", "task_type": "qualify_lead", "required_agent_type": "sales", "priority": 3}'
status=$(http_post "/api/v1/business-tasks/" "$payload")
DELEGATE_TASK_ID=$(json_field "task_id" "$(body)")

# Find a sales agent to delegate to
status=$(http_get "/api/v1/business-agents/?agent_type=sales&limit=1")
SALES_AGENT_ID=$(body | python3 -c "import sys,json; agents=json.load(sys.stdin); print(agents[0]['agent_id'] if agents else '')" 2>/dev/null || echo "")

if [ -n "$DELEGATE_TASK_ID" ] && [ -n "$SALES_AGENT_ID" ]; then
    status=$(http_post "/api/v1/business-tasks/$DELEGATE_TASK_ID/delegate" "{\"agent_id\": \"$SALES_AGENT_ID\"}")
    check "POST /api/v1/business-tasks/$DELEGATE_TASK_ID/delegate" "200" "$status" "$(body)"
else
    yellow "  ⚠ Skipped delegation test (task_id='$DELEGATE_TASK_ID', agent_id='$SALES_AGENT_ID')"
fi

# ---------------------------------------------------------------------------
# 12. Business Tasks — cancel
# ---------------------------------------------------------------------------

echo ""
yellow "=== 12. Business Tasks — Cancel ==="

# Create a fresh queued task to cancel
payload='{"title": "Task to cancel", "task_type": "generic_task", "priority": 10}'
status=$(http_post "/api/v1/business-tasks/" "$payload")
CANCEL_TASK_ID=$(json_field "task_id" "$(body)")

if [ -n "$CANCEL_TASK_ID" ]; then
    status=$(http_delete "/api/v1/business-tasks/$CANCEL_TASK_ID")
    check "DELETE /api/v1/business-tasks/$CANCEL_TASK_ID (cancel)" "204" "$status" "$(body)"
fi

# ---------------------------------------------------------------------------
# 13. Business Agents — terminate
# ---------------------------------------------------------------------------

echo ""
yellow "=== 13. Business Agents — Terminate ==="

if [ -n "$CREATED_AGENT_ID" ]; then
    status=$(http_delete "/api/v1/business-agents/$CREATED_AGENT_ID")
    check "DELETE /api/v1/business-agents/$CREATED_AGENT_ID (terminate)" "204" "$status" "$(body)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "========================================"
TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    green "All $TOTAL checks passed ✓"
else
    red "$FAIL of $TOTAL checks failed"
fi
echo "========================================"

[ $FAIL -eq 0 ] && exit 0 || exit 1
