
import asyncio
import json

from mcp import Client
from server import mcp



def extract_data(result):
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {result}")

    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and structured:
        return structured.get("result", structured)

    data = getattr(result, "data", None)
    if isinstance(data, dict) and data:
        return data.get("result", data)

    content = result.content or []
    for item in content:
        text = getattr(item, "text", None)
        if text:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed.get("result", parsed)
            return parsed

    raise RuntimeError(
        "MCP returned no extractable payload. "
        f"is_error={result.is_error}; "
        f"structured_type={type(structured).__name__}; "
        f"data_type={type(data).__name__}; "
        f"content_count={len(content)}"
    )

async def main():
    table_name = "marketplace_lab.gold.fact_orders"

    async with Client(mcp, raise_exceptions=True) as client:
        for tool_name, source in [
            (
                "databricks_get_table_lineage",
                "system.access.table_lineage",
            ),
            (
                "databricks_get_column_lineage",
                "system.access.column_lineage",
            ),
        ]:
            result = await client.call_tool(
                tool_name,
                {"full_name": table_name},
            )

            print("RAW MCP RESULT:")
            print(result.model_dump(exclude_none=False))

            print(f"\nDEBUG TOOL: {tool_name}")
            print("Result type:", type(result).__name__)
            print("Is error:", result.is_error)
            print("Content items:", len(result.content or []))

            structured = getattr(result, "structured_content", None)
            print("Structured content type:", type(structured).__name__)

            data_field = getattr(result, "data", None)
            print("Data field type:", type(data_field).__name__)

            if isinstance(structured, dict):
                print("Structured keys:", list(structured.keys())[:15])

            if isinstance(data_field, dict):
                print("Data keys:", list(data_field.keys())[:15])

            data = extract_data(result)

            assert data["status"] == "completed", data
            assert data["source"] == source, data
            assert data["table_name"] == table_name, data
            assert isinstance(data["events"], list), data

            print(
                f"PASS: {tool_name} executed; "
                f"events={len(data['events'])}"
            )

    print("STAGE 6.5.8 MCP LINEAGE VALIDATION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
