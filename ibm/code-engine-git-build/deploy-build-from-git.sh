#!/usr/bin/env bash
# Deploy an MCP server to IBM Cloud Code Engine by BUILDING FROM A GIT REPO.
#
# Flow (all server-side — no local Docker):
#   1. Ensure an IBM Container Registry (ICR) namespace exists (create-or-reuse).
#   2. Create a Code Engine registry-access secret from an IBM Cloud API key so
#      Code Engine can PUSH the built image to that namespace.
#   3. Ensure the Code Engine project exists and is selected.
#   4. `ce app create/update --build-source <git> --image <icr-ref>
#      --registry-secret <secret>`: Code Engine clones the repo, builds the
#      Dockerfile, pushes the image to ICR, then deploys it.
#
# The container serves MCP over streamable-HTTP at :$CE_PORT/mcp with a health
# check at :$CE_PORT/health.
#
# This is the "build from Git" counterpart to ../prebuilt-image/. It requires
# IBM Container Registry authority (namespace create/write + an API key to make
# the registry secret) — the authority the original trial account lacked.
#
# Prerequisites:
#   - IBM Cloud CLI:            https://cloud.ibm.com/docs/cli
#   - Code Engine plugin:       ibmcloud plugin install code-engine
#   - Container Registry plugin: ibmcloud plugin install container-registry
#   - Logged in:                ibmcloud login --sso   (or --apikey)
#   - Config:                   cp .env.example .env && edit && source .env
#
# Usage:
#   source ibm/code-engine-git-build/.env
#   # optional (else you'll be prompted, input hidden):
#   #   export IBMCLOUD_API_KEY="$(ibmcloud iam api-key-create ce-icr-push \
#   #       -d 'Code Engine ICR push' --output json | jq -r .apikey)"
#   bash ibm/code-engine-git-build/deploy-build-from-git.sh
#
# Idempotent: creates namespace/secret/app on first run, updates on later runs.
set -euo pipefail

# --- Validate config ----------------------------------------------------------
: "${IBMCLOUD_REGION:?set IBMCLOUD_REGION (source ibm/code-engine-git-build/.env)}"
: "${IBMCLOUD_RESOURCE_GROUP:?set IBMCLOUD_RESOURCE_GROUP}"
: "${CE_PROJECT:?set CE_PROJECT}"
: "${CE_APP_NAME:?set CE_APP_NAME}"
: "${CE_PORT:?set CE_PORT}"
: "${GIT_REPO_URL:?set GIT_REPO_URL (public repo to build)}"
: "${ICR_REGION:?set ICR_REGION}"
: "${ICR_DOMAIN:?set ICR_DOMAIN (e.g. us.icr.io)}"
: "${ICR_NAMESPACE:?set ICR_NAMESPACE}"
: "${IMAGE_TAG:?set IMAGE_TAG}"
: "${CE_REGISTRY_SECRET:?set CE_REGISTRY_SECRET}"

GIT_BRANCH="${GIT_BRANCH:-main}"
GIT_CONTEXT_DIR="${GIT_CONTEXT_DIR:-.}"
GIT_DOCKERFILE="${GIT_DOCKERFILE:-Dockerfile}"

IMAGE_REF="${ICR_DOMAIN}/${ICR_NAMESPACE}/${CE_APP_NAME}:${IMAGE_TAG}"

echo "=== Target ==="
echo "  region:          ${IBMCLOUD_REGION}"
echo "  resource group:  ${IBMCLOUD_RESOURCE_GROUP}"
echo "  project:         ${CE_PROJECT}"
echo "  app:             ${CE_APP_NAME}"
echo "  port:            ${CE_PORT}"
echo "  git repo:        ${GIT_REPO_URL}"
echo "  git branch:      ${GIT_BRANCH}"
echo "  context dir:     ${GIT_CONTEXT_DIR}"
echo "  dockerfile:      ${GIT_DOCKERFILE}"
echo "  image (ICR):     ${IMAGE_REF}"
echo "  registry secret: ${CE_REGISTRY_SECRET}"
echo ""

# --- Confirm we are logged in -------------------------------------------------
if ! ibmcloud target >/dev/null 2>&1; then
  echo "FATAL: not logged in. Run 'ibmcloud login --sso' first." >&2
  exit 1
fi

# --- Select region + resource group ------------------------------------------
echo "=== Targeting region + resource group ==="
ibmcloud target -r "${IBMCLOUD_REGION}" -g "${IBMCLOUD_RESOURCE_GROUP}"

