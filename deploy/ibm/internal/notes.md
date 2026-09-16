---
title: "IBM Cloud Pilot Notes — CDC PLACES MCP Server"
description: "What worked, what's blocked, and what hackathon participants will need on IBM Cloud"
status: draft
tier: 2
last_updated: "2026-08-06"
---

# IBM Cloud Pilot Notes — CDC PLACES MCP Server

Notes from a trial run of the MCP-hackathon cloud workflow (local build → deploy
to cloud → evaluate with an agent) on an IBM Cloud environment, using the CDC
PLACES MCP server as the example. Written to brief the IBM rep on the permission
gaps that hackathon participants would hit.

## Environment used

| Item | Value |
|---|---|
| IBM Cloud account | `itz-watsonx-2` (TechZone-style trial account) |
| Region (compute) | `us-east` (Washington DC) — IBM Cloud Code Engine |
| Region (Orchestrate) | `us-south` — watsonx Orchestrate SaaS |
| Resource group | `watsonx-orcestrate-n71jr` (only one available) |
| CLIs | `ibmcloud` 2.46.0, `code-engine` plugin 1.62.7, Orchestrate ADK 2.14.0 |

## What worked end-to-end ✅

1. **Deployed the MCP server to IBM Code Engine.** Container app running with a
   public HTTPS route:
   `https://cdc-places-mcp-server.2d6q9k1izlwm.us-east.codeengine.appdomain.cloud`
   - `/health` → 200 healthy
   - `/mcp` → responds with correct MCP protocol behavior (rejects un-initialized
     calls with "Missing session ID" — the expected handshake requirement)
2. **Registered the server in watsonx Orchestrate via the UI** as an MCP tool
   (remote / streamable-HTTP, no auth). Orchestrate discovered both tools
   (`get_cdc_places_data`, `area_summary_stats`).
3. **Built an agent in the Orchestrate UI** using those tools and confirmed it
   can reach the MCP server and answer questions in the chat/preview.

This proves the full workflow shape: **local → IBM Code Engine → Orchestrate
agent → dataset answers.**

## What was blocked 🚫 (account-permission gaps)

All three blockers are the **same root cause**: the trial account does not grant
the logged-in user the IAM policies needed for self-service resource creation.

| # | Blocked action | Error / action denied | Impact |
|---|---|---|---|
| 1 | **Code Engine build-from-Git (Path A)** | `insufficient permission to assign policies to the service ID used to access IBM Container Registry` | Cannot use server-side "build from repo" deploys. Had to fall back to deploying a **prebuilt public image** (Path B). |
| 2 | **Create IBM Container Registry namespace** | `No namespaces exist … or you are not authorized` | Confirms no push target exists for server-side builds. |
| 3 | **Create an IAM API key** | `iam-identity.user-apikey.create … denied due to lack of access policy` | Cannot authenticate the **Orchestrate ADK CLI** → no scripted toolkit registration or automated evaluation (`orchestrate evaluations evaluate`). UI-only. |

## Workarounds we used

- **Deploy:** switched from Git-build (Path A) to **prebuilt public image**
  (Path B) — `ghcr.io/gsa-tts/cdc-places-mcp-server:0.1.0`. No registry-write
  permission needed. This is the exact image the Dockerfile produces, so it's a
  faithful deploy; we just lose the build-from-source convenience.
- **Orchestrate:** did registration + agent build **in the UI** instead of the
  CLI. Sufficient to demo, but not scriptable/repeatable.
- **Evaluation:** manual UI chat-testing against the 10 gold Q/A pairs
  (`eval/phoenix/datasets/places-eval-0/places-eval-0.csv`) instead of the
  automated evaluator.

## What to ask the IBM rep for

To make this **plug-and-play for hackathon participants**, participants (or a
shared service ID) need, in the account/resource group they'll use:

1. **Container Registry authority** — permission to create an ICR namespace and
   the associated service-ID policy, so Code Engine **build-from-Git** works.
   *(Or: pre-provision one shared ICR namespace + grant participants Writer.)*
   Enables the zero-local-Docker "point Code Engine at your repo" flow.
2. **IAM API key creation** (`iam-identity.user-apikey.create`) — so participants
   can authenticate the **Orchestrate ADK CLI** and run **scripted evaluations**.
   *(Or: an admin issues each participant an IAM API key.)*
3. **Confirm the account tier supports Code Engine** — project creation worked
   here, but confirm participants' accounts aren't Lite-only (Lite cannot create
   Code Engine projects).
4. **Clarify Orchestrate access model** — whether each participant gets their own
   Orchestrate instance/API key, or shares one, and where the API key is issued
   (IBM Cloud IAM vs. an Orchestrate-native key on the Settings → API details
   page — the UI path we could not fully confirm).

### Nice-to-know questions

- Is there a **shared service ID** pattern IBM recommends for a multi-participant
  hackathon (one identity with the registry/API-key policies, vs. per-user)?
- Recommended **region pairing** — is Code Engine in `us-east` + Orchestrate in
  `us-south` fine, or should both be co-located?
- For public-data MCP servers with **no auth**, is that acceptable in their
  environment, or do they require the endpoint to be fronted with auth?

