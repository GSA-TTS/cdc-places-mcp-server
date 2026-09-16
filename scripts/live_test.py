"""Live-test the running PLACES MCP server over HTTP.

Usage:
    .venv-linux/bin/python scripts/live_test.py [BASE_URL]

Connects to the server's MCP endpoint, lists tools, and calls
get_cdc_places_data so you can verify the {data, citation} response
against the real CDC PLACES API.
"""

import asyncio
import json
import sys

from fastmcp import Client

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp/"


async def main():
    async with Client(BASE_URL) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        result = await client.call_tool(
            "get_cdc_places_data",
            {
                "geo": "county",
                "year": "2020",
                "measureid": "CSMOKING",
                "datavaluetypeid": "CrdPrv",
                "locationname": "Wayne",
            },
        )

        payload = result.structured_content or result.data
        print("\n--- citation ---")
        print(json.dumps(payload["citation"], indent=2))
        print("\n--- first data record ---")
        data = payload["data"]
        print(json.dumps(data[0] if data else data, indent=2))
        print(f"\nrecord count: {len(data) if data else 0}")


if __name__ == "__main__":
    asyncio.run(main())
