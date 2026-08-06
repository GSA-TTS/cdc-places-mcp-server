---
title: "watsonx Orchestrate — Local MCP Toolkit (stdio)"
description: "Register the CDC PLACES MCP server as a LOCAL MCP toolkit that runs inside the watsonx Orchestrate runtime over stdio — no HTTP endpoint, no container, no cloud deploy"
status: draft
tier: 2
last_updated: "2026-08-06"
---

# watsonx Orchestrate — Local MCP Toolkit (stdio)

This kit registers the CDC PLACES MCP server as a **local MCP toolkit**: you ship
the server *code* to watsonx Orchestrate, which installs it (via a
`requirements.txt`) and runs it **over stdio inside the Orchestrate runtime**.
There is **no HTTP endpoint, no container, no IBM Code Engine, and no image
registry** — the lowest-overhead path for a novice developer to get a Python MCP
server into Orchestrate.

> **Why this is the lowest-overhead route for novices.** The pasted ADK docs
> describe three "own-code" tool types. Ranked by setup burden:
>
> | Option | You must… | Overhead |
> |---|---|---|
> | **Local MCP toolkit (this kit)** | drop a `server.py` + `requirements.txt` and run one import command | **Lowest** — reuses your existing FastMCP server unchanged; no HTTP, no deploy, no infra |
> | **Remote MCP toolkit** (`../code-engine-git-build/`, `../prebuilt-image/`) | build/deploy an HTTP server to Code Engine, manage a public URL | Medium — needs cloud deploy + registry authority |
> | **ADK Python toolkit** | rewrite tools into ADK decorator conventions | Higher — code rewrite, not a straight reuse |
>
> Local MCP toolkit wins for novices because it **reuses the code you already
> have** (the `places` package) with the fewest new concepts: no Docker, no cloud
> account plumbing, no public networking. Trade-off: it runs *inside* Orchestrate
> with a ~100–300 ms process-startup cost per call (fine for moderate use), and
> it only works from a machine that has the ADK + your repo (e.g. the Bob VM).

## How it reuses this repo

`server.py` in this folder is a **3-line stdio entrypoint** that imports the
existing FastMCP app (`places.app:mcp`) and runs it over stdio. `requirements.txt`
installs the `places` package from the repo root, so **you do not duplicate or
rewrite any tool code** — edits in `src/places/` are picked up on the next import.

```
ibm/local-mcp-toolkit/
├── server.py          # stdio entrypoint: adds its dir to sys.path, then `from places.app import mcp; mcp.run(transport="stdio")`
├── requirements.txt   # pinned runtime deps (fastmcp, pandas, requests) staged next to the package
├── toolkit.yaml       # import config template (kind: mcp, command: python server.py, tools: *)
├── register-toolkit.sh# stage minimal package_root + activate ADK env + import (idempotent)
├── .env.example       # instance URL + env/toolkit names (no secrets)
└── README.md          # this runbook
```

> **How the register script assembles the upload (learned the hard way):**
> watsonx Orchestrate uploads `package_root`, installs a `requirements.txt` found
> there, then runs `command` over stdio. To make that work reliably the script
> builds a small **staging** dir (`_stage/`, git-ignored) containing a
> **flattened** copy of the package — `places/` and `server.py` at the top level
> (no `src/` prefix) plus the pinned `requirements.txt` — and points
> `package_root` at it. This avoids three failure modes hit during the pilot:
> a 413 (uploading the whole repo incl. venvs), a `ModuleNotFoundError: places`
> (src-layout not importable at runtime), and `ModuleNotFoundError: fastmcp`
> (deps not installed because the ADK reads `requirements.txt`, not pyproject).

---

## Part 1 — Prerequisites

Local MCP toolkits run **inside Orchestrate**, but you import them from a machine
that has the ADK and this repo. In the hackathon that machine is the **Bob VM**;
locally, any Python 3.11–3.14 environment works.

```bash
# Python 3.11-3.14
pip install --upgrade ibm-watsonx-orchestrate
orchestrate --version
```