# --- Obtain the API key used for the registry secret --------------------------
# Prefer IBMCLOUD_API_KEY from the environment; otherwise prompt (hidden input).
# NEVER written to disk.
API_KEY="${IBMCLOUD_API_KEY:-}"
if [[ -z "${API_KEY}" ]]; then
  echo "=== IBM Cloud API key (for ICR push secret) ==="
  echo "  IBMCLOUD_API_KEY is not set. Enter an IBM Cloud API key with ICR write"
  echo "  access (input hidden). Create one with:"
  echo "    ibmcloud iam api-key-create ce-icr-push -d 'Code Engine ICR push'"
  read -r -s -p "  IBM Cloud API key: " API_KEY
  echo ""
  if [[ -z "${API_KEY}" ]]; then
    echo "FATAL: no API key provided; cannot create the registry secret." >&2
    exit 1
  fi
fi

# --- Ensure the ICR namespace exists (create-or-reuse) ------------------------
echo "=== Ensuring ICR namespace '${ICR_NAMESPACE}' in region '${ICR_REGION}' ==="
ibmcloud cr region-set "${ICR_REGION}" >/dev/null
if ibmcloud cr namespace-list --output json 2>/dev/null | grep -q "\"${ICR_NAMESPACE}\""; then
  echo "  namespace exists — reusing."
else
  echo "  namespace not found — creating '${ICR_NAMESPACE}'..."
  ibmcloud cr namespace-add "${ICR_NAMESPACE}"
fi

# --- Ensure the Code Engine project exists and is selected --------------------
echo "=== Selecting Code Engine project '${CE_PROJECT}' ==="
if ibmcloud ce project select --name "${CE_PROJECT}" >/dev/null 2>&1; then
  echo "  project exists — selected."
else
  echo "  project not found — creating '${CE_PROJECT}'..."
  ibmcloud ce project create --name "${CE_PROJECT}"
  ibmcloud ce project select --name "${CE_PROJECT}"
fi

# --- Ensure the Code Engine registry-access secret ----------------------------
# CE uses this to authenticate to ICR when PUSHING the built image.
# Username is always 'iamapikey' for ICR; password is the API key.
echo "=== Ensuring Code Engine registry secret '${CE_REGISTRY_SECRET}' ==="
if ibmcloud ce registry get --name "${CE_REGISTRY_SECRET}" >/dev/null 2>&1; then
  echo "  secret exists — updating credentials."
  ibmcloud ce registry update \
    --name "${CE_REGISTRY_SECRET}" \
    --server "${ICR_DOMAIN}" \
    --username iamapikey \
    --password "${API_KEY}"
else
  echo "  secret not found — creating."
  ibmcloud ce registry create \
    --name "${CE_REGISTRY_SECRET}" \
    --server "${ICR_DOMAIN}" \
    --username iamapikey \
    --password "${API_KEY}"
fi

# --- Build-from-Git args ------------------------------------------------------
# --build-source     : the Git repo Code Engine clones
# --build-commit     : branch (or commit) to build
# --build-context-dir: subdir containing the Dockerfile
# --build-dockerfile : Dockerfile path within the context dir
# --build-strategy   : dockerfile build
# --image            : ICR destination for the built image (CE pushes here)
# --registry-secret  : credentials CE uses to push to --image
SOURCE_ARGS=(
  --build-source "${GIT_REPO_URL}"
  --build-commit "${GIT_BRANCH}"
  --build-context-dir "${GIT_CONTEXT_DIR}"
  --build-dockerfile "${GIT_DOCKERFILE}"
  --build-strategy dockerfile
  --image "${IMAGE_REF}"
  --registry-secret "${CE_REGISTRY_SECRET}"
)

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

# --- Create or update the application (triggers server-side build) ------------
if ibmcloud ce app get --name "${CE_APP_NAME}" >/dev/null 2>&1; then
  echo "=== Updating existing app '${CE_APP_NAME}' (rebuild from Git) ==="
  ibmcloud ce app update "${COMMON_ARGS[@]}" "${SOURCE_ARGS[@]}"
else
  echo "=== Creating app '${CE_APP_NAME}' (build from Git) ==="
  # The first build clones + builds + pushes before deploying; it can take a few
  # minutes. The CLI streams build + deploy progress.
  ibmcloud ce app create "${COMMON_ARGS[@]}" "${SOURCE_ARGS[@]}"
fi

# --- Report the public URL ----------------------------------------------------
APP_URL="$(ibmcloud ce app get --name "${CE_APP_NAME}" --output url)"
echo ""
echo "=== Deployed ==="
echo "  App URL:      ${APP_URL}"
echo "  MCP endpoint: ${APP_URL}/mcp"
echo "  Health:       ${APP_URL}/health"
echo "  Image in ICR: ${IMAGE_REF}"
echo ""
echo "Verify with:"
echo "  bash ibm/code-engine-git-build/smoke-test.sh ${APP_URL}"
