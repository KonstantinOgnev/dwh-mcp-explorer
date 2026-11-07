
import asyncio
import json
from pathlib import Path

from mcp import Client, StdioServerParameters


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
SERVER_FILE = PROJECT_ROOT / "server.py"


async def main():
    assert PYTHON_EXE.is_file(), "Python executable not found"
    assert SERVER_FILE.is_file(), "server.py not found"

    server_params = StdioServerParameters(
        command=str(PYTHON_EXE),
        args=[str(SERVER_FILE)],
        cwd=str(PROJECT_ROOT)
    )

    async with Client(server_params, raise_exceptions=True) as client:

        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools.tools}

        assert len(tool_names) == 13
        assert "investigate_dwh_object" in tool_names

        print("PASS: STDIO server started")
        print("PASS: 13 MCP tools discovered")

        resources = await client.list_resources()
        resource_uris = {
            str(resource.uri) for resource in resources.resources
        }
        assert "dwh://explorer/capabilities" in resource_uris

        print("PASS: MCP Resources discovered")

        prompts = await client.list_prompts()
        prompt_names = {prompt.name for prompt in prompts.prompts}

        assert "investigate_dwh_table" in prompt_names

        print("PASS: MCP Prompts discovered")

        result = await client.call_tool(
            "investigate_dwh_object",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        assert not result.is_error

        if result.structured_content is not None:
            data = result.structured_content
        else:
            data = json.loads(result.content[0].text)

        assert data["object"] == "gold.fact_orders"
        assert data["investigation_status"] == "completed"
        assert data["overall_status"] == "WARNING"
        assert data["summary"]["column_count"] == 5

        print("PASS: Composite Tool executed over STDIO")
        print("PASS: Reconciliation result validated")
        print("STAGE 5.3.5.1 STDIO VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
