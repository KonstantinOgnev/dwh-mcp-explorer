import json
import tempfile
import unittest

from dwh_mcp.agent.config import AgentConfig
from dwh_mcp.agent.run_logging import RunLogger
from dwh_mcp.agent.run_statistics import (
    latency_summary,
    estimate_cost,
)


class RunStatisticsTests(unittest.TestCase):
    def test_percentiles(self):
        result = latency_summary([100, 20, 40, 10, 30])
        self.assertEqual(result, {
            "count": 5,
            "p50_ms": 30,
            "p95_ms": 100,
            "max_ms": 100,
        })

    def test_empty_and_single_sample(self):
        self.assertEqual(latency_summary([]), {
            "count": 0,
            "p50_ms": None,
            "p95_ms": None,
            "max_ms": None,
        })
        self.assertEqual(latency_summary([42]), {
            "count": 1,
            "p50_ms": 42,
            "p95_ms": 42,
            "max_ms": 42,
        })

    def test_invalid_durations(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    latency_summary([value])

    def test_cost_and_missing_prices(self):
        self.assertEqual(
            estimate_cost(1_000_000, 1_000_000, 2, 10),
            12.0,
        )
        self.assertEqual(estimate_cost(0, 0, 2, 10), 0.0)
        self.assertIsNone(estimate_cost(100, 50, None, 10))
        self.assertIsNone(estimate_cost(100, 50, 2, None))

    def test_invalid_prices(self):
        for rate in (-1, float("nan"), float("inf")):
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    estimate_cost(100, 50, rate, 10)

    def test_statistics_saved_to_run_json(self):
        config = AgentConfig(
            api_key="local-test-key",
            model="local-test",
            input_usd_per_million=2,
            output_usd_per_million=10,
        )

        with tempfile.TemporaryDirectory() as directory:
            log = RunLogger(
                "Statistics test", config, output_root=directory
            )

            for index, duration in enumerate([10, 20, 30, 40, 100], 1):
                log.event(
                    "model_response",
                    duration_ms=duration,
                    total_input_tokens=index * 200_000,
                    total_output_tokens=index * 200_000,
                )

            log.event(
                "tool_started",
                tool="describe",
                is_retry=False,
            )
            log.event(
                "tool_result",
                tool="describe",
                duration_ms=50,
                is_error=False,
            )
            log.event(
                "tool_started",
                tool="lineage",
                is_retry=False,
            )
            log.event(
                "tool_result",
                tool="lineage",
                duration_ms=90,
                is_error=True,
            )
            log.finish("completed")

            data = json.loads(
                (log.directory / "run.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(data["latency"]["method"], "nearest_rank")
        self.assertEqual(data["latency"]["model"]["count"], 5)
        self.assertEqual(data["latency"]["model"]["p50_ms"], 30)
        self.assertEqual(data["latency"]["model"]["p95_ms"], 100)
        self.assertEqual(
            data["latency"]["tools"]["describe"]["p95_ms"], 50
        )
        self.assertEqual(
            data["latency"]["tools"]["lineage"]["p95_ms"], 90
        )
        self.assertEqual(data["metrics"]["tool_errors"], 1)
        self.assertEqual(data["cost"]["estimated_usd"], 12.0)
        self.assertEqual(data["cost"]["input_usd_per_million"], 2)
        self.assertEqual(data["cost"]["output_usd_per_million"], 10)

    def test_unconfigured_cost_saved_as_null(self):
        config = AgentConfig(api_key="local-test-key", model="local-test")

        with tempfile.TemporaryDirectory() as directory:
            log = RunLogger(
                "No prices", config, output_root=directory
            )
            log.finish("failed")
            data = json.loads(
                (log.directory / "run.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertIsNone(data["cost"]["estimated_usd"])
        self.assertEqual(data["latency"]["model"]["count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)