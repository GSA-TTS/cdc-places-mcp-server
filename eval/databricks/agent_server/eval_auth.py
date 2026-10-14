"""Eval-time auth shim for the Databricks-generated agent.

WHY THIS FILE EXISTS
--------------------
The agent.py produced by Databricks' "generate agent from code" feature ships
with:

    def get_mcp_user_workspace_client():
        # Uncomment the line below to enable on-behalf-of-user authentication
        # return get_user_workspace_client()
        return None

Returning ``None`` means the agent sends NO credential to your deployed MCP
server (a Databricks App). Databricks Apps are OAuth-gated, so the MCP
connection silently fails ("Failed to connect MCP server") and the agent runs
with ZERO tools -- it will answer from base-model knowledge and your eval will
look like the agent "has no tools".

On-Behalf-Of (OBO) auth does not help for an OFFLINE eval: OBO reads the
``x-forwarded-access-token`` request header, which only exists when a real user
calls the deployed app over HTTP. A notebook eval calls invoke() in-process with
no request, so there is no header to forward. A plain notebook identity also
cannot mint an OAuth token ("OAuth tokens are not available for runtime
authentication"), so it cannot reach the app either.

The only identity that reliably reaches a deployed Databricks App from an
offline eval is a SERVICE PRINCIPAL using OAuth machine-to-machine (M2M).

WHAT THIS FILE DOES
-------------------
It leaves the generated agent.py UNTOUCHED. Instead it monkeypatches the
agent module's ``get_mcp_user_workspace_client`` to return an authenticated
service-principal WorkspaceClient. The generated ``init_mcp_servers()`` calls
that function by name, so the patch takes effect with no edits to agent.py.

USAGE (from the eval script)
----------------------------
    import agent_server.agent as agent
    from agent_server.eval_auth import patch_agent_with_service_principal

    patch_agent_with_service_principal(
        agent,
        host="https://<workspace>.cloud.databricks.com",
        client_id="<sp application id>",
        client_secret="<sp oauth secret>",
    )
    # now agent.invoke(...) reaches the MCP app as the service principal
"""

from __future__ import annotations

from typing import Optional

from databricks.sdk import WorkspaceClient


def build_service_principal_client(
    host: str,
    client_id: str,
    client_secret: str,
) -> WorkspaceClient:
    """Return a machine-to-machine (OAuth M2M) service-principal client.

    This is the identity that is accepted by a deployed Databricks App MCP
    server. The service principal must have been granted ``Can Use`` on the app
    (plus the usual workspace-access entitlement) or requests will 403.
    """
    return WorkspaceClient(
        host=host,
        client_id=client_id,
        client_secret=client_secret,
        auth_type="oauth-m2m",
    )


def patch_agent_with_service_principal(
    agent_module,
    host: str,
    client_id: str,
    client_secret: str,
) -> WorkspaceClient:
    """Monkeypatch the generated agent module to authenticate as an SP.

    Replaces ``agent_module.get_mcp_user_workspace_client`` so that
    ``init_mcp_servers()`` builds each ``McpServer`` with an authenticated
    service-principal ``workspace_client``. The generated agent.py is not
    modified on disk.

    Returns the built WorkspaceClient so the caller can, if desired, sanity-check
    auth (e.g. ``client.current_user.me()``) before running the eval.
    """
    sp_client = build_service_principal_client(host, client_id, client_secret)

    def _get_mcp_user_workspace_client() -> Optional[WorkspaceClient]:
        return sp_client

    agent_module.get_mcp_user_workspace_client = _get_mcp_user_workspace_client
    return sp_client
