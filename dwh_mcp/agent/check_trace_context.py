import unittest
from unittest.mock import MagicMock, patch

from mcp import Client
from server import mcp
import json


class TraceContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_metadata_trace_through_mcp(self):
        table = "marketplace_lab.gold.fact_orders"
        provider = MagicMock()
        provider.describe_table.return_value = {
            "full_name": table,
            "columns": [],
            "properties": {},
        }

        with patch("server._databricks_provider", return_value=provider):
            async with Client(mcp, raise_exceptions=True) as client:
                tools = await client.list_tools()
                tool = next(
                    item for item in tools.tools
                    if item.name == "databricks_describe_table"
                )
                self.assertEqual(
                    set(tool.input_schema["properties"]), {"full_name"}
                )

                result = await client.call_tool(
                    "databricks_describe_table",
                    {"full_name": table},
                    meta={
                        "dwh_trace": {
                            "run_id": "local-run-123",
                            "tool_use_id": "local-call-456",
                        },
                    },
                )

        print(
            json.dumps(
                result.model_dump(mode="json", exclude_none=True),
                ensure_ascii=False,
                indent=2,
            )
        )

        self.assertFalse(
            result.is_error,
            "MCP returned a tool error; see the response above",
        )

        payload = result.structured_content
        if payload is None:
            for item in result.content:
                if item.type == "text":
                    try:
                        candidate = json.loads(item.text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(candidate, dict):
                        payload = candidate
                        break

        self.assertIsInstance(payload, dict)
        trace = payload["_trace"]
        self.assertEqual(trace["run_id"], "local-run-123")
        self.assertEqual(trace["tool_use_id"], "local-call-456")
        self.assertEqual(trace["operation"], "databricks.tables.get")
        self.assertEqual(trace["status"], "completed")
        self.assertIsNone(trace["error_code"])
        self.assertGreaterEqual(trace["duration_ms"], 0)
        self.assertTrue(trace["mcp_request_id"])
        provider.describe_table.assert_called_once_with(table)


if __name__ == "__main__":
    unittest.main(verbosity=2)