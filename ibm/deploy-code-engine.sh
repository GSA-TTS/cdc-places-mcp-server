#!/usr/bin/env bash
# Deploy an MCP server to IBM Cloud Code Engine.
#
# Two deploy paths (selected by ibm/.env):
#
#   Path A (default) — build from a public Git repo, SERVER-SIDE.
#     Code Engine clones GIT_REPO_URL and builds its Dockerfile for you. No
#     local Docker, no registry, no push. This is the cloud.gov-like,
#     plug-and-play path: point GIT_REPO_URL at your public fork and run.
#
#   Path B (override) — deploy a prebuilt public image.
#     If IMAGE is set in ibm/.env, that image is deployed directly and the Git
#     vars are ignored. Use for a pinned, reproducible release.
#
# The container serves MCP over streamable-HTTP at :$CE_PORT/mcp with a health
# check at :$CE_PORT/health.
#
# Prerequisites:
#   - IBM Cloud CLI: https://cloud.ibm.com/docs/cli
#   - Code Engine plugin: `ibmcloud plugin install code-engine`
#   - Logged in:          `ibmcloud login --sso`
#   - Config:             `cp ibm/.env.example ibm/.env` && edit && `source ibm/.env`
#
# Usage:
#   source ibm/.env
#   bash ibm/deploy-code-engine.sh
#
# Idempotent: creates the app on first run, updates it on subsequent runs.
set -euo pipefail

# --- Validate common config ---------------------------------------------------
: "${IBMCLOUD_REGION:?set IBMCLOUD_REGION (source ibm/.env)}"
: "${IBMCLOUD_RESOURCE_GROUP:?set IBMCLOUD_RESOURCE_GROUP}"
: "${CE_PROJECT:?set CE_PROJECT}"
: "${CE_APP_NAME:?set CE_APP_NAME}"
: "${CE_PORT:?set CE_PORT}"

# --- Decide deploy path -------------------------------------------------------
# IMAGE set (non-empty) => Path B. Otherwise => Path A (Git build).
IMAGE="${IMAGE:-}"
if [[ -n "${IMAGE}" ]]; then
  DEPLOY_MODE="image"
else
  DEPLOY_MODE="git"
  : "${GIT_REPO_URL:?Path A requires GIT_REPO_URL (or set IMAGE for Path B)}"
  GIT_BRANCH="${GIT_BRANCH:-main}"
  GIT_CONTEXT_DIR="${GIT_CONTEXT_DIR:-.}"
  GIT_DOCKERFILE="${GIT_DOCKERFILE:-Dockerfile}"
fi

echo "=== Target ==="
echo "  region:         ${IBMCLOUD_REGION}"
echo "  resource group: ${IBMCLOUD_RESOURCE_GROUP}"
echo "  project:        ${CE_PROJECT}"
echo "  app:            ${CE_APP_NAME}"
echo "  port:           ${CE_PORT}"
echo "  deploy mode:    ${DEPLOY_MODE}"
if [[ "${DEPLOY_MODE}" == "git" ]]; then
  echo "  git repo:       ${GIT_REPO_URL}"
  echo "  git branch:     ${GIT_BRANCH}"
  echo "  context dir:    ${GIT_CONTEXT_DIR}"
  echo "  dockerfile:     ${GIT_DOCKERFILE}"
else
  echo "  image:          ${IMAGE}"
fi
echo ""

# --- Confirm we are logged in -------------------------------------------------
if ! ibmcloud target >/dev/null 2>&1; then
  echo "FATAL: not logged in. Run 'ibmcloud login --sso' first." >&2
  exit 1
fi

# --- Select region + resource group ------------------------------------------
echo "=== Targeting region + resource group ==="
ibmcloud target -r "${IBMCLOUD_REGION}" -g "${IBMCLOUD_RESOURCE_GROUP}"

# --- Ensure the Code Engine project exists and is selected --------------------
echo "=== Selecting Code Engine project '${CE_PROJECT}' ==="
if ibmcloud ce project select --name "${CE_PROJECT}" >/dev/null 2>&1; then
  echo "  project exists — selected."
else
  echo "  project not found — creating '${CE_PROJECT}'..."
  ibmcloud ce project create --name "${CE_PROJECT}"
  ibmcloud ce project select --name "${CE_PROJECT}"
fi

# --- Build the mode-specific source args --------------------------------------
# Path A: --build-source (+ branch/context/dockerfile). Code Engine runs the
#         build server-side and deploys the resulting image.
# Path B: --image, deploying the prebuilt public image directly.
SOURCE_ARGS=()
if [[ "${DEPLOY_MODE}" == "git" ]]; then
  SOURCE_ARGS=(
    --build-source "${GIT_REPO_URL}"
    --build-commit "${GIT_BRANCH}"
    --build-context-dir "${GIT_CONTEXT_DIR}"
    --build-dockerfile "${GIT_DOCKERFILE}"
    --build-strategy dockerfile
  )
else
  SOURCE_ARGS=(--image "${IMAGE}")
fi

# --- Create or update the application ----------------------------------------
# --port          : container listen port (health checks + traffic routed here)
# --min-scale 1   : keep one instance warm so the eval agent never hits a cold
#                   start mid-experiment (Code Engine scales to zero by default)
# --cpu / --memory: modest sizing; the server is I/O-bound (CDC API calls)
COMMON_ARGS=(
  --name "${CE_APP_NAME}"
  --port "${CE_PORT}"
  --min-scale 1
  --cpu 0.5
  --memory 1G
)

if ibmcloud ce app get --name "${CE_APP_NAME}" >/dev/null 2>&1; then
  echo "=== Updating existing app '${CE_APP_NAME}' (${DEPLOY_MODE} mode) ==="
  ibmcloud ce app update "${COMMON_ARGS[@]}" "${SOURCE_ARGS[@]}"
else
  echo "=== Creating app '${CE_APP_NAME}' (${DEPLOY_MODE} mode) ==="
  # In git mode this triggers a server-side build first, which can take a few
  # minutes on the first run; the CLI streams build + deploy progress.
  ibmcloud ce app create "${COMMON_ARGS[@]}" "${SOURCE_ARGS[@]}"
fi

# --- Report the public URL ----------------------------------------------------
APP_URL="$(ibmcloud ce app get --name "${CE_APP_NAME}" --output url)"
echo ""
echo "=== Deployed ==="
echo "  App URL:      ${APP_URL}"
echo "  MCP endpoint: ${APP_URL}/mcp"
echo "  Health:       ${APP_URL}/health"
echo ""
echo "Verify with:"
echo "  bash ibm/smoke-test.sh ${APP_URL}"
