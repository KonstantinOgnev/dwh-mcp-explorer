
import asyncio
import json

from mcp import Client
from server import mcp


EXPECTED_TOOLS = {
    "list_schemas",
    "list_tables",
    "describe_table",
    "get_primary_keys",
    "get_foreign_keys",
    "investigate_dwh_object",
    "list_sql_files",
    "read_sql_file",
    "get_table_knowledge",
    "get_table_lineage",
    "reconcile_table_mapping",
    "reconcile_column_constraints",
    "generate_reconciliation_report",
}


def extract_result(result):
    if result.is_error:
        raise RuntimeError(f"MCP error: {result.content}")

    if result.structured_content is not None:
        return result.structured_content

    for item in result.content:
        if item.type == "text":
            return json.loads(item.text)

    raise ValueError("No usable MCP result")


async def main():
    async with Client(mcp, raise_exceptions=True) as client:
        response = await client.list_tools()

        names = {tool.name for tool in response.tools}

        assert names == EXPECTED_TOOLS, (
            f"Missing: {EXPECTED_TOOLS - names}; "
            f"Unexpected: {names - EXPECTED_TOOLS}"
        )

        print("PASS: MCP tool registry")

        # Check tool input contracts
        by_name = {
            tool.name: tool
            for tool in response.tools
        }

        report_schema = by_name[
            "generate_reconciliation_report"
        ].input_schema

        properties = report_schema["properties"]

        assert set(properties) == {
            "schema",
            "table",
            "filename"
        }

        print("PASS: Report tool input contract")

        # Positive integration check
        result = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        data = extract_result(result)

        assert data["overall_status"] == "WARNING"
        assert data["summary"]["column_count"] == 5
        assert data["summary"]["status_counts"]["PASS"] == 4
        assert data["summary"]["status_counts"]["WARNING"] == 1

        print("PASS: Positive reporting contract")

        # Negative integration check
        result = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders_negative.sql"
            }
        )

        data = extract_result(result)

        assert data["overall_status"] == "FAIL"
        assert "amount" in data["reconciliation"]["missing_in_sql"]
        assert (
            "order_total"
            in data["reconciliation"]["missing_in_database"]
        )

        print("PASS: Negative reporting contract")

        print("STAGE 5 REFACTORING VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
