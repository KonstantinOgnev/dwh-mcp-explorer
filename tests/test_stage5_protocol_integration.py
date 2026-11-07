
import asyncio
import json

from mcp import Client
from server import mcp


def extract_result(result):
    """Extract structured or JSON-text MCP tool output."""
    if result.is_error:
        raise RuntimeError(str(result.content))

    if result.structured_content is not None:
        return result.structured_content

    for block in result.content:
        if block.type == "text":
            return json.loads(block.text)

    raise AssertionError("Tool returned no usable content")


async def main():
    async with Client(mcp, raise_exceptions=True) as client:

        # 1. Check Tools
        tools_response = await client.list_tools()
        tool_names = {tool.name for tool in tools_response.tools}

        assert len(tool_names) == 13
        assert "investigate_dwh_object" in tool_names
        print("PASS: MCP tools discovered")

        # 2. Check Static Resource
        resources = await client.list_resources()
        resource_uris = {
            str(item.uri) for item in resources.resources
        }

        assert "dwh://explorer/capabilities" in resource_uris

        capabilities = await client.read_resource(
            "dwh://explorer/capabilities"
        )

        capability_data = json.loads(
            capabilities.contents[0].text
        )
        assert capability_data["sql_execution"] is False
        print("PASS: Static resource accessible")

        # 3. Check Dynamic Resource Template
        templates = await client.list_resource_templates()

        template_uris = {
            str(item.uri_template)
            for item in templates.resource_templates
        }
        assert "dwh://tables/{schema}/{table}" in template_uris

        table_resource = await client.read_resource(
            "dwh://tables/gold/fact_orders"
        )

        table_data = json.loads(table_resource.contents[0].text)

        assert table_data["object"] == "gold.fact_orders"
        assert len(table_data["columns"]) == 5
        print("PASS: Dynamic resource accessible")

        # 4. Check Prompt
        prompts = await client.list_prompts()
        prompt_names = {item.name for item in prompts.prompts}

        assert "investigate_dwh_table" in prompt_names

        prompt = await client.get_prompt(
            "investigate_dwh_table",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        assert "investigate_dwh_object" in (
            prompt.messages[0].content.text
        )
        print("PASS: MCP prompt accessible")

        # 5. Execute Composite Tool
        tool_result = await client.call_tool(
            "investigate_dwh_object",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        investigation = extract_result(tool_result)

        assert investigation["object"] == "gold.fact_orders"
        assert investigation["investigation_status"] == "completed"
        assert investigation["overall_status"] == "WARNING"
        assert investigation["summary"]["column_count"] == 5

        print("PASS: Composite MCP tool executed")
        print("PASS: Investigation result validated")
        print("STAGE 5.3.4 PROTOCOL INTEGRATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
