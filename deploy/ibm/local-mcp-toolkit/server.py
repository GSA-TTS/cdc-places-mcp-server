#!/usr/bin/env python
"""Local MCP toolkit entrypoint for watsonx Orchestrate (stdio transport).

watsonx Orchestrate runs a LOCAL MCP toolkit by starting this script inside its
own runtime and speaking MCP over stdio (stdin/stdout). This entrypoint reuses
the EXISTING FastMCP server defined in the `places` package and runs it over
stdio — no HTTP, no Code Engine, no container.

The register script stages this file NEXT TO the `places` package (flattened out
of the repo's src/ layout), so `places` is importable from this script's own
directory. We add that directory to sys.path defensively in case Orchestrate
runs the command from a different working directory.

Contrast with the other kits:
  - ibm/code-engine-git-build/ and ibm/prebuilt-image/ deploy an HTTP server to
    IBM Code Engine and register it as a REMOTE MCP toolkit (URL).
  - THIS kit ships the server code to Orchestrate and runs it LOCALLY (stdio).

Orchestrate invokes:  python server.py
"""

import os
import sys

# Ensure the directory containing this file (which also contains the `places`
# package after staging) is importable, regardless of the runtime CWD.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from places.app import mcp

if __name__ == "__main__":
    # stdio is the transport watsonx Orchestrate uses for local MCP toolkits.
    mcp.run(transport="stdio")
