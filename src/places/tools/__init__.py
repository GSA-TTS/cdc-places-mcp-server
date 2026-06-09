"""
Tools module for CDC PLACES MCP server.

This module provides tools for querying the CDC PLACES API.
Each tool is defined in its own file for better organization and maintainability.
"""

from places.tools import get_cdc_places_data, area_summary_stats


def register_tools(mcp):
    """
    Register all tools with the MCP server.
    
    This function maintains backward compatibility with the original tools.py interface.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    # Register individual tools
    get_cdc_places_data.register(mcp)
    area_summary_stats.register(mcp)


__all__ = ['register_tools']
