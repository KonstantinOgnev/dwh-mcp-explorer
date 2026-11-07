
import asyncio
import json

from mcp import Client
from server import mcp


def extract_result(result):
    if result.is_error:
        raise RuntimeError(str(result.content))

    if result.structured_content is not None:
        return result.structured_content

    for block in result.content:
        if block.type == "text":
            return json.loads(block.text)

    raise ValueError("No usable tool result")


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        response = await client.list_tools()
        tool_names = {tool.name for tool in response.tools}

        assert len(tool_names) >= 17, (
            f"Expected at least 17 MCP tools, found {len(tool_names)}"
        )

        assert "investigate_dwh_object" in tool_names
        assert "databricks_investigate_object" in tool_names
        assert "databricks_validate_grain" in tool_names

        databricks_tools = {
            "databricks_list_catalogs",
            "databricks_list_schemas",
            "databricks_list_tables",
            "databricks_describe_table",
        }

        assert databricks_tools.issubset(tool_names), (
            "Missing Databricks MCP tools: "
            f"{databricks_tools - tool_names}"
        )
        assert "investigate_dwh_object" in tool_names

        print("PASS: 17 MCP tools registered")

        result = await client.call_tool(
            "investigate_dwh_object",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql",
            },
        )

        data = extract_result(result)

        assert data["object"] == "gold.fact_orders"
        assert data["overall_status"] == "WARNING"
        assert data["investigation_status"] == "completed"
        assert data["summary"]["column_count"] == 5

        print("PASS: Composite MCP tool invocation")
        print("PASS: Investigation output contract")
        print("STAGE 5.3.1 VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
