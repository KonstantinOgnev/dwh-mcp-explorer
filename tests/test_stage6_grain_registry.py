
import asyncio

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        tools_result = await client.list_tools()

        names = {
            tool.name
            for tool in tools_result.tools
        }

        assert "databricks_validate_grain" in names, (
            "Grain validation tool is not registered"
        )

        assert len(names) == 21, (
            f"Expected 21 MCP tools, found {len(names)}"
        )

    print("REGISTERED MCP TOOLS:", len(names))
    print("GRAIN TOOL: databricks_validate_grain")
    print("STAGE 6.7.7: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
