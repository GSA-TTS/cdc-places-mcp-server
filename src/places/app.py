from fastmcp import FastMCP
from places.tools import register_tools
from starlette.responses import JSONResponse

# Initialize FastMCP server
mcp = FastMCP("places",stateless_http=True)
# mcp = FastMCP("places")

register_tools(mcp)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

# Create ASGI app for deployment
app = mcp.http_app()

# for local testing 
# if __name__ == "__main__":
#     # Initialize and run the server
#     mcp.run(transport='stdio')