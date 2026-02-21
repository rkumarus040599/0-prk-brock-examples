import asyncio
from fastmcp import Client

# Update this URL if your server is bound differently
MCP_URL = "http://127.0.0.1:8000/mcp"

async def main():
    # Connect directly to your HTTP MCP server
    client = Client(MCP_URL)

    async with client:
        # Optional: initialize explicitly (usually happens automatically)
        await client.initialize()

        # 1) List tools
        tools = await client.list_tools()
        print("Tools from server:")
        for t in tools:
            print("-", t.name)

        # 2) Call the ping tool if it exists
        if any(t.name == "ping" for t in tools):
            result = await client.call_tool("ping", {"message": "hello from client"})
            print("Ping result:", result)
        else:
            print("No 'ping' tool found on the server.")

if __name__ == "__main__":
    asyncio.run(main())
