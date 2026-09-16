#!/usr/bin/env bash
# Smoke-test a deployed Databricks Apps MCP server.
#
# IMPORTANT: Databricks Apps sit behind the workspace's OAuth/SSO by default, so
# an unauthenticated curl to /health or /mcp will usually get a 302 redirect to
# a login page or a 401 — that is EXPECTED, not a server failure. To hit the app
# programmatically you must send a bearer token.
#
# Usage:
#   # Unauthenticated reachability check (expects 302/401 for a private app):
#   bash deploy/databricks/smoke-test.sh https://<app-url>
#
#   # Authenticated check (recommended) — pass a token that can access the app:
#   DATABRICKS_TOKEN="$(databricks auth token --output json | jq -r .access_token)" \
#     bash deploy/databricks/smoke-test.sh https://<app-url>
set -euo pipefail

BASE_URL="${1:?usage: smoke-test.sh <base-url>}"
BASE_URL="${BASE_URL%/}"

AUTH_ARGS=()
if [[ -n "${DATABRICKS_TOKEN:-}" ]]; then
  AUTH_ARGS=(-H "Authorization: Bearer ${DATABRICKS_TOKEN}")
  echo "(using DATABRICKS_TOKEN for authenticated requests)"
else
  echo "(no DATABRICKS_TOKEN set — a private app will return 302/401, which is expected)"
fi
echo ""

echo "=== 1. Health check: ${BASE_URL}/health ==="
HEALTH_CODE="$(curl -s -o /tmp/dbx-health.json -w '%{http_code}' ${AUTH_ARGS[@]+"${AUTH_ARGS[@]}"} "${BASE_URL}/health" || true)"
cat /tmp/dbx-health.json 2>/dev/null; echo ""
case "${HEALTH_CODE}" in
  200)
    echo "PASS: health check 200"
    ;;
  302 | 401 | 403)
    echo "INFO: HTTP ${HEALTH_CODE} — app is up but requires auth (expected for a"
    echo "      private Databricks App). Re-run with DATABRICKS_TOKEN to verify the"
    echo "      body, or test from an authenticated client."
    ;;
  *)
    echo "WARN: unexpected HTTP ${HEALTH_CODE} from /health." >&2
    ;;
esac
echo ""

echo "=== 2. MCP endpoint: ${BASE_URL}/mcp ==="
MCP_CODE="$(curl -s -o /tmp/dbx-mcp.txt -w '%{http_code}' ${AUTH_ARGS[@]+"${AUTH_ARGS[@]}"} \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  "${BASE_URL}/mcp" || true)"
head -c 2000 /tmp/dbx-mcp.txt 2>/dev/null; echo ""
echo "HTTP ${MCP_CODE}"
echo ""
echo "Notes:"
echo "  - 302/401/403 → app is up but auth-gated (expected without a token)."
echo "  - A 'Missing session ID' JSON-RPC error with a token → the transport is"
echo "    reachable; a real MCP client does the initialize handshake first."
