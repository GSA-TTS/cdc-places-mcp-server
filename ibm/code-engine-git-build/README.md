---
title: "IBM Code Engine Build-from-Git Deployment"
description: "Deploy the CDC PLACES MCP server to IBM Code Engine by building from a public Git repo, pushing to IBM Container Registry"
status: draft
tier: 2
last_updated: "2026-08-06"
---

# IBM Code Engine — Build-from-Git Deployment

This kit deploys the CDC PLACES MCP server to **IBM Cloud Code Engine** by
**building directly from a public Git repo**: Code Engine clones the repo, builds
its `Dockerfile` **server-side**, pushes the resulting image to **your IBM
Container Registry (ICR) namespace**, then deploys it. **No local Docker, no
local image build, no manual push.**

> **Which kit is this?** This is the **build-from-Git** kit — the intended
> "point Code Engine at your repo and go" experience. It was **blocked in the
> original trial account** (`itz-watsonx-2`), which lacked the IBM Container
> Registry authority server-side builds need (see
> [`../internal/notes.md`](../internal/notes.md)). Use this kit in an account
> that **has** Container Registry access.
>
> If you only have a prebuilt public image (no ICR authority), use the sibling
> [`../prebuilt-image/`](../prebuilt-image/README.md) kit instead.

## How it differs from the prebuilt-image kit

| | This kit (`code-engine-git-build/`) | Sibling (`prebuilt-image/`) |
|---|---|---|
| Source | Code Engine builds your **Git repo** | You supply a **prebuilt image** ref |
| Local Docker | **Not needed** | Needed to build/push the image |
| Image registry | Pushes to **your ICR namespace** | Any public registry (e.g. GHCR) |
| Extra IBM authority | **ICR namespace + API key** (for push secret) | None |
| Best for | The plug-and-play participant flow | Pinned release when ICR is unavailable |

## What gets deployed (CDC PLACES example)

- **Repo:** any public repo with a Dockerfile that serves MCP (this repo is one)
- **Transport:** MCP over streamable-HTTP at `/mcp`; health check at `/health`
- **Port:** `8080` (set by the `Dockerfile`)
- **Tools:** `get_cdc_places_data`, `area_summary_stats`
- **Built image lands at:** `${ICR_DOMAIN}/${ICR_NAMESPACE}/${CE_APP_NAME}:${IMAGE_TAG}`

---

## Part 1 — Prerequisites

### 1.1 Install the IBM Cloud CLI + plugins

```bash
# macOS/Linux
curl -fsSL https://clis.cloud.ibm.com/install/osx | sh   # macOS
# or: curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

ibmcloud plugin install code-engine
ibmcloud plugin install container-registry
ibmcloud --version
```

