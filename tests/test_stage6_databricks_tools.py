
import asyncio
import json

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        response = await client.list_tools()
        names = {tool.name for tool in response.tools}

        expected = {
            "databricks_list_catalogs",
            "databricks_list_schemas",
            "databricks_list_tables",
            "databricks_describe_table",
        }

        assert expected.issubset(names), expected - names
        print("PASS: 4 Databricks MCP tools registered")

        result = await client.call_tool(
            "databricks_describe_table",
            {
                "full_name": "marketplace_lab.gold.fact_orders"
            },
        )

        assert not result.is_error, result

        if result.structured_content:
            data = result.structured_content
        else:
            data = json.loads(result.content[0].text)

        # Некоторые MCP-клиенты оборачивают словарь в result.
        if isinstance(data, dict) and "result" in data:
            data = data["result"]

        assert data["full_name"] == (
            "marketplace_lab.gold.fact_orders"
        )
        assert data["table_type"] == "MANAGED"
        assert data["data_source_format"] == "DELTA"
        assert len(data["columns"]) == 26

        print("PASS: Databricks MCP tool executed")
        print("PASS: Unity Catalog metadata validated")
        print("STAGE 6.4.3 VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