## Repo artifacts produced

On branch `feat/ibm-code-engine-deploy` under `ibm/`. Each deployment option is a
self-contained kit in its own directory so they stay clearly delineated:

| Kit | Method | Transport / where it runs | Status |
|---|---|---|---|
| `ibm/prebuilt-image/` | Deploy a prebuilt public image to Code Engine | streamable-HTTP on Code Engine | ✅ worked in the original `itz-watsonx-2` trial account |
| `ibm/code-engine-git-build/` | Code Engine builds from a public Git repo, pushes to IBM Container Registry, deploys | streamable-HTTP on Code Engine | ✅ verified live in `itz-saas-606` (the account with ICR authority) |
| `ibm/local-mcp-toolkit/` | Ship the server code to watsonx Orchestrate; run it over **stdio inside the Orchestrate runtime** (via ADK) | stdio, inside Orchestrate — no HTTP, no container | ✅ verified live against the Orchestrate SaaS instance (ADK 2.14.0) |

Each kit contains its own `README.md`, `.env.example`, and scripts. `internal/`
(this file + `credentials.txt`) is git-ignored.

### Option 1 — Prebuilt image (`ibm/prebuilt-image/`)
- `deploy-code-engine.sh` deploys a public image (e.g. `ghcr.io/...`) directly.
- Lowest cloud authority required (no registry write). This is the fallback that
  worked when the trial account lacked ICR permissions.

### Option 2 — Code Engine build-from-Git (`ibm/code-engine-git-build/`)
- `deploy-build-from-git.sh`: ensures an ICR namespace → creates a Code Engine
  registry-access secret from an IAM API key → `ce app create --build-source …
  --image icr.io/<ns>/… --registry-secret …`. Code Engine clones the repo, builds
  the Dockerfile server-side, pushes to ICR, and deploys. No local Docker.
- **Verified live** in `itz-saas-606`. Account-reality gotchas discovered and
  documented in the kit: no `Default` resource group (use the generated
  `eid-<hash>` group); the ICR registry is **global** (`icr.io`), independent of
  the Code Engine region; reuse the pre-provisioned namespace
  (`gsa-hackathon-cr-erm1`) rather than creating one.
- App URL from the run:
  `https://cdc-places-mcp-server.2d83albi0vxi.us-east.codeengine.appdomain.cloud`

### Option 3 — Local MCP toolkit / stdio (`ibm/local-mcp-toolkit/`)
- Lowest-overhead route for novices: reuses the existing FastMCP server unchanged
  and runs it **inside Orchestrate over stdio** — no HTTP endpoint, no Code
  Engine, no container, no image registry.
- `register-toolkit.sh`: activates the ADK env and imports the toolkit. It builds
  a minimal, **flattened** staging `package_root` (`places/` + `server.py` +
  pinned `requirements.txt`) and points the import at it.
- **Verified live** (ADK 2.14.0): `cdc_places_local` registered with both tools.
- Three failure modes hit and fixed during the run (all documented in the kit
  README so the next person isn't stuck):
  1. **Zscaler TLS interception** — ADK IAM login failed with
     `SSLCertVerificationError: unable to get local issuer certificate`. `curl`
     worked (macOS keychain trusts Zscaler) but Python's `certifi` bundle did
     not. Fix: export the Zscaler root from the keychain
     (`security find-certificate -a -c Zscaler …`), merge it with certifi into
     one PEM, and point the ADK at it via `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`.
  2. **413 Request Entity Too Large** — pointing `package_root` at the repo root
     uploaded ~290 MB (the two virtualenvs). Fix: stage only the flattened
     package.
  3. **ModuleNotFoundError (`places`, then `fastmcp`)** — src-layout wasn't
     importable at runtime, and the ADK installs deps from a `requirements.txt`
     at `package_root` (not from `pyproject.toml`). Fix: flatten `places/` +
     `server.py` at the staging root (server.py adds its dir to `sys.path`) and
     ship the pinned `requirements.txt`.

Shared support files:
- `smoke-test.sh` (in each Code Engine kit) — live `/health` + `/mcp` verification.
- `.env.example` — deploy/registration coordinates (no secrets).
- `README.md` (per kit) — full runbook.
- `notes.md` — this file.

## Known follow-ups

- **DONE:** Re-test **build-from-Git** after ICR authority — verified in
  `itz-saas-606` (see Option 2). The intended participant experience now works.
- Authenticate the **ADK CLI** and run `orchestrate evaluations evaluate` against
  the 10 gold questions for automated, repeatable scoring. (ADK auth is now
  proven working via the local-MCP-toolkit run — the Zscaler CA-bundle export is
  the prerequisite on a GSA network.)
- Minor DX fix noted during the run: the deploy scripts need vars **exported**
  (`set -a; source ibm/<kit>/.env; set +a`) before `bash …`. Consider having each
  script source its own `.env` so a single `bash ibm/<kit>/deploy-*.sh` just works.

## Notes from Meeting
- Look into Watson X orchestrate Python Toolkits for Python Server deployment (https://developer.watson-orchestrate.ibm.com/apis/toolkits/create-a-toolkit#create-a-toolkit)

