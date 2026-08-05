---
title: "IBM Cloud Deployment + watsonx Orchestrate Evaluation"
description: "Deploy the CDC PLACES MCP server to IBM Code Engine and evaluate it with watsonx Orchestrate"
status: draft
tier: 2
last_updated: "2026-08-05"
---

# IBM Cloud Deployment + watsonx Orchestrate Evaluation

This runbook takes an MCP server from a **public Git repo** to a running,
publicly reachable MCP endpoint on **IBM Cloud Code Engine**, then registers it
as a tool in **watsonx Orchestrate (SaaS)** and runs the gold-standard evaluation
questions against an agent. The CDC PLACES server is used as the worked example.

> **Hackathon workflow this fits:** participants build locally → deploy to a cloud
> environment (here, IBM) → run agent experiments over gold datasets to verify the
> server lets the agent answer correctly. This is the IBM leg of that loop.

## Two ways to deploy

Code Engine can deploy **directly from a Git repo** — it clones your repo and
builds the Dockerfile server-side, so you need **no local Docker and no image
registry**. That is the default, plug-and-play path (closest to a cloud.gov
`cf push` experience). A prebuilt-image path is also supported for pinned
releases.

| Path | How | Local Docker? | When |
|---|---|---|---|
| **A — Git build (default)** | CE clones `GIT_REPO_URL`, builds its `Dockerfile` | No | Hackathon default: point at your public fork and go |
| **B — Prebuilt image** | CE deploys `IMAGE` directly | Yes (to build/push it) | Pinned, reproducible release from a public registry |

You choose the path in `ibm/.env`: leave `IMAGE` empty to use Git build (A);
set `IMAGE` to use the prebuilt image (B).

## What gets deployed (CDC PLACES example)

- **Repo:** any public repo with a Dockerfile that serves MCP (this repo is one)
- **Transport:** MCP over streamable-HTTP at `/mcp`; health check at `/health`
- **Port:** `8080` (set by the `Dockerfile`)
- **Tools:** `get_cdc_places_data`, `area_summary_stats`

---

## Part 1 — Prerequisites (starting from nothing)

You said you have IBM Cloud console/credential access but no CLI set up yet.
Start here.

### 1.1 Install the IBM Cloud CLI + Code Engine plugin

```bash
# macOS/Linux
curl -fsSL https://clis.cloud.ibm.com/install/osx | sh   # macOS
# or: curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

ibmcloud plugin install code-engine
ibmcloud --version
```

