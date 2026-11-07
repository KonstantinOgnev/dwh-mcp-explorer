
import asyncio

from mcp import Client
from server import mcp


import json


def extract_tool_result(result):
    """Extract MCP tool result from structured or text content."""

    if result.structured_content is not None:
        return result.structured_content

    if result.is_error:
        raise RuntimeError(
            f"MCP tool returned an error: {result.content}"
        )

    for block in result.content:
        if block.type == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return block.text

    return None

async def main():

    async with Client(mcp, raise_exceptions=True) as client:

        # 1. Discover available tools
        tools = await client.list_tools()

        print("Available MCP Tools:")
        for tool in tools.tools:
            print(f" - {tool.name}")

        # 2. List DWH schemas
        schemas = await client.call_tool(
            "list_schemas",
            {}
        )
        print("\nSchemas:")
        print(schemas.structured_content)

        # 3. List tables in Gold schema
        tables = await client.call_tool(
            "list_tables",
            {"schema": "gold"}
        )

        print("\n=== TABLES DIAGNOSTICS ===")
        print("Is error:", tables.is_error)
        print(extract_tool_result(tables))
        print("Raw content:", tables.content)

        # 4. Describe Gold fact table
        columns = await client.call_tool(
            "describe_table",
            {
                "schema": "gold",
                "table": "fact_orders"
            }
        )
        print("\nColumns:")
        print(columns.structured_content)

        # 5. Discover primary keys
        primary_keys = await client.call_tool(
            "get_primary_keys",
            {
                "schema": "gold",
                "table": "fact_orders"
            }
        )
        print("\nPrimary Keys:")
        print(primary_keys.structured_content)

        # 6. Discover foreign keys
        foreign_keys = await client.call_tool(
            "get_foreign_keys",
            {
                "schema": "gold",
                "table": "fact_orders"
            }
        )
        print("\nForeign Keys:")
        print(foreign_keys.structured_content)


        sql_files = await client.call_tool(
            "list_sql_files",
            {}
        )

        print("\nSQL Source Files:")
        print(extract_tool_result(sql_files))


        # Read SQL transformation source
        sql_file = await client.call_tool(
            "read_sql_file",
            {"filename": "fact_orders.sql"}
        )

        print("\nSQL File Content:")
        print(extract_tool_result(sql_file))

        # Stage 4: Collect table knowledge
        knowledge = await client.call_tool(
            "get_table_knowledge",
            {
                "schema": "gold",
                "table": "fact_orders"
            }
        )

        print("\n=== TABLE KNOWLEDGE ===")
        print(extract_tool_result(knowledge))

        # Stage 4: Extract table-level lineage
        lineage = await client.call_tool(
            "get_table_lineage",
            {"filename": "fact_orders.sql"}
        )

        print("\n=== TABLE LINEAGE ===")
        print(extract_tool_result(lineage))

        # Stage 4: Reconcile SQL mapping with database
        reconciliation = await client.call_tool(
            "reconcile_table_mapping",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        print("\n=== METADATA RECONCILIATION ===")
        print(extract_tool_result(reconciliation))

        # Stage 4: Negative reconciliation test
        negative_test = await client.call_tool(
            "reconcile_table_mapping",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders_negative.sql"
            }
        )

        print("\n=== NEGATIVE RECONCILIATION TEST ===")
        print(extract_tool_result(negative_test))

        # Stage 4: Inspect source column metadata
        for schema, table in [
            ("staging", "orders"),
            ("gold", "dim_customer")
        ]:
            result = await client.call_tool(
                "describe_table",
                {"schema": schema, "table": table}
            )

            print(f"\n=== SOURCE METADATA: {schema}.{table} ===")
            print(extract_tool_result(result))

        # Stage 4: Type and nullability reconciliation
        constraints = await client.call_tool(
            "reconcile_column_constraints",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        print("\n=== COLUMN CONSTRAINT RECONCILIATION ===")
        print(extract_tool_result(constraints))

        # Stage 4.8: Generate structured report
        report = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        print("\n=== STRUCTURED RECONCILIATION REPORT ===")

        report_data = extract_tool_result(report)

        import json
        print(json.dumps(report_data, indent=2))

        # Stage 4.8: Negative structured report test
        negative_report = await client.call_tool(
            "generate_reconciliation_report",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders_negative.sql"
            }
        )

        negative_data = extract_tool_result(negative_report)

        print("\n=== NEGATIVE STRUCTURED REPORT ===")
        print("Overall status:", negative_data["overall_status"])
        print("Summary:", negative_data["summary"])
        print("Findings:", negative_data["findings"])

        assert negative_data["overall_status"] == "FAIL"
        assert negative_data["reconciliation"]["mapping_complete"] is False

if __name__ == "__main__":
    asyncio.run(main())
