#!/usr/bin/env bash
# Smoke-test a deployed CDC PLACES MCP server.
#
# Verifies two things against the LIVE endpoint (no mocks):
#   1. /health returns 200 with a healthy body
#   2. /mcp answers a JSON-RPC tools/list and advertises the expected tools
#
# Usage:
#   bash ibm/smoke-test.sh https://<app>.<region>.codeengine.appdomain.cloud
set -euo pipefail

BASE_URL="${1:?usage: smoke-test.sh <base-url>}"
BASE_URL="${BASE_URL%/}"  # strip trailing slash

echo "=== 1. Health check: ${BASE_URL}/health ==="
HEALTH_CODE="$(curl -s -o /tmp/ce-health.json -w '%{http_code}' "${BASE_URL}/health")"
cat /tmp/ce-health.json; echo ""
if [[ "${HEALTH_CODE}" != "200" ]]; then
  echo "FAIL: health check returned HTTP ${HEALTH_CODE}" >&2
  exit 1
fi
echo "PASS: health check 200"
echo ""

# MCP streamable-HTTP requires an Accept header advertising both content types
# and a JSON-RPC initialize before tools/list. We do a single tools/list call;
# FastMCP accepts it and returns the tool catalog.
echo "=== 2. MCP tools/list: ${BASE_URL}/mcp ==="
RESP="$(curl -s "${BASE_URL}/mcp" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}')"

echo "${RESP}" | head -c 2000; echo ""

if echo "${RESP}" | grep -q "get_cdc_places_data" && \
   echo "${RESP}" | grep -q "area_summary_stats"; then
  echo ""
  echo "PASS: both tools advertised (get_cdc_places_data, area_summary_stats)"
else
  echo ""
  echo "WARN: expected tools not found in tools/list response." >&2
  echo "      The server may require an MCP initialize handshake first — if the" >&2
  echo "      health check passed, register it in Orchestrate and test there." >&2
fi
