#!/usr/bin/env bash
# Deploy this MCP server to Databricks Apps.
#
# Flow:
#   1. Ensure the Databricks App exists (create-or-reuse).
#   2. Sync the repo source to a workspace path (SOURCE_CODE_PATH).
#   3. `databricks apps deploy` from that path.
#
# Databricks builds a container from the synced source + app.yaml, injects
# DATABRICKS_APP_PORT at runtime, and app.py serves MCP over streamable-HTTP at
# :$DATABRICKS_APP_PORT/mcp with a health check at /health.
#
# Prerequisites:
#   - Databricks CLI (v0.205+):  https://docs.databricks.com/dev-tools/cli/install.html
#   - Authenticated:             databricks auth login --host <workspace-url>
#                                (or a configured profile / DATABRICKS_TOKEN)
#   - Apps enabled on your workspace.
#   - Config:                    cp .env.example .env && edit
#
# Usage:
#   set -a; source deploy/databricks/.env; set +a
#   bash deploy/databricks/deploy-databricks-app.sh
#
# Idempotent: creates the app on first run, redeploys on subsequent runs.
set -euo pipefail

# --- Validate config ----------------------------------------------------------
: "${APP_NAME:?set APP_NAME (source deploy/databricks/.env)}"
: "${SOURCE_CODE_PATH:?set SOURCE_CODE_PATH (absolute /Workspace path)}"

# Optional passthroughs to the CLI.
PROFILE_ARGS=()
if [[ -n "${DATABRICKS_CONFIG_PROFILE:-}" ]]; then
  PROFILE_ARGS=(--profile "${DATABRICKS_CONFIG_PROFILE}")
fi
if [[ -n "${DATABRICKS_HOST:-}" ]]; then
  export DATABRICKS_HOST
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Target ==="
echo "  app name:         ${APP_NAME}"
echo "  source code path: ${SOURCE_CODE_PATH}"
echo "  profile:          ${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
echo "  repo root:        ${REPO_ROOT}"
echo ""

# --- Confirm the CLI is installed and authenticated ---------------------------
if ! command -v databricks >/dev/null 2>&1; then
  echo "FATAL: 'databricks' CLI not found." >&2
  echo "       Install: https://docs.databricks.com/dev-tools/cli/install.html" >&2
  exit 1
fi
if ! databricks "${PROFILE_ARGS[@]}" current-user me >/dev/null 2>&1; then
  echo "FATAL: not authenticated. Run:" >&2
  echo "       databricks auth login --host <workspace-url>" >&2
  exit 1
fi

# --- app.yaml must sit at the source root Databricks deploys from -------------
# Databricks Apps reads app.yaml from the deployed source directory. We keep the
# canonical copy in this kit and stage it at the repo root for the sync so the
# deploy sees it without polluting the repo. (Removed after deploy.)
STAGED_APP_YAML="${REPO_ROOT}/app.yaml"
CLEANUP_APP_YAML=0
if [[ ! -f "${STAGED_APP_YAML}" ]]; then
  cp "${SCRIPT_DIR}/app.yaml" "${STAGED_APP_YAML}"
  CLEANUP_APP_YAML=1
fi
cleanup() {
  if [[ "${CLEANUP_APP_YAML}" == "1" ]]; then
    rm -f "${STAGED_APP_YAML}"
  fi
}
trap cleanup EXIT

# --- Ensure the app exists (create-or-reuse) ----------------------------------
echo "=== Ensuring Databricks App '${APP_NAME}' ==="
if databricks "${PROFILE_ARGS[@]}" apps get "${APP_NAME}" >/dev/null 2>&1; then
  echo "  app exists — reusing."
else
  echo "  app not found — creating '${APP_NAME}'..."
  databricks "${PROFILE_ARGS[@]}" apps create "${APP_NAME}"
fi

# --- Sync the repo source to the workspace path -------------------------------
# `databricks sync` uploads the repo (respecting .gitignore) to SOURCE_CODE_PATH.
echo "=== Syncing source to ${SOURCE_CODE_PATH} ==="
databricks "${PROFILE_ARGS[@]}" sync "${REPO_ROOT}" "${SOURCE_CODE_PATH}"

# --- Deploy -------------------------------------------------------------------
echo "=== Deploying app '${APP_NAME}' from ${SOURCE_CODE_PATH} ==="
databricks "${PROFILE_ARGS[@]}" apps deploy "${APP_NAME}" \
  --source-code-path "${SOURCE_CODE_PATH}"

# --- Report the app URL -------------------------------------------------------
APP_URL="$(databricks "${PROFILE_ARGS[@]}" apps get "${APP_NAME}" \
  --output json 2>/dev/null | grep -o '"url"[^,]*' | head -1 | cut -d'"' -f4 || true)"
echo ""
echo "=== Deployed ==="
if [[ -n "${APP_URL}" ]]; then
  echo "  App URL:      ${APP_URL}"
  echo "  MCP endpoint: ${APP_URL}/mcp"
  echo "  Health:       ${APP_URL}/health"
  echo ""
  echo "Verify with:"
  echo "  bash deploy/databricks/smoke-test.sh ${APP_URL}"
else
  echo "  Deployed. Get the URL with:"
  echo "    databricks ${PROFILE_ARGS[*]} apps get ${APP_NAME}"
fi
