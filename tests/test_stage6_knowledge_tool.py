import asyncio
import json
from unittest.mock import patch

from mcp import Client
from server import mcp


async def main():
    full_name = "marketplace_lab.gold.fact_orders"

    expected = {
        "object_name": full_name,
        "platform": "azure_databricks",
        "metadata": {
            "full_name": full_name,
            "table_type": "MANAGED",
        },
        "table_lineage": {
            "status": "completed",
            "row_count": 1,
            "events": [],
        },
        "column_lineage": {
            "status": "completed",
            "row_count": 0,
            "events": [],
        },
        "status": "completed",
    }

    with patch(
        "server.investigate_databricks_object",
        return_value=expected,
    ) as mock_investigate:

        async with Client(mcp, raise_exceptions=True) as client:
            result = await client.call_tool(
                "databricks_investigate_object",
                {"full_name": full_name},
            )

        assert not result.is_error

        assert len(result.content) == 1

        actual = json.loads(result.content[0].text)

        assert actual == expected

        mock_investigate.assert_called_once()

    print("OBJECT:", actual["object_name"])
    print("STATUS:", actual["status"])
    print("MCP CONTENT ITEMS:", len(result.content))
    print("STAGE 6.6.6: PASSED")


if __name__ == "__main__":
    asyncio.run(main())