> Alternatively use the browser-based [IBM Cloud Shell](https://cloud.ibm.com/shell),
> which has `ibmcloud` and the `ce` + `cr` plugins preinstalled. If you use Cloud
> Shell, clone this repo there.

### 1.2 Log in

```bash
ibmcloud login --sso          # federated / SSO accounts
# or, if you were issued an API key:
#   ibmcloud login --apikey <API_KEY>
```

Confirm what you can see (do this **before** editing `.env` — the correct values
differ per account):

```bash
ibmcloud resource groups      # NOTE: many accounts have NO "Default" group
ibmcloud regions              # pick one (us-east, us-south, eu-de, ...)
ibmcloud cr region            # shows your CURRENT ICR region + domain
ibmcloud cr namespace-list    # existing ICR namespaces (may be pre-provisioned)
```

> **Account-reality gotchas (learned from a live TechZone `itz-saas-*` run):**
> - **Resource group:** there may be **no `Default` group**. Accounts often expose
>   a single generated group like `eid-<hash>` — use that exact name for
>   `IBMCLOUD_RESOURCE_GROUP`, or `ibmcloud target -g` fails.
> - **ICR region is `global` (`icr.io`) by default** in these accounts, and is
>   **independent of `IBMCLOUD_REGION`**. A Code Engine app in `us-east` pushing
>   to the `global` registry is a valid, working pairing. Set `ICR_REGION` /
>   `ICR_DOMAIN` from what `ibmcloud cr region` reports. (`ibmcloud cr regions`
>   — plural — is **not** a command in current CLI versions.)
> - **Reuse a pre-provisioned namespace.** If `namespace-list` shows a shared
>   namespace (e.g. `gsa-hackathon-cr-erm1`), set `ICR_NAMESPACE` to it and reuse
>   it — you then don't need namespace-**create** authority at all.

> **Account authority required (this kit's whole point):** you need permission to
> create an ICR namespace (or Writer on an existing one) **and** to create an
> IAM API key for the push secret. These are the exact policies the trial account
> denied — see [`../internal/notes.md`](../internal/notes.md). If `namespace-add`
> or `api-key-create` fails with an authorization error, fall back to the
> `../prebuilt-image/` kit and ask your account admin for these policies.

> **Code Engine needs a paid (or trial-upgraded) account** — the free "Lite"
> account cannot create Code Engine projects.

### 1.3 Configure the deploy env file

```bash
cp ibm/code-engine-git-build/.env.example ibm/code-engine-git-build/.env
# edit ibm/code-engine-git-build/.env using the values you discovered above:
#   - IBMCLOUD_REGION / IBMCLOUD_RESOURCE_GROUP: from `ibmcloud regions` /
#     `ibmcloud resource groups` (NOT necessarily "Default" — see gotchas)
#   - GIT_REPO_URL / GIT_BRANCH: your PUBLIC repo/fork
#   - ICR_REGION / ICR_DOMAIN: from `ibmcloud cr region` (often global / icr.io)
#   - ICR_NAMESPACE: a pre-provisioned namespace from `ibmcloud cr namespace-list`
#     if one exists, else a name you have authority to create
#   - IMAGE_TAG, CE_REGISTRY_SECRET: image tag + CE secret name
source ibm/code-engine-git-build/.env
```

`ibm/code-engine-git-build/.env` holds **no secrets** — only coordinates. It is
git-ignored.

### 1.4 Provide an IBM Cloud API key (for the ICR push secret)

Code Engine needs credentials to **push** the built image to ICR. The deploy
script builds a registry secret from an IBM Cloud API key. Provide it via an
environment variable so it never touches disk:

```bash
export IBMCLOUD_API_KEY="$(ibmcloud iam api-key-create ce-icr-push \
    -d 'Code Engine ICR push' --output json | jq -r .apikey)"
```

If `IBMCLOUD_API_KEY` is unset, the script prompts for it (input hidden). Rotate
or delete the key when you're done: `ibmcloud iam api-key-delete ce-icr-push`.

---

## Part 2 — Deploy (build from Git)

### 2.1 Run the deploy script

```bash
source ibm/code-engine-git-build/.env
# (IBMCLOUD_API_KEY exported per 1.4, or you'll be prompted)
bash ibm/code-engine-git-build/deploy-build-from-git.sh
```

The script is idempotent and:

1. Verifies you're logged in; targets your region + resource group
2. **Ensures the ICR namespace** (`ICR_NAMESPACE`) exists — creates it if missing
3. **Creates/updates the Code Engine registry secret** (`CE_REGISTRY_SECRET`)
   from your API key so CE can push to ICR
4. Creates (or selects) the Code Engine project `CE_PROJECT`
5. Runs `ce app create/update --build-source ... --image <icr-ref>
   --registry-secret ...`: Code Engine clones the repo, builds the `Dockerfile`,
   pushes the image to ICR, and deploys it. The first build takes a few minutes;
   the CLI streams build + deploy progress.
6. Prints the public app URL and the ICR image reference

It sets `--min-scale 1` so one instance stays warm — avoiding a cold-start
timeout when the Orchestrate agent makes its first tool call mid-evaluation.

> **Worked example (this repo):** in `.env` set
> `GIT_REPO_URL=https://github.com/GSA-TTS/cdc-places-mcp-server` and
> `GIT_BRANCH=feat/ibm-code-engine-deploy`. For your own server, point these at
> your public fork.

> **Redeploy on push:** re-running the script rebuilds from the current branch
> tip — your "deploy latest" loop. For fully automated deploy-on-push, IBM offers
> the [Code Engine GitHub Action](https://github.com/IBM/code-engine-github-action).

### 2.2 Smoke-test the live endpoint

```bash
bash ibm/code-engine-git-build/smoke-test.sh https://<app>.<region>.codeengine.appdomain.cloud
```

Expected:
- `/health` → HTTP 200, `{"status":"healthy",...}`
- `/mcp` `tools/list` → advertises `get_cdc_places_data` and `area_summary_stats`

If health passes but `tools/list` returns
`{"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}` (the
smoke test prints a `WARN` for this), that is **expected, not a failure** —
FastMCP's streamable-HTTP transport requires an MCP `initialize` handshake before
`tools/list`, which a raw curl skips. Orchestrate performs the full handshake and
discovers the tools correctly. (This matches the observed behavior on the live
`us-east` deploy.)

You can also confirm the built image landed in ICR:

```bash
ibmcloud cr region-set "${ICR_REGION}"
ibmcloud cr images --restrict "${ICR_NAMESPACE}"
```

---

## Part 3 — Register in watsonx Orchestrate + evaluate

Registration in watsonx Orchestrate and evaluation against the gold dataset are
**identical regardless of how the server was deployed** (the Orchestrate side
only sees the public `/mcp` URL). Follow **Part 3 and Part 4** of the sibling
runbook — they apply unchanged here:

- [`../prebuilt-image/README.md`](../prebuilt-image/README.md) → *Part 3 —
  Register the server in watsonx Orchestrate* and *Part 4 — Evaluate against the
  gold dataset*.

Use the Code Engine URL this kit printed as the MCP endpoint.

---

## Teardown

```bash
source ibm/code-engine-git-build/.env
ibmcloud ce app delete --name "${CE_APP_NAME}" -f
# Optionally remove the CE registry secret and the whole project:
#   ibmcloud ce registry delete --name "${CE_REGISTRY_SECRET}" -f
#   ibmcloud ce project delete --name "${CE_PROJECT}" -f

# Optionally remove the pushed image / namespace from ICR:
ibmcloud cr region-set "${ICR_REGION}"
#   ibmcloud cr image-rm "${ICR_DOMAIN}/${ICR_NAMESPACE}/${CE_APP_NAME}:${IMAGE_TAG}"
#   ibmcloud cr namespace-rm "${ICR_NAMESPACE}"

# Delete the API key created for the push secret:
#   ibmcloud iam api-key-delete ce-icr-push
```

---

## Files in this directory

| File | Purpose |
|---|---|
| `.env.example` | Deployment coordinates template (copy to `.env`, no secrets) |
| `deploy-build-from-git.sh` | Idempotent build-from-Git deploy (namespace → registry secret → build+deploy) |
| `smoke-test.sh` | Live `/health` + `/mcp` verification |
| `README.md` | This runbook |

## Known gaps / notes

- **Public-repo only:** hackathon scope is public data, so the script does not
  wire up a Code Engine Git secret. A private repo would additionally need
  `ibmcloud ce secret create` (SSH/token) and `--build-git-repo-secret` on the
  app create/update.
- **API key handling:** the IBM Cloud API key is read from `IBMCLOUD_API_KEY` or
  prompted (hidden) and **never written to disk**. Rotate/delete it when done.
- **Region pairing:** the ICR region is **independent** of the Code Engine
  region. A verified working pairing is **Code Engine in `us-east` pushing to the
  `global` registry (`icr.io`)** — common in TechZone / `itz-saas-*` accounts.
  Set `ICR_REGION` / `ICR_DOMAIN` from `ibmcloud cr region`; you do **not** have
  to co-locate them with `IBMCLOUD_REGION`.
- **Authentication to the MCP server:** the endpoint is exposed publicly with no
  auth (matches the pilot posture). For anything beyond a hackathon, front it
  with auth and pass credentials via an Orchestrate connection.
