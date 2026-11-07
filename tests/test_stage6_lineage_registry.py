
import asyncio

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()
        names = {tool.name for tool in result.tools}

        expected = {
            "databricks_get_table_lineage",
            "databricks_get_column_lineage",
        }

        assert len(names) == 19, names
        assert expected.issubset(names), expected - names

        print("PASS: 19 MCP tools registered")
        print("PASS: 2 Databricks Lineage tools discovered")
        print("STAGE 6.5.7 REGISTRY VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
