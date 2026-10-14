#!/usr/bin/env bash
# Set up a service principal (SP) for running the offline MLflow eval against a
# deployed Databricks Apps MCP server.
#
# WHY THIS EXISTS
#   A deployed Databricks App is OAuth-gated. An offline notebook eval cannot
#   reach it with the notebook's own identity (runtime auth can't mint an OAuth
#   token, and OBO needs a forwarded request header that doesn't exist offline).
#   The only identity that works is a service principal using OAuth M2M. This
#   script provisions that SP and wires up everything the eval needs.
#
# WHAT IT DOES (idempotent — safe to re-run)
#   1. Create (or reuse) a service principal.
#   2. Grant it the `workspace-access` entitlement.
#   3. Grant it `CAN_USE` on your MCP app.
#   4. Mint an OAuth secret for it   [account-CLI; falls back to a UI prompt].
#   5. Create a Databricks secret scope and store sp_id + sp_secret.
#   6. Print the values to paste into agent_eval_offline.py's CONFIG block.
#
# PREREQUISITES
#   - Databricks CLI (v0.205+), authenticated as a WORKSPACE ADMIN of the
#     workspace where the app is deployed:  databricks auth login --host <url>
#   - The MCP app already deployed (run deploy-databricks-app.sh first).
#
# USAGE
#   # reads deploy/databricks/.env for APP_NAME / host / profile if present:
#   set -a; source deploy/databricks/.env; set +a
#   bash eval/databricks/setup-eval-sp.sh
#
#   # or pass everything explicitly:
#   bash eval/databricks/setup-eval-sp.sh \
#     --app-name my-mcp-server \
#     --sp-name sp-mcp-eval \
#     --scope mcp-eval-secrets
#
#   # if OAuth-secret auto-mint fails, re-run with the secret you made in the UI:
#   bash eval/databricks/setup-eval-sp.sh --oauth-secret 'dose_xxx...'
set -euo pipefail

# --- Defaults (overridable by flags / env) -----------------------------------
SP_NAME="${SP_NAME:-sp-mcp-eval}"
SCOPE="${SCOPE:-mcp-eval-secrets}"
KEY_ID="${KEY_ID:-sp_id}"
KEY_SECRET="${KEY_SECRET:-sp_secret}"
APP_NAME="${APP_NAME:-}"
OAUTH_SECRET="${OAUTH_SECRET:-}"
ACCOUNT_ID="${DATABRICKS_ACCOUNT_ID:-}"

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-name)     APP_NAME="$2"; shift 2 ;;
    --sp-name)      SP_NAME="$2"; shift 2 ;;
    --scope)        SCOPE="$2"; shift 2 ;;
    --key-id)       KEY_ID="$2"; shift 2 ;;
    --key-secret)   KEY_SECRET="$2"; shift 2 ;;
    --oauth-secret) OAUTH_SECRET="$2"; shift 2 ;;
    --account-id)   ACCOUNT_ID="$2"; shift 2 ;;
    -h|--help)      usage 0 ;;
    *) echo "unknown arg: $1" >&2; usage 1 ;;
  esac
done

: "${APP_NAME:?set --app-name (or APP_NAME via deploy/databricks/.env)}"

PROFILE_ARGS=()
if [[ -n "${DATABRICKS_CONFIG_PROFILE:-}" ]]; then
  PROFILE_ARGS=(--profile "${DATABRICKS_CONFIG_PROFILE}")
fi
DBX=(databricks "${PROFILE_ARGS[@]}")

# --- Preflight ----------------------------------------------------------------
if ! command -v databricks >/dev/null 2>&1; then
  echo "FATAL: 'databricks' CLI not found." >&2
  echo "       Install: https://docs.databricks.com/dev-tools/cli/install.html" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "FATAL: 'jq' not found (needed to parse CLI JSON). Install jq and retry." >&2
  exit 1
fi
if ! "${DBX[@]}" current-user me >/dev/null 2>&1; then
  echo "FATAL: not authenticated. Run: databricks auth login --host <workspace-url>" >&2
  exit 1
fi

echo "=== Config ==="
echo "  app name:      ${APP_NAME}"
echo "  SP name:       ${SP_NAME}"
echo "  secret scope:  ${SCOPE} (keys: ${KEY_ID}, ${KEY_SECRET})"
echo "  profile:       ${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
echo ""

# --- 1. Create or reuse the service principal ---------------------------------
echo "=== 1. Service principal ==="
SP_JSON="$("${DBX[@]}" service-principals list --output json 2>/dev/null || echo '[]')"
APP_ID="$(echo "${SP_JSON}" | jq -r --arg n "${SP_NAME}" '.[] | select(.displayName==$n) | .applicationId' | head -1)"
SP_NUMERIC_ID="$(echo "${SP_JSON}" | jq -r --arg n "${SP_NAME}" '.[] | select(.displayName==$n) | .id' | head -1)"

if [[ -n "${APP_ID}" && "${APP_ID}" != "null" ]]; then
  echo "  reusing existing SP '${SP_NAME}' (applicationId=${APP_ID})"
else
  echo "  creating SP '${SP_NAME}'..."
  CREATE_JSON="$("${DBX[@]}" service-principals create --display-name "${SP_NAME}" --output json)"
  APP_ID="$(echo "${CREATE_JSON}" | jq -r '.applicationId')"
  SP_NUMERIC_ID="$(echo "${CREATE_JSON}" | jq -r '.id')"
  echo "  created (applicationId=${APP_ID}, id=${SP_NUMERIC_ID})"
