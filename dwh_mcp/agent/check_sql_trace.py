import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mcp import Client
from server import mcp
from dwh_mcp.databricks_grain_provider import DatabricksGrainProvider
from dwh_mcp.databricks_lineage_provider import DatabricksLineageProvider


TABLE = "marketplace_lab.gold.fact_orders"


def payload_from(result):
    if result.is_error:
        raise AssertionError(f"MCP tool error: {result.content}")

    if result.structured_content is not None:
        return result.structured_content

    for item in result.content:
        if item.type == "text":
            try:
                payload = json.loads(item.text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

    raise AssertionError("No JSON payload in MCP response")


class SqlTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_sql_statement_ids(self):
        scenarios = (
            ("databricks_validate_grain", "SUCCEEDED"),
            ("databricks_validate_grain", "FAILED"),
            ("databricks_get_table_lineage", "SUCCEEDED"),
            ("databricks_get_table_lineage", "FAILED"),
            ("databricks_get_column_lineage", "SUCCEEDED"),
            ("databricks_get_column_lineage", "FAILED"),
        )

        for tool, state in scenarios:
            with self.subTest(tool=tool, state=state):
                is_grain = tool == "databricks_validate_grain"
                provider_class = (
                    DatabricksGrainProvider
                    if is_grain
                    else DatabricksLineageProvider
                )

                # Skip the constructor: no credentials or network clients.
                provider = object.__new__(provider_class)
                provider.warehouse_id = "fake-warehouse"
                provider.client = MagicMock()

                statement_id = f"statement-{tool}-{state}"
                fake_response = SimpleNamespace(
                    statement_id=statement_id,
                    status=SimpleNamespace(
                        state=SimpleNamespace(value=state),
                        error=SimpleNamespace(message="Simulated failure"),
                    ),
                    manifest=SimpleNamespace(
                        schema=SimpleNamespace(columns=[]),
                        truncated=False,
                    ),
                    result=SimpleNamespace(
                        data_array=[["10", "10", "0"]] if is_grain else [],
                    ),
                )
                execute = provider.client.statement_execution.execute_statement
                execute.return_value = fake_response

                patch_target = (
                    "server.DatabricksGrainProvider"
                    if is_grain
                    else "server._databricks_lineage_provider"
                )
                arguments = {"full_name": TABLE}
                if is_grain:
                    arguments["key_column"] = "order_id"

                with patch(patch_target, return_value=provider):
                    async with Client(
                        mcp, raise_exceptions=True
                    ) as client:
                        result = await client.call_tool(
                            tool,
                            arguments,
                            meta={
                                "dwh_trace": {
                                    "run_id": "sql-test-run",
                                    "tool_use_id": "sql-test-call",
                                },
                            },
                        )

                payload = payload_from(result)
                trace = payload["_trace"]

                self.assertEqual(trace["statement_id"], statement_id)
                self.assertEqual(trace["run_id"], "sql-test-run")
                self.assertEqual(trace["tool_use_id"], "sql-test-call")
                self.assertGreaterEqual(trace["duration_ms"], 0)
                execute.assert_called_once()

                if state == "FAILED":
                    self.assertEqual(payload["status"], "failed")
                    self.assertEqual(trace["status"], "failed")
                    self.assertEqual(
                        trace["error_code"],
                        payload["error"]["category"],
                    )
                else:
                    self.assertEqual(trace["status"], "completed")
                    self.assertIsNone(trace["error_code"])


if __name__ == "__main__":
    unittest.main(verbosity=2)