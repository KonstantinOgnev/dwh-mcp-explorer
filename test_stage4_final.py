
import asyncio

from test_client import extract_tool_result
from mcp import Client
from server import mcp


async def main():
    async with Client(mcp, raise_exceptions=True) as client:


        tools_response = await client.list_tools()

        tool_names = {
            tool.name
            for tool in tools_response.tools
        }

        print("Available MCP Tools:", sorted(tool_names))

        required_tools = {
            "list_schemas",
            "list_tables",
            "describe_table",
            "get_primary_keys",
            "get_foreign_keys",
            "list_sql_files",
            "read_sql_file",
            "get_table_knowledge",
            "get_table_lineage",
            "reconcile_table_mapping",
            "reconcile_column_constraints",
            "generate_reconciliation_report",
        }

        assert required_tools.issubset(tool_names), (
            f"Missing MCP Tools: {required_tools - tool_names}"
        )

        print(f"PASS: {len(required_tools)} MCP Tools available")

        # Test normal reconciliation report
        positive_result = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql",
            },
        )

        assert not positive_result.is_error
        positive = extract_tool_result(positive_result)

        assert positive is not None
        assert positive["overall_status"] == "WARNING"
        assert positive["summary"]["column_count"] == 5
        assert positive["summary"]["status_counts"]["PASS"] == 4
        assert positive["summary"]["status_counts"]["WARNING"] == 1
        assert positive["reconciliation"]["mapping_complete"]

        print("PASS: Positive reconciliation report")

        # Test intentionally incorrect SQL mapping
        negative_result = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders_negative.sql",
            },
        )

        assert not negative_result.is_error
        negative = extract_tool_result(negative_result)

        assert negative is not None
        assert negative["overall_status"] == "FAIL"
        assert not negative["reconciliation"]["mapping_complete"]

        assert "amount" in negative["reconciliation"]["missing_in_sql"]
        assert (
            "order_total"
            in negative["reconciliation"]["missing_in_database"]
        )

        print("PASS: Negative reconciliation report")
        print("STAGE 4 FINAL VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