fi

if [[ -z "${APP_ID}" || "${APP_ID}" == "null" ]]; then
  echo "FATAL: could not determine the SP applicationId." >&2
  exit 1
fi

# --- 2. Grant workspace-access entitlement ------------------------------------
echo ""
echo "=== 2. workspace-access entitlement ==="
HAS_WS="$("${DBX[@]}" service-principals get "${SP_NUMERIC_ID}" --output json 2>/dev/null \
  | jq -r '[.entitlements[]?.value] | index("workspace-access") // empty')"
if [[ -n "${HAS_WS}" ]]; then
  echo "  already granted."
else
  echo "  granting workspace-access..."
  "${DBX[@]}" service-principals patch "${SP_NUMERIC_ID}" --json '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [
      {"op": "add", "path": "entitlements", "value": [{"value": "workspace-access"}]}
    ]
  }' >/dev/null || {
    echo "  WARN: entitlement patch failed. You may need workspace-admin rights." >&2
    echo "        Grant 'Workspace access' to '${SP_NAME}' in Settings > Identity and access." >&2
  }
fi

# --- 3. Grant CAN_USE on the app ----------------------------------------------
echo ""
echo "=== 3. app permission (CAN_USE) ==="
if "${DBX[@]}" apps get "${APP_NAME}" >/dev/null 2>&1; then
  if "${DBX[@]}" apps set-permissions "${APP_NAME}" --json "{
    \"access_control_list\": [
      {\"service_principal_name\": \"${APP_ID}\", \"permission_level\": \"CAN_USE\"}
    ]
  }" >/dev/null 2>&1; then
    echo "  granted CAN_USE on '${APP_NAME}' to the SP."
  else
    echo "  WARN: could not set app permissions via CLI (verb/version may differ)." >&2
    echo "        Grant it in the UI: Compute > Apps > ${APP_NAME} > Permissions >" >&2
    echo "        add '${SP_NAME}' with 'Can Use'." >&2
  fi
else
  echo "  WARN: app '${APP_NAME}' not found. Deploy it first, then re-run, or grant" >&2
  echo "        CAN_USE manually once it exists." >&2
fi

# --- 4. Mint an OAuth secret (account CLI; fall back to UI) --------------------
echo ""
echo "=== 4. OAuth secret ==="
if [[ -z "${OAUTH_SECRET}" ]]; then
  echo "  attempting to mint an OAuth secret via the account CLI..."
  ACC_ARGS=()
  [[ -n "${ACCOUNT_ID}" ]] && ACC_ARGS=(--account-id "${ACCOUNT_ID}")
  if SECRET_JSON="$("${DBX[@]}" account service-principal-secrets create "${SP_NUMERIC_ID}" \
        "${ACC_ARGS[@]}" --output json 2>/dev/null)"; then
    OAUTH_SECRET="$(echo "${SECRET_JSON}" | jq -r '.secret // empty')"
  fi
fi

if [[ -z "${OAUTH_SECRET}" ]]; then
  cat >&2 <<EOF
  Could not auto-mint the OAuth secret (this requires ACCOUNT-level CLI access).
  Do this ONE step in the UI, then re-run this script with --oauth-secret:

    1. Account console (accounts.cloud.databricks.com)
       > User management > Service principals > ${SP_NAME}
       > Secrets (OAuth secrets) > Generate secret
    2. Copy the Secret value (shown once).
    3. Re-run:
         bash eval/databricks/setup-eval-sp.sh \\
           --app-name ${APP_NAME} --sp-name ${SP_NAME} \\
           --scope ${SCOPE} --oauth-secret '<the-secret-value>'

  (Everything else above is already done and is idempotent.)
EOF
  exit 2
fi
echo "  have an OAuth secret."

# --- 5. Store credentials in a secret scope -----------------------------------
echo ""
echo "=== 5. secret scope ==="
if "${DBX[@]}" secrets list-scopes --output json 2>/dev/null \
     | jq -e --arg s "${SCOPE}" '.scopes[]? | select(.name==$s)' >/dev/null; then
  echo "  scope '${SCOPE}' exists — reusing."
else
  echo "  creating scope '${SCOPE}'..."
  "${DBX[@]}" secrets create-scope "${SCOPE}"
fi
"${DBX[@]}" secrets put-secret "${SCOPE}" "${KEY_ID}"     --string-value "${APP_ID}"
"${DBX[@]}" secrets put-secret "${SCOPE}" "${KEY_SECRET}" --string-value "${OAUTH_SECRET}"
echo "  stored ${KEY_ID} + ${KEY_SECRET}."

# --- 6. Report ----------------------------------------------------------------
cat <<EOF

=== Done ===
Service principal '${SP_NAME}' is provisioned and its credentials are stored in
secret scope '${SCOPE}'.

Set these in agent_eval_offline.py's CONFIG block:

    SECRET_SCOPE            = "${SCOPE}"
    SECRET_KEY_CLIENT_ID   = "${KEY_ID}"
    SECRET_KEY_CLIENT_SECRET = "${KEY_SECRET}"

Then run the notebook. If MCP tool calls 403, confirm the SP has CAN_USE on the
app (step 3 above) — that grant requires workspace-admin rights.
EOF
