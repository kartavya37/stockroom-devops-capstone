#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# A simple load generator. It makes CPU pressure on the backend.
# The HPA then increases the number of Pods.
#
#   ./scripts/load-test.sh http://localhost:8000 60 20
#     argument 1: the address of the backend  (default: http://localhost:8000)
#     argument 2: the duration in seconds     (default: 60)
#     argument 3: the number of workers       (default: 20)
#
# Watch the result in a second terminal:
#   kubectl get hpa -n stockroom --watch
# ---------------------------------------------------------------------------
set -euo pipefail

TARGET="${1:-http://localhost:8000}"
DURATION="${2:-60}"
WORKERS="${3:-20}"

echo "Target:   $TARGET"
echo "Duration: ${DURATION}s"
echo "Workers:  $WORKERS"
echo

if ! curl -fsS "${TARGET}/health" >/dev/null; then
  echo "ERROR: the backend does not answer at ${TARGET}/health" >&2
  exit 1
fi

END=$(( $(date +%s) + DURATION ))

worker() {
  local count=0
  while [ "$(date +%s)" -lt "$END" ]; do
    curl -fsS "${TARGET}/api/items/stats" >/dev/null 2>&1 || true
    curl -fsS "${TARGET}/api/items" >/dev/null 2>&1 || true
    count=$(( count + 2 ))
  done
  echo "$count"
}

for _ in $(seq 1 "$WORKERS"); do
  worker &
done

wait
echo
echo "The load test is complete. Look at the autoscaler:"
echo "  kubectl get hpa -n stockroom"
echo "  kubectl get pods -n stockroom"