Your Orchestrate instance URL + API key are on the wxO service page in IBM Cloud
(Resource List → your watsonx Orchestrate instance), and also recorded in
`ibm/internal/credentials.txt` (`WXO_INSTANCE_URL`, `WXO_API_KEY`).

> **Security:** treat the API key as a secret. Pass it via the `WXO_API_KEY`
> environment variable (below); never commit it. `ibm/internal/` is git-ignored.

---

## Part 2 — Register the toolkit

### 2.1 Configure the env file

```bash
cp ibm/local-mcp-toolkit/.env.example ibm/local-mcp-toolkit/.env
# edit ibm/local-mcp-toolkit/.env:
#   - WXO_INSTANCE_URL: your Orchestrate instance URL
#   - WXO_ENV_NAME / TOOLKIT_NAME: local labels (defaults are fine)
source ibm/local-mcp-toolkit/.env
```

`.env` holds **no secrets** — only the instance URL and names. It is git-ignored.

### 2.2 Provide your API key and run the register script

```bash
export WXO_API_KEY="<your Orchestrate API key>"   # else you'll be prompted (hidden)
bash ibm/local-mcp-toolkit/register-toolkit.sh
```

The script:
1. Confirms the ADK is installed
2. Adds (if needed) and **activates** the Orchestrate env against your instance
3. **Stages** a minimal, flattened `package_root` (`_stage/`: `places/` +
   `server.py` + pinned `requirements.txt`) so the upload is tiny and installs
   cleanly
4. **Imports** the toolkit — Orchestrate installs `requirements.txt` and runs
   `python server.py` over stdio when tools are called
5. Lists toolkits so you can confirm `cdc_places_local` appears with its 2 tools
6. Cleans up the generated `_stage/` and `_toolkit.generated.yaml`

It is idempotent: on re-run it removes and re-imports so code/dependency changes
are picked up.

> **Manual equivalent** (if you prefer the flag form) — note it needs the same
> flattened staging dir, not the repo root:
> ```bash
> orchestrate toolkits add \
>   --kind mcp \
>   --name cdc_places_local \
>   --description "CDC PLACES health statistics (local stdio MCP)" \
>   --package_root <staging-dir with places/ + server.py + requirements.txt> \
>   --command "python server.py" \
>   --tools "*"
> ```

### 2.2a Corporate TLS interception (Zscaler / GSA network) — likely required

On a GSA-managed network the ADK's IAM login may fail with:

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: unable to get local issuer certificate
```

This is **not** a bad key or URL. A TLS-inspection proxy (Zscaler) re-signs HTTPS
with a private CA that Python's default `certifi` bundle does not trust — even
though `curl`/your browser work, because macOS Keychain already trusts it. The
fix is to give Python a CA bundle that includes the proxy root **exported from
the Keychain** (the handshake alone omits the self-signed root, so exporting from
Keychain is what works).

```bash
# 1. Confirm interception (issuer will name your proxy, e.g. Zscaler):
openssl s_client -connect iam.cloud.ibm.com:443 -showcerts </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer

# 2. Export the proxy root(s) from the macOS System keychain:
security find-certificate -a -c "Zscaler" -p /Library/Keychains/System.keychain \
  > /tmp/zscaler-roots.pem 2>/dev/null
security find-certificate -a -c "Zscaler" -p /System/Library/Keychains/SystemRootCertificates.keychain \
  >> /tmp/zscaler-roots.pem 2>/dev/null
grep -c "BEGIN CERTIFICATE" /tmp/zscaler-roots.pem   # expect >= 1

# 3. Build a merged bundle = certifi roots + the proxy root(s):
CERTIFI="$(uv run --active python -c 'import certifi; print(certifi.where())')"
cat "$CERTIFI" /tmp/zscaler-roots.pem > /tmp/wxo-ca-bundle.pem

# 4. Point the ADK (requests + urllib) at the merged bundle, in THIS shell:
export SSL_CERT_FILE=/tmp/wxo-ca-bundle.pem
export REQUESTS_CA_BUNDLE=/tmp/wxo-ca-bundle.pem

