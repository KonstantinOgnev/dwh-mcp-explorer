ALLOWED_TOOLS = {
    "databricks_describe_table",
    "databricks_get_table_lineage",
    "databricks_get_column_lineage",
    "databricks_validate_grain",
}


async def get_agent_tools(client) -> list[dict]:
    result = await client.list_tools()

    available = {tool.name: tool for tool in result.tools}
    missing = ALLOWED_TOOLS - available.keys()

    if missing:
        raise RuntimeError(
            f"Required MCP tools are missing: {sorted(missing)}"
        )

    return [
        {
            "name": name,
            "description": available[name].description or name,
            "input_schema": available[name].input_schema,
        }
        for name in sorted(ALLOWED_TOOLS)
    ]