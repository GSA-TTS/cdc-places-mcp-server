# Deploying Your MCP Server

Local development runs your server over **stdio** (how Claude Desktop / Claude
Code launch it). To share it with an agent platform, deploy it to a host that
serves it over **streamable-HTTP**, then register it.

This template ships deployment kits for two targets:

| Target | Kits | Transport | When to use |
|---|---|---|---|
| **IBM watsonx Orchestrate** | [`ibm/`](ibm/) — 3 kits | stdio (local) **or** streamable-HTTP (Code Engine) | You're evaluating/agent-building in watsonx Orchestrate |
| **Databricks** | [`databricks/`](databricks/) | streamable-HTTP (Databricks Apps) | You're deploying alongside a Databricks workspace |

## The server code doesn't change

Every kit runs the **same** server in `src/example_server/`. The entry point
`app.py` auto-selects its transport:

- a platform port (`DATABRICKS_APP_PORT` or `PORT`) → **HTTP** on that port;
- `MCP_TRANSPORT=streamable-http` → HTTP on `MCP_HOST:MCP_PORT`;
- otherwise → **stdio**.

So IBM Code Engine and Databricks Apps both "just work" — they inject a port and
the server serves HTTP with `/mcp` + `/health`.

## IBM (three options, lowest → highest overhead)

See [`ibm/README.md`](ibm/README.md) for the full chooser. In short:

1. **[`ibm/local-mcp-toolkit/`](ibm/local-mcp-toolkit/)** — ship the code; run it
   over stdio **inside** Orchestrate. No HTTP, no container, no registry.
   **Lowest overhead — recommended for first-timers.**
2. **[`ibm/code-engine-git-build/`](ibm/code-engine-git-build/)** — Code Engine
   builds from your public Git repo and pushes to your Container Registry.
   Needs ICR authority.
3. **[`ibm/prebuilt-image/`](ibm/prebuilt-image/)** — deploy a prebuilt public
   image to Code Engine (or build from Git). Lowest cloud authority.

## Databricks

See [`databricks/README.md`](databricks/README.md). Deploy as a Databricks App:
the kit syncs your repo to the workspace and runs `databricks apps deploy`. The
app is gated by workspace auth, so clients present a bearer token.

## cloud.gov (bonus)

Not a full kit, but the repo root includes a `manifest.yaml` for cloud.gov
(Cloud Foundry). Deploy with `cf push` after `cf login`/`cf target`. See the
comments in `manifest.yaml`.

---

## Security reminder

All kits expose the MCP endpoint with **no authentication** by default (except
Databricks, which is gated by workspace SSO). That matches a public-data
hackathon posture. For anything beyond a hackathon, front the endpoint with auth
and review your agency's ATO requirements. Never commit secrets — each kit's
`.env` is git-ignored and holds coordinates only.