> Alternatively, skip local install entirely and use the browser-based
> [IBM Cloud Shell](https://cloud.ibm.com/shell) — it has `ibmcloud` and the
> `ce` plugin preinstalled. If you use Cloud Shell, clone this repo there.

### 1.2 Log in

```bash
ibmcloud login --sso          # federated / SSO accounts (most GSA vendor tenants)
# or, if you were issued an API key:
#   ibmcloud login --apikey <API_KEY>
```

Confirm what you can see:

```bash
ibmcloud resource groups      # note the group name (often "Default")
ibmcloud regions              # pick one near you (us-south, us-east, eu-de, ...)
```

> **Code Engine needs a paid (or trial-upgraded) account** — the free "Lite"
> account cannot create Code Engine projects. If `ce project create` later fails
> with a billing error, that's the cause.

### 1.3 Configure the deploy env file

```bash
cp ibm/.env.example ibm/.env
# edit ibm/.env:
#   - IBMCLOUD_REGION / IBMCLOUD_RESOURCE_GROUP: match `ibmcloud regions` /
#     `ibmcloud resource groups`
#   - Path A (default): set GIT_REPO_URL to your PUBLIC repo/fork and GIT_BRANCH.
#     Leave IMAGE empty.
#   - Path B (prebuilt image): set IMAGE=<public image ref>; Git vars are ignored.
source ibm/.env
```

`ibm/.env` holds **no secrets** — only region/project/repo/image coordinates.
Your credentials live in the `ibmcloud login` session, not in the file.
(`ibm/.env` is git-ignored.)

---

## Part 2 — Deploy to Code Engine

### 2.1 Run the deploy script

```bash
source ibm/.env
bash ibm/deploy-code-engine.sh
```

The script is idempotent and picks the path from `ibm/.env`:

1. Verifies you're logged in and targets your region + resource group
2. Creates (or selects) the Code Engine project `CE_PROJECT`
3. **Path A (Git build):** hands CE your `GIT_REPO_URL` + branch; CE clones and
   builds the `Dockerfile` server-side, then deploys the resulting image.
   The first build takes a few minutes; the CLI streams build + deploy progress.
   **Path B (image):** deploys `IMAGE` directly.
4. Prints the public app URL

It sets `--min-scale 1` so one instance stays warm — this avoids a cold-start
timeout when the Orchestrate agent makes its first tool call mid-evaluation.

> **Path A worked example (this repo):** in `ibm/.env` set
> `GIT_REPO_URL=https://github.com/GSA-TTS/cdc-places-mcp-server` and
> `GIT_BRANCH=feat/ibm-code-engine-deploy`, leave `IMAGE` empty, then run the
> script. For your own hackathon server, point these at your public fork instead.

> **Redeploy on push:** re-running the script with Path A rebuilds from the
> current branch tip — that's your "deploy latest" loop. (For fully automated
> deploy-on-push, IBM offers the
> [Code Engine GitHub Action](https://github.com/IBM/code-engine-github-action).)

### 2.2 Smoke-test the live endpoint

```bash
# Use the App URL the deploy script printed:
bash ibm/smoke-test.sh https://<app>.<region>.codeengine.appdomain.cloud
```

Expected:
- `/health` → HTTP 200, `{"status":"healthy",...}`
- `/mcp` `tools/list` → advertises `get_cdc_places_data` and `area_summary_stats`

If health passes but `tools/list` doesn't (FastMCP may require an MCP
`initialize` handshake first over a raw curl), that's fine — Orchestrate speaks
the full MCP handshake and will discover the tools correctly in Part 3.

---

## Part 3 — Register the server in watsonx Orchestrate (SaaS)

watsonx Orchestrate imports a **remote MCP server** as a **toolkit**. The cleanest,
most reproducible path is the ADK CLI (`orchestrate`), which works against the
SaaS instance the same way it works locally.

### 3.1 Install the ADK

```bash
# Python 3.11–3.14
pip install --upgrade ibm-watsonx-orchestrate
orchestrate --version
```

### 3.2 Point the ADK at your SaaS instance

In the Orchestrate SaaS UI: **Settings → API details** (or your instance's
"about"/settings page). Copy the **service instance URL** and generate/copy an
**API key**.

```bash
orchestrate env add --name ibm-saas --url "<YOUR_ORCHESTRATE_INSTANCE_URL>"
orchestrate env activate ibm-saas --api-key "<YOUR_ORCHESTRATE_API_KEY>"
orchestrate env list        # confirm ibm-saas is active
```

### 3.3 Add the CDC PLACES MCP server as a toolkit

The server is a **remote streamable-HTTP** MCP endpoint (the Code Engine URL),
so use `--url` + `--transport streamable_http`, and import all tools with `-t "*"`:

```bash
orchestrate toolkits add \
  --kind mcp \
  --name cdc_places \
  --description "CDC PLACES health statistics (get_cdc_places_data, area_summary_stats)" \
  --url "https://<app>.<region>.codeengine.appdomain.cloud/mcp" \
  --transport streamable_http \
  --tools "*"

orchestrate toolkits list    # confirm cdc_places is present with 2 tools
```

> If your Orchestrate version requires the MCP path without `/mcp`, or reports a
> transport mismatch, re-run with the base URL or `--transport sse`. `sse` and
> `streamable_http` are the two supported remote transports.

### 3.4 Create an agent that uses the toolkit

In the Orchestrate UI, create (or edit) an agent and **add the `cdc_places`
tools** to it. Give it a system instruction aligned with the eval harness:

```
You are an expert data retriever for the CDC PLACES dataset.
Use the cdc_places tools to answer questions with specific numeric values.
```

Chat-test it in the UI with one gold question before running the full set:

> *"What percent of adults had short sleep durations in Kauai County, Hawaii in 2018?"*
> (Gold answer: **36.9**)

---

## Part 4 — Evaluate against the gold dataset

The gold questions live in `eval/phoenix/datasets/places-eval-0/places-eval-0.csv`
(10 Q/A pairs) — the same set the repo's Phoenix harness uses. You have two ways
to evaluate on IBM:

### Option A — Orchestrate's built-in evaluations (native)

The ADK ships `orchestrate evaluations evaluate`, which runs test cases against
an agent in your active env and scores tool calls + final answers.

**A.1 — Convert each gold Q/A into a test-case JSON.** Orchestrate expects one
JSON file per test case (a directory of them is fine). Each file names the agent,
the user story, the expected tool call(s), and keywords the final answer must
contain. For the first gold row it looks like:

```json
{
  "agent": "cdc_places_agent",
  "goals": {
    "get_cdc_places_data": ["summarize"]
  },
  "goal_details": [
    {
      "type": "tool_call",
      "name": "get_cdc_places_data",
      "tool_name": "get_cdc_places_data",
      "args": {
        "year": "2018",
        "measureid": "SLEEP",
        "geo": "county",
        "datavaluetypeid": "CrdPrv",
        "locationname": "Kauai"
      }
    },
    {
      "type": "text",
      "name": "summarize",
      "response": "About 36.9% of adults had short sleep duration in Kauai County, Hawaii in 2018.",
      "keywords": ["36.9"]
    }
  ],
  "story": "What percent of adults had short sleep durations in Kauai County, Hawaii in 2018?",
  "starting_sentence": "I have a question about CDC PLACES data."
}
```

> The `keywords` array is what makes scoring objective — the gold numeric answer
> (`36.9`) must appear in the agent's final response. For questions where the
> exact tool args are hard to predict, you can omit the `tool_call` goal and keep
> only the `text` goal with keywords, which grades the final answer alone.

Put your test-case files (one per gold question) in a directory, e.g. `ibm/eval/`.

**A.2 — Provide watsonx credentials.** Create a `.env` for the evaluator with
your SaaS instance + key (these are read by the evaluator, distinct from the
`orchestrate env` you activated):

```bash
# ibm/eval.env  (git-ignored — do NOT commit)
WO_INSTANCE=<YOUR_ORCHESTRATE_INSTANCE_URL>
WO_API_KEY=<YOUR_ORCHESTRATE_API_KEY>
```

**A.3 — Run the evaluation** (non-legacy pipeline scores against the live agent):

```bash
export USE_LEGACY_EVAL=FALSE
orchestrate evaluations evaluate \
  --test-paths ./ibm/eval \
  --output-dir ./ibm/eval-results \
  --env-file ./ibm/eval.env
```

Review per-question pass/fail and tool-call traces in `./ibm/eval-results` and in
the Orchestrate UI. Add `-l` (and start the server with Langfuse) if you want the
scored traces in a Langfuse dashboard.

### Option B — Reuse the repo's agent harness, pointed at the IBM endpoint

The existing `eval/phoenix/agent.py` already drives an agent over the MCP server
and scores it with an LLM judge (`match_expected_response`). It currently points
at a local server (`http://localhost:8000/mcp`). To evaluate the **IBM-deployed**
server instead, change the MCP URL to your Code Engine endpoint:

```python
# eval/phoenix/agent.py
"places_server": {
    "transport": "http",
    "url": "https://<app>.<region>.codeengine.appdomain.cloud/mcp",
},
```

Then run the experiment as documented in `eval/phoenix`:

```bash
uv run eval/phoenix/run_experiment.py --dataset-name places-eval-0
```

This exercises the *same* deployed server the Orchestrate agent uses, so a pass
here corroborates the Orchestrate result. (Note this harness uses the USAi model
gateway via `USAI_API_KEY`, not watsonx's LLM — use Option A if you want the
agent's *reasoning* model to be watsonx-hosted too.)

> **Recommendation for this pilot:** use **Option A** to prove the end-to-end
> IBM/watsonx path (agent reasoning + tool calls both on IBM), and keep **Option B**
> as a cross-check that the deployed endpoint returns correct data independent of
> the orchestration platform.

---

## Teardown

```bash
source ibm/.env
ibmcloud ce app delete --name "${CE_APP_NAME}" -f
# Optionally remove the whole project (deletes all apps in it):
#   ibmcloud ce project delete --name "${CE_PROJECT}" -f

# Remove the Orchestrate toolkit:
orchestrate toolkits remove --name cdc_places
```

---

## Files in this directory

| File | Purpose |
|---|---|
| `.env.example` | Deployment coordinates template (copy to `.env`, no secrets) |
| `deploy-code-engine.sh` | Idempotent deploy — Git build (default) or prebuilt image |
| `smoke-test.sh` | Live `/health` + `/mcp` verification |
| `README.md` | This runbook |

## Known gaps / notes

- **Git build path is public-repo only:** the hackathon scope is public data, so
  the deploy script assumes public repos and does not wire up a Code Engine Git
  secret. A private repo would additionally need `ibmcloud ce secret create`
  (SSH/token) and `--build-git-repo-secret` on the app create/update.
- **Version-specific Orchestrate flags:** the `orchestrate toolkits add` flags
  above match the current ADK (`--kind mcp`, `--transport streamable_http|sse`,
  `--tools "*"`). If your SaaS tenant pins an older ADK, run
  `orchestrate toolkits add --help` and adjust.
- **Authentication to the MCP server:** this deployment exposes the MCP endpoint
  publicly with no auth (matches the repo's cloud.gov posture for the pilot). For
  anything beyond a hackathon, front it with auth (e.g. Code Engine
  `auth-oidc-proxy` sample) and pass credentials via an Orchestrate connection
  (`orchestrate connections`).
- **Gold-answer drift:** `eval/mcp-data-check/questions.csv` and the Phoenix CSV
  disagree on two rows (Nassau NY year: 2021 vs 2022; Vermont IQR: 4 vs 4.85)
  because they were built against different PLACES releases. Pick one release's
  gold set per experiment so scoring is apples-to-apples.
