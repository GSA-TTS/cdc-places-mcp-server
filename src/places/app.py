from fastmcp import FastMCP
from places.tools import register_tools
from starlette.responses import JSONResponse
import os 

# Initialize FastMCP server
mcp = FastMCP("places")

register_tools(mcp)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

app = mcp.http_app(stateless_http=True)

if __name__ == "__main__":
    port_env = os.environ.get("DATABRICKS_APP_PORT") or os.environ.get("PORT")
    if port_env:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(port_env))
    else:
        mcp.run(transport="stdio")