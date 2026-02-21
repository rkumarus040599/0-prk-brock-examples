# from mcp.server.fastmcp import FastMCP

# #mcp = FastMCP("phase2b-mcp")
# mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# @mcp.tool()
# def ping() -> str:
#     """
#     Simple connectivity check tool for MCP.
#     """
#     return "Ping successful"
    
# if __name__ == "__main__":
#     mcp.run(transport="streamable-http")

from mcp import run
from gateway_mcp_server import server  # your MCP server implementation

if __name__ == "__main__":
    run(
        server=server,
        transport="streamable-http",
    )
