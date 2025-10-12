from typing import Dict, Any, Optional, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.core.utils.settings import get_settings

_mcp_client = None
_mcp_tools = []

async def initialize_mcp_client():
    """
    Initializes the Multi-Server MCP Client.
    This client is used to interact with various MCP servers (e.g., 'singtel_mcp_server').
    It attempts to load tools from configured MCP servers.
    """
    global _mcp_client, _mcp_tools

    if _mcp_client is None:
        settings = get_settings()
        _mcp_client = MultiServerMCPClient(
            {
                "tutornet_mcp_server": {
                    "url": settings.mcp_url,
                    "transport": "streamable_http"
                }
            }
        )
        try:
            _mcp_tools = await _mcp_client.get_tools()
            # Log successful loading of tools
            # print(f"Successfully loaded {len(_mcp_tools)} MCP tools.")
        except Exception as e:
            # Log failure to load tools
            print(f"Failed to load MCP tools-client: {e}")
            _mcp_tools = []

def get_mcp_client():
    """
    Returns the initialized MCP client and its loaded tools.

    Returns:
        Tuple[MultiServerMCPClient, List[Any]]: The MCP client instance and a list of its tools.
    """
    global _mcp_client, _mcp_tools
    return _mcp_client, _mcp_tools