# 5. Verify before registering:
uv run --active python -c "import urllib.request; urllib.request.urlopen('https://iam.cloud.ibm.com/identity/.well-known/openid-configuration', timeout=10); print('TLS to IAM OK')"
```

Then run the register script **in the same shell** so the exports carry over.

> If step 2 finds no Zscaler-named cert, fall back to bundling ALL keychain roots:
> `security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain > /tmp/allroots.pem`
> then `cat "$CERTIFI" /tmp/allroots.pem > /tmp/wxo-ca-bundle.pem`.
>
> `/tmp` is fine to get unblocked; for a durable path, save the merged bundle
> somewhere stable (e.g. `~/.config/orchestrate/ca-bundle.pem`) and export
> `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE` to it in your shell profile.

### 2.3 (Optional) Verify the entrypoint locally first

You can confirm the stdio server starts before importing it to Orchestrate:

```bash
# From the repo root, with the repo installed (e.g. `uv sync` or `pip install -e .`):
python ibm/local-mcp-toolkit/server.py
# It will block waiting for MCP stdio input; Ctrl-C to exit. No error = good.
```

---

## Part 3 — Build an agent that uses it

In the Orchestrate UI, create/edit an agent and add the **`cdc_places_local`**
tools (`get_cdc_places_data`, `area_summary_stats`). Give it an instruction
aligned with the eval harness:

```
You are an expert data retriever for the CDC PLACES dataset.
Use the cdc_places tools to answer questions with specific numeric values.
```

Chat-test one gold question:

> *"What percent of adults had short sleep durations in Kauai County, Hawaii in 2018?"*
> (Gold answer: **36.9**)

For automated evaluation against the 10 gold Q/A pairs, follow **Part 4** of the
sibling runbook [`../prebuilt-image/README.md`](../prebuilt-image/README.md) —
the evaluation is identical regardless of how the tools were registered.

---

## Connections (only if your server needs secrets)

The CDC PLACES server needs **no credentials** (public CDC data), so `toolkit.yaml`
declares no `connections`. If you adapt this kit for a server that needs secrets,
create a connection and pass it at import time:

```bash
orchestrate connections add -a my_connection
for env in draft live; do
  orchestrate connections configure -a my_connection --env $env --type team --kind key_value
  orchestrate connections set-credentials -a my_connection --env $env -e "SECURE_VAR=value"
done
# then add `connections: [my_connection]` to toolkit.yaml, or pass -a my_connection to `add`
```

The connection type determines which env vars Orchestrate injects into the stdio
process at runtime (Basic, Bearer, API Key, OAuth, Key/Value, ...).

---

## Teardown

```bash
orchestrate toolkits remove --name cdc_places_local
```

---

## How this compares to the other IBM kits

| Kit | Transport | Where it runs | Infra needed |
|---|---|---|---|
| **`local-mcp-toolkit/` (this)** | **stdio** | **Inside Orchestrate** | **None** (ADK + repo) |
| `code-engine-git-build/` | streamable-HTTP | IBM Code Engine (built from Git) | Code Engine + ICR |
| `prebuilt-image/` | streamable-HTTP | IBM Code Engine (prebuilt image) | Code Engine + public image |

## Known gaps / notes

- **Runs inside Orchestrate:** no public endpoint exists, so you cannot smoke-test
  it with curl like the Code Engine kits. Verify by importing and chat-testing in
  the UI (Part 3), or run `server.py` locally (2.3).
- **Startup overhead:** process-per-invocation adds ~100–300 ms/call. Fine for
  hackathon/demo and moderate use; for high-frequency Python tools the ADK docs
  recommend a Python toolkit instead.
- **Import machine needs Python + the repo:** the ADK bundles `package_root` and
  its dependencies at import time. Run the register script from the Bob VM (or a
  local checkout), not from a bare shell without the repo.
- **Requirements install:** `requirements.txt` installs the repo via `../../`.
  If your Orchestrate/ADK version rejects a relative editable path, replace it
  with the repo's pinned deps (copy from the repo root `requirements.txt`) plus
  the `places` package source, or publish `places` to PyPI and depend on it by
  name.
