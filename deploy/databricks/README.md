# Databricks Apps Deployment

Deploy your MCP server as a [Databricks App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/).
Databricks builds a container from your synced source and `app.yaml`, runs it,
and exposes it behind your workspace's authentication.

- **Transport:** MCP over streamable-HTTP at `/mcp` (stateless); health at `/health`
- **Port:** Databricks injects `DATABRICKS_APP_PORT` (defaults to `8000`); this
  template's `app.py` detects it and serves HTTP automatically — no code changes.

> **How the template already supports this:** `src/example_server/app.py` checks
> for `DATABRICKS_APP_PORT` (and generic `PORT`) and switches to streamable-HTTP
> on that port. That's the only wiring Databricks Apps needs.

## What Databricks injects at runtime

| Variable | Purpose |
|---|---|
| `DATABRICKS_APP_PORT` | Port your server must listen on (default 8000) |
| `DATABRICKS_HOST` | Workspace URL |
| `DATABRICKS_CLIENT_ID` | Service principal client ID |
| `DATABRICKS_CLIENT_SECRET` | OAuth secret |

The last three are available if your tools need to call back into Databricks
(e.g. query a table). The example tool doesn't use them.

---

## Part 1 — Prerequisites

### 1.1 Install the Databricks CLI (v0.205+)

```bash
# macOS
brew tap databricks/tap && brew install databricks
# or see: https://docs.databricks.com/dev-tools/cli/install.html
databricks --version
```

### 1.2 Authenticate

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com
databricks current-user me      # confirm you're logged in
```

> Databricks **Apps** must be enabled on your workspace. If `apps` commands fail
> with a feature error, ask your workspace admin to enable Databricks Apps.

### 1.3 Configure the deploy env file

```bash
cp deploy/databricks/.env.example deploy/databricks/.env
# edit:
#   - APP_NAME:          your server's name (lowercase, hyphens)
#   - SOURCE_CODE_PATH:  absolute /Workspace path (replace <you> with your user)
#   - DATABRICKS_HOST / DATABRICKS_CONFIG_PROFILE: optional, if not using DEFAULT
set -a; source deploy/databricks/.env; set +a
```

`.env` holds **no secrets** — auth lives in your CLI login. It is git-ignored.

---

## Part 2 — Deploy

```bash
set -a; source deploy/databricks/.env; set +a
bash deploy/databricks/deploy-databricks-app.sh
```

The script is idempotent and:

1. Confirms the CLI is installed and authenticated.
2. Stages `app.yaml` at the repo root (where Databricks expects it) for the sync.
3. Ensures the App exists (create-or-reuse).
4. Syncs the repo to `SOURCE_CODE_PATH` in your workspace.
5. Runs `databricks apps deploy` from that path.
6. Prints the app URL (`/mcp` + `/health`).

The first deploy builds the container and can take a few minutes.

### Smoke-test

```bash
# Private apps are auth-gated — an unauthenticated curl returns 302/401 (expected).
bash deploy/databricks/smoke-test.sh https://<app-url>

# Authenticated check:
DATABRICKS_TOKEN="$(databricks auth token --output json | jq -r .access_token)" \
  bash deploy/databricks/smoke-test.sh https://<app-url>
```

---

## Part 3 — Connect a client

Databricks Apps are gated by workspace auth, so an MCP client must present a
bearer token. For **watsonx Orchestrate** or **Claude** (remote HTTP), register
the endpoint and supply the token as an `Authorization: Bearer <token>` header
via the client's connection/credential mechanism.

For a quick local test with an MCP client that supports HTTP + headers:

```json
{
  "mcpServers": {
    "example-mcp": {
      "type": "http",
      "url": "https://<app-url>/mcp",
      "headers": { "Authorization": "Bearer <DATABRICKS_TOKEN>" }
    }
  }
}
```

> Token from `databricks auth token`. Tokens are short-lived; for a durable
> integration use a service principal with access to the app.

---

## Teardown

```bash
set -a; source deploy/databricks/.env; set +a
databricks apps delete "${APP_NAME}"
# Optionally remove the synced source:
#   databricks workspace delete "${SOURCE_CODE_PATH}" --recursive
```

---

## Files in this directory

| File | Purpose |
|---|---|
| `app.yaml` | Databricks Apps runtime config (the `command` that starts the server) |
| `.env.example` | Deploy coordinates template (copy to `.env`, no secrets) |
| `deploy-databricks-app.sh` | Idempotent create → sync → deploy |
| `smoke-test.sh` | Live `/health` + `/mcp` reachability check (auth-aware) |
| `README.md` | This runbook |

## Known gaps / notes

- **Auth-gated by default:** Databricks Apps sit behind workspace SSO/OAuth, so
  unauthenticated probes return 302/401 — that's expected, not a failure. Use a
  bearer token to reach the app programmatically.
- **Renamed package:** if you renamed `example_server`, update the module path in
  `app.yaml` (`python -m <your_pkg>.app`).
- **`app.yaml` location:** Databricks reads `app.yaml` from the deployed source
  root. The deploy script stages this kit's copy at the repo root for the sync
  and removes it afterward; if you prefer, commit a copy at the repo root instead.
- **Stateless HTTP:** the server runs stateless streamable-HTTP, which scales
  cleanly on Apps (no sticky sessions required).
