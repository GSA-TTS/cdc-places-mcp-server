## MCP Server for the CDC PLACES Dataset

WARNING: This is a proof of concept and is not intended for production use.

A Model Context Protocol (MCP) server that provides access to the CDC PLACES dataset for health statistics and outcomes data across US geographic areas.

#### Overview

The CDC PLACES dataset provides model-based estimates for chronic disease risk factors, health outcomes, and clinical preventive service use for all 50 states, the District of Columbia, and 500 of the largest US cities and census places. This MCP server exposes that data to MCP clients over either `stdio` or HTTP.

#### Disclaimer

This MCP is a pilot project and is under development. The developers bear no responsibility for the accuracy of the data returned from the tool.

## Local Install

This project targets Python `3.13` and uses `uv` for dependency management.

```powershell
uv sync
```

If you are not using `uv`, create a Python `3.13` virtual environment and install the project in editable mode.

## Launch Modes

The server supports two runtime modes:

- `stdio` for local MCP clients
- HTTP for hosted deployment or manual health checks

### Local MCP (`stdio`)

Recommended launch command:

```powershell
uv run --directory . python -m places
```

Equivalent commands:

```powershell
uv run python -m places.app
uv run places-mcp
```

### Local HTTP

Set `PORT` and launch the same module:

```powershell
$env:PORT = "8000"
uv run python -m places
```

Health check:

```text
http://127.0.0.1:8000/health
```

## OpenAI / Codex MCP Registration

For Codex CLI, prefer registering the local server with the repo's virtual environment Python directly:

```powershell
codex mcp add cdc-places -- C:/Users/wsn8/code/cdc-places-mcp-server/.venv/Scripts/python.exe -m places
```

This is the most reliable Windows option because it avoids `uv` path lookup and `--directory` path parsing issues.

If you prefer `uv`, use forward slashes in the directory path:

```powershell
codex mcp add cdc-places -- uv run --directory C:/Users/wsn8/code/cdc-places-mcp-server python -m places
```

Equivalent JSON-shaped configuration:

```json
{
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "C:\\Users\\wsn8\\code\\cdc-places-mcp-server",
    "python",
    "-m",
    "places"
  ]
}
```

This starts the server over `stdio`, which is the expected transport for a local MCP client process.

To inspect the saved registration:

```powershell
codex mcp get cdc-places --json
```

## Notes

- `src/places/app.py` is the actual server entrypoint.
- `server.json` points at the hosted remote deployment; it is not used for local `stdio` startup.
- Tool execution requires outbound access to the CDC Socrata API at `data.cdc.gov`.
