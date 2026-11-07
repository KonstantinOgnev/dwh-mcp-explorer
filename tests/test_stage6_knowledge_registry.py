import asyncio

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        tools_result = await client.list_tools()

        names = {tool.name for tool in tools_result.tools}

        assert "databricks_investigate_object" in names, (
            "Knowledge Base tool is not registered"
        )

        assert len(names) >= 20, (
            f"Expected at least 20 MCP tools, found {len(names)}"
        )

        assert "databricks_investigate_object" in names
        assert "databricks_validate_grain" in names


        print("REGISTERED MCP TOOLS:", len(names))
        print("KNOWLEDGE TOOL: databricks_investigate_object")
        print("STAGE 6.6.5: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
