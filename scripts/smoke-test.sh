#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# The smoke test. It makes a check of each endpoint against a running stack.
#
#   ./scripts/smoke-test.sh http://localhost:8000
# ---------------------------------------------------------------------------
set -euo pipefail

BASE="${1:-http://localhost:8000}"
SKU="SMOKE-$(date +%s)"
PASS=0
FAIL=0

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  PASS  $label (HTTP $actual)"
    PASS=$(( PASS + 1 ))
  else
    echo "  FAIL  $label (expected $expected, got $actual)"
    FAIL=$(( FAIL + 1 ))
  fi
}

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

echo "Smoke test against $BASE"

check "GET /health"  200 "$(code "$BASE/health")"
check "GET /ready"   200 "$(code "$BASE/ready")"
check "GET /metrics" 200 "$(code "$BASE/metrics")"
check "GET /api/items" 200 "$(code "$BASE/api/items")"
check "GET /api/items/stats" 200 "$(code "$BASE/api/items/stats")"

ID=$(curl -fsS -X POST "$BASE/api/items" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Smoke test item\",\"sku\":\"$SKU\",\"quantity\":10,\"unit_price\":1.5,\"reorder_level\":2}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  PASS  POST /api/items (id $ID)"
PASS=$(( PASS + 1 ))

check "GET /api/items/$ID" 200 "$(code "$BASE/api/items/$ID")"
check "PUT /api/items/$ID" 200 "$(code -X PUT "$BASE/api/items/$ID" -H 'Content-Type: application/json' -d '{"quantity":1}')"
check "DELETE /api/items/$ID" 204 "$(code -X DELETE "$BASE/api/items/$ID")"
check "GET deleted item" 404 "$(code "$BASE/api/items/$ID")"

echo
echo "Pass: $PASS   Fail: $FAIL"
[ "$FAIL" -eq 0 ]
