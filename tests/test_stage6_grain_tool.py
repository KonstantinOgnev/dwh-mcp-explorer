
import asyncio
import json
from unittest.mock import patch

from mcp import Client
from server import mcp


async def main():
    full_name = "marketplace_lab.gold.fact_orders"
    key_column = "order_id"

    expected = {
        "table_name": full_name,
        "key_column": key_column,
        "total_rows": 10000,
        "distinct_keys": 10000,
        "duplicate_rows": 0,
        "null_keys": 0,
        "status": "passed",
    }

    with patch(
        "server.DatabricksGrainProvider"
    ) as mock_provider_class:

        mock_provider = mock_provider_class.return_value
        mock_provider.validate_grain.return_value = expected

        async with Client(mcp, raise_exceptions=True) as client:
            result = await client.call_tool(
                "databricks_validate_grain",
                {
                    "full_name": full_name,
                    "key_column": key_column,
                },
            )

        assert not result.is_error
        assert len(result.content) == 1

        actual = json.loads(result.content[0].text)

        assert actual == expected

        mock_provider.validate_grain.assert_called_once_with(
            full_name=full_name,
            key_column=key_column,
        )

    print("TABLE:", actual["table_name"])
    print("KEY:", actual["key_column"])
    print("STATUS:", actual["status"])
    print("MCP CONTENT ITEMS:", len(result.content))
    print("STAGE 6.7.8: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
