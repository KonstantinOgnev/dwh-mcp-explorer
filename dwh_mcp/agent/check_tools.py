import asyncio

from mcp import Client
from server import mcp
from dwh_mcp.agent.mcp_client import get_agent_tools


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await get_agent_tools(client)

        print("Tools exposed to the agent:")
        for tool in tools:
            print(f" - {tool['name']}")
            print(
                "   Parameters:",
                list(tool["input_schema"].get("properties", {})),
            )


if __name__ == "__main__":
    asyncio.run(main())