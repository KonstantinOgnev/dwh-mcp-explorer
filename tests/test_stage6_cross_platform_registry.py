
import asyncio

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        response = await client.list_tools()

    names = {tool.name for tool in response.tools}

    required_tools = {
        # PostgreSQL / DWH tools
        "list_schemas",
        "list_tables",
        "describe_table",
        "get_primary_keys",
        "get_foreign_keys",
        "investigate_dwh_object",

        # Databricks tools
        "databricks_list_catalogs",
        "databricks_list_schemas",
        "databricks_list_tables",
        "databricks_describe_table",
        "databricks_get_table_lineage",
        "databricks_get_column_lineage",
        "databricks_investigate_object",
        "databricks_validate_grain",
    }

    missing = required_tools - names

    assert not missing, (
        f"Missing MCP tools: {sorted(missing)}"
    )

    print("REGISTERED MCP TOOLS:", len(names))
    print("POSTGRESQL / DWH TOOLS: AVAILABLE")
    print("DATABRICKS TOOLS: AVAILABLE")
    print("STAGE 6.8.2: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
