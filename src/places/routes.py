from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

def register_routes(mcp: FastMCP) -> None:

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy", "service": "nih-reporter-mcp-server"})