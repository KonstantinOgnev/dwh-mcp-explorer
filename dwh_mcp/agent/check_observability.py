import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from dwh_mcp.agent import runner
from dwh_mcp.agent.config import AgentConfig
from dwh_mcp.agent.run_logging import RunLogger
from dwh_mcp.agent.check_runner import (
    TABLE,
    FakeObject,
    tool_call,
    response,
    tool_result,
    failed_result,
)


class ObservabilityTests(unittest.IsolatedAsyncioTestCase):
    async def run_scenario(self, responses, results, *, blocked=False):
        config = AgentConfig(api_key="local-test", model="local-test")
        clock = [0.0]
        response_iterator = iter(responses)
        result_iterator = iter(results)

        async def create_response(**kwargs):
            clock[0] += 0.25
            return next(response_iterator)

        async def execute_tool(*args, **kwargs):
            clock[0] += 0.1
            return next(result_iterator)

        model = MagicMock()
        model.messages.create = AsyncMock(side_effect=create_response)

        client = MagicMock()
        client.call_tool = AsyncMock(side_effect=execute_tool)

        model_context = MagicMock()
        model_context.__aenter__ = AsyncMock(return_value=model)
        model_context.__aexit__ = AsyncMock(return_value=False)

        client_context = MagicMock()
        client_context.__aenter__ = AsyncMock(return_value=client)
        client_context.__aexit__ = AsyncMock(return_value=False)

        with tempfile.TemporaryDirectory() as directory:
            log = RunLogger(
                "Local observability test",
                config,
                output_root=directory,
            )

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
                patch.object(
                    runner, "perf_counter", side_effect=lambda: clock[0]
                ),
            ):
                if blocked:
                    with self.assertRaises(RuntimeError):
                        await runner.run_agent(
                            "Local test", target_table=TABLE
                        )
                else:
                    await runner.run_agent(
                        "Local test", target_table=TABLE
                    )

            summary = json.loads(
                (log.directory / "run.json").read_text(encoding="utf-8")
            )
            events = [
                json.loads(line)
                for line in (
                    log.directory / "events.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]

            self.assertTrue(all(
                event["run_id"] == summary["run_id"]
                for event in events
            ))
            self.assertGreaterEqual(summary["duration_ms"], 0)
            self.assertIn("finished_at", summary)

            for event in events:
                if event["type"] == "model_response":
                    self.assertEqual(event["duration_ms"], 250.0)
                elif event["type"] == "tool_result":
                    self.assertEqual(event["duration_ms"], 100.0)

            report_exists = (log.directory / "report.md").exists()

        return summary, events, client, report_exists

    async def test_success_metrics(self):
        summary, events, client, report_exists = await self.run_scenario(
            [
                response(tool_call()),
                response(
                    FakeObject(type="text", text="Test report"),
                    stop="end_turn",
                ),
            ],
            [tool_result({"full_name": TABLE})],
        )

        self.assertEqual(summary["status"], "completed")
        self.assertTrue(report_exists)
        self.assertEqual(summary["metrics"], {
            "model_calls": 2,
            "tool_calls": 1,
            "tool_errors": 0,
            "tool_retries": 0,
            "blocked_calls": 0,
            "input_tokens": 20,
            "output_tokens": 10,
        })

        started = next(
            e for e in events if e["type"] == "tool_started"
        )
        finished = next(
            e for e in events if e["type"] == "tool_result"
        )
        self.assertEqual(started["tool_use_id"], finished["tool_use_id"])
        self.assertEqual(finished["status"], "completed")
        self.assertIsNone(finished["error_code"])
        client.call_tool.assert_awaited_once()

    async def test_retry_and_error_metrics(self):
        summary, events, client, _ = await self.run_scenario(
            [
                response(tool_call()),
                response(tool_call(call_id="call_2")),
                response(
                    FakeObject(type="text", text="Test report"),
                    stop="end_turn",
                ),
            ],
            [
                failed_result("SOURCE_UNAVAILABLE", retryable=True),
                tool_result({"full_name": TABLE}),
            ],
        )

        self.assertEqual(summary["metrics"]["tool_calls"], 2)
        self.assertEqual(summary["metrics"]["tool_errors"], 1)
        self.assertEqual(summary["metrics"]["tool_retries"], 1)
        self.assertEqual(summary["metrics"]["model_calls"], 3)
        self.assertEqual(summary["metrics"]["input_tokens"], 30)
        self.assertEqual(summary["metrics"]["output_tokens"], 15)

        results = [e for e in events if e["type"] == "tool_result"]
        self.assertEqual(results[0]["error_code"], "SOURCE_UNAVAILABLE")
        self.assertEqual(results[0]["status"], "failed")
        self.assertEqual(results[1]["status"], "completed")
        self.assertEqual(results[1]["attempt"], 2)
        self.assertEqual(client.call_tool.await_count, 2)

    async def test_blocked_call_metrics(self):
        summary, events, client, report_exists = await self.run_scenario(
            [response(tool_call(table="other.gold.table"))],
            [],
            blocked=True,
        )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["metrics"]["blocked_calls"], 1)
        self.assertEqual(summary["metrics"]["tool_calls"], 0)
        self.assertEqual(summary["metrics"]["tool_errors"], 0)
        self.assertFalse(report_exists)
        self.assertTrue(any(
            e["type"] == "tool_call_blocked" for e in events
        ))
        client.call_tool.assert_not_awaited()


if __name__ == "__main__":
    unittest.main(verbosity=2)