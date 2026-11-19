import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from dwh_mcp.agent import runner
from dwh_mcp.agent.config import AgentConfig


TABLE = "marketplace_lab.gold.fact_orders"
DESCRIBE = "databricks_describe_table"
LINEAGE = "databricks_get_table_lineage"


class FakeObject(SimpleNamespace):
    def model_dump(self, **kwargs):
        def convert(value):
            if isinstance(value, SimpleNamespace):
                return {
                    key: convert(item)
                    for key, item in vars(value).items()
                }
            if isinstance(value, dict):
                return {
                    key: convert(item)
                    for key, item in value.items()
                }
            if isinstance(value, (list, tuple)):
                return [convert(item) for item in value]
            return value

        return convert(self)


def tool_call(name=DESCRIBE, table=TABLE, call_id="call_1"):
    return FakeObject(
        type="tool_use",
        id=call_id,
        name=name,
        input={"full_name": table},
    )


def response(*blocks, stop="tool_use"):
    return FakeObject(
        content=list(blocks),
        stop_reason=stop,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def tool_result(payload):
    return FakeObject(
        structured_content=payload,
        content=[],
        is_error=False,
    )


def failed_result(category, retryable=False):
    return tool_result({
        "status": "failed",
        "error": {
            "category": category,
            "retryable": retryable,
        },
    })

class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def run_scenario(
        self,
        responses,
        results=(),
        *,
        limit=8,
        max_steps=10,
        expected_failure=False,
    ):
        config = AgentConfig(
            api_key="local-test",
            model="local-test",
            max_steps=max_steps,
            max_tool_calls=limit,
        )

        model = MagicMock()
        model.messages.create = AsyncMock(side_effect=responses)

        client = MagicMock()
        client.call_tool = AsyncMock(side_effect=results)

        model_context = MagicMock()
        model_context.__aenter__ = AsyncMock(return_value=model)
        model_context.__aexit__ = AsyncMock(return_value=False)

        client_context = MagicMock()
        client_context.__aenter__ = AsyncMock(return_value=client)
        client_context.__aexit__ = AsyncMock(return_value=False)

        with tempfile.TemporaryDirectory() as directory:
            log = MagicMock()
            log.directory = Path(directory)

            with (
                patch.object(
                    runner, "load_agent_config", return_value=config
                ),
                patch.object(runner, "RunLogger", return_value=log),
                patch.object(
                    runner, "AsyncAnthropic",
                    return_value=model_context,
                ),
                patch.object(
                    runner, "Client", return_value=client_context
                ),
                patch.object(
                    runner, "get_agent_tools",
                    new=AsyncMock(return_value=[]),
                ),
            ):
                if expected_failure:
                    with self.assertRaises(RuntimeError):
                        await runner.run_agent(
                            "Local test", target_table=TABLE
                        )
                    log.save_report.assert_not_called()
                    self.assertEqual(
                        log.finish.call_args.args[0], "failed"
                    )
                else:
                    report = await runner.run_agent(
                        "Local test", target_table=TABLE
                    )
                    self.assertEqual(report, "Test report")
                    log.save_report.assert_called_once_with(report)
                    log.finish.assert_called_once_with("completed")

            partial_exists = (
                log.directory / "partial_report.md"
            ).exists()

        return client, model, log, partial_exists

    async def test_success(self):
        client, _, _, _ = await self.run_scenario(
            [
                response(tool_call()),
                response(
                    FakeObject(type="text", text="Test report"),
                    stop="end_turn",
                ),
            ],
            [tool_result({"full_name": TABLE})],
        )
        client.call_tool.assert_awaited_once_with(
            DESCRIBE, {"full_name": TABLE}
        )

    async def test_other_table_never_reaches_mcp(self):
        client, _, log, _ = await self.run_scenario(
            [response(tool_call(table="other.gold.table"))],
            expected_failure=True,
        )
        client.call_tool.assert_not_awaited()
        self.assertTrue(any(
            call.args[0] == "tool_call_blocked"
            for call in log.event.call_args_list
        ))

    async def test_successful_repeat_never_reaches_mcp(self):
        client, _, _, _ = await self.run_scenario(
            [
                response(tool_call()),
                response(tool_call(call_id="call_2")),
            ],
            [tool_result({"full_name": TABLE})],
            expected_failure=True,
        )
        self.assertEqual(client.call_tool.await_count, 1)

    async def test_not_found_blocks_lineage_in_same_response(self):
        client, _, _, _ = await self.run_scenario(
            [
                response(
                    tool_call(),
                    tool_call(LINEAGE, call_id="call_2"),
                ),
            ],
            [failed_result("OBJECT_NOT_FOUND")],
            expected_failure=True,
        )
        self.assertEqual(client.call_tool.await_count, 1)

    async def test_budget_blocks_next_call(self):
        client, _, _, _ = await self.run_scenario(
            [
                response(
                    tool_call(),
                    tool_call(LINEAGE, call_id="call_2"),
                ),
            ],
            [tool_result({"full_name": TABLE})],
            limit=1,
            expected_failure=True,
        )
        self.assertEqual(client.call_tool.await_count, 1)

    async def test_last_model_step_executes_no_tools(self):
        client, _, _, _ = await self.run_scenario(
            [response(tool_call())],
            max_steps=1,
            expected_failure=True,
        )
        client.call_tool.assert_not_awaited()

    async def test_truncated_report_is_not_completed(self):
        client, _, _, partial_exists = await self.run_scenario(
            [
                response(
                    FakeObject(type="text", text="Partial report"),
                    stop="max_tokens",
                ),
            ],
            expected_failure=True,
        )
        client.call_tool.assert_not_awaited()
        self.assertTrue(partial_exists)


if __name__ == "__main__":
    unittest.main(verbosity=2)