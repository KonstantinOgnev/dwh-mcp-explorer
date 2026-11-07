
import asyncio
from unittest.mock import patch

from mcp import Client
from server import mcp


async def main():
    with patch("server.DatabricksGrainProvider") as provider_class:
        provider = provider_class.return_value

        provider.validate_grain.side_effect = RuntimeError(
            "Simulated Databricks SQL execution failure"
        )

        async with Client(mcp, raise_exceptions=False) as client:
            result = await client.call_tool(
                "databricks_validate_grain",
                {
                    "full_name": "marketplace_lab.gold.fact_orders",
                    "key_column": "order_id",
                },
            )

        assert result.is_error is True, (
            f"Expected MCP error, got: {result}"
        )

        provider.validate_grain.assert_called_once()

    print("MCP ERROR FLAG:", result.is_error)
    print("STAGE 6.8.4: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
