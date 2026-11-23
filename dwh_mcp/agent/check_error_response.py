import asyncio
import json

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "databricks_describe_table",
            {
                "full_name": (
                    "marketplace_lab.gold."
                    "__agent_missing_table_test_20261117"
                )
            },
        )

        payload = result.structured_content

        if payload is None:
            for block in result.content:
                if block.type == "text":
                    payload = json.loads(block.text)
                    break

        print("MCP is_error:", result.is_error)
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        assert isinstance(payload, dict)
        assert payload["status"] == "failed"
        assert payload["error"]["category"] == "OBJECT_NOT_FOUND"
        assert payload["error"]["retryable"] is False

        print("Structured not-found response OK")


if __name__ == "__main__":
    asyncio.run(main())