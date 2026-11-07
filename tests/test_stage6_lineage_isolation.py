
import asyncio
from unittest.mock import patch
from types import SimpleNamespace

from mcp import Client
from server import mcp
from dwh_mcp.databricks_lineage_provider import (
    DatabricksLineageProvider,
)


async def main():
    provider = DatabricksLineageProvider()

    # Execute a real Databricks query once.
    full_result = provider.get_table_lineage(
        "marketplace_lab.gold.fact_orders"
    )

    print("PROVIDER RESULT TYPE:", type(full_result).__name__)
    print("PROVIDER RESULT IS NONE:", full_result is None)

    if full_result is None:
        raise RuntimeError(
            "DatabricksLineageProvider.get_table_lineage() "
            "returned None"
        )

    # Keep only one real lineage event.
    test_payload = {
        **full_result,
        "events": full_result["events"][:1],
        "row_count": min(1, len(full_result["events"])),
    }

    mock_provider = SimpleNamespace(
        get_table_lineage=lambda full_name: test_payload
    )

    with patch(
        "server._databricks_lineage_provider",
        return_value=mock_provider,
    ):
        async with Client(mcp, raise_exceptions=True) as client:
            result = await client.call_tool(
                "databricks_get_table_lineage",
                {
                    "full_name": (
                        "marketplace_lab.gold.fact_orders"
                    )
                },
            )

            print("Is error:", result.is_error)
            print("Content count:", len(result.content or []))
            print(
                "Structured content type:",
                type(result.structured_content).__name__,
            )

            print(
                "First content:",
                result.content[0].text[:1000]
                if result.content else "EMPTY",
            )


if __name__ == "__main__":
    asyncio.run(main())
