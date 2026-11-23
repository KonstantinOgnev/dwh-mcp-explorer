import json
import tempfile
import unittest

from dwh_mcp.agent.config import AgentConfig
from dwh_mcp.agent.redaction import MASK, Redactor
from dwh_mcp.agent.run_logging import RunLogger


class RedactionTests(unittest.TestCase):
    def test_nested_sensitive_fields(self):
        source = {
            "password": "private-password",
            "nested": [{"access_token": "private-token"}],
            "input_tokens": 123,
            "category": "ACCESS_DENIED",
        }

        cleaned = Redactor().clean(source)

        self.assertEqual(cleaned["password"], MASK)
        self.assertEqual(cleaned["nested"][0]["access_token"], MASK)
        self.assertEqual(cleaned["input_tokens"], 123)
        self.assertEqual(cleaned["category"], "ACCESS_DENIED")
        self.assertEqual(source["password"], "private-password")

    def test_json_inside_string(self):
        content = json.dumps({
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "client_secret": "nested-secret",
                    "row_count": 10000,
                }),
            }],
        })

        cleaned = Redactor().clean(content)
        outer = json.loads(cleaned)
        inner = json.loads(outer["content"][0]["text"])

        self.assertEqual(inner["client_secret"], MASK)
        self.assertEqual(inner["row_count"], 10000)
        self.assertNotIn("nested-secret", cleaned)

    def test_text_patterns_and_known_secret(self):
        redactor = Redactor(secrets=("configured-key-123",))
        cleaned = redactor.text(
            "Key configured-key-123; "
            "Bearer sample-token-456; user@example.com"
        )

        self.assertNotIn("configured-key-123", cleaned)
        self.assertNotIn("sample-token-456", cleaned)
        self.assertNotIn("user@example.com", cleaned)
        self.assertIn(MASK, cleaned)

    def test_real_log_files(self):
        secret = "configured-test-key-123"
        config = AgentConfig(api_key=secret, model="local-test")

        with tempfile.TemporaryDirectory() as directory:
            log = RunLogger(
                f"Investigate table; key={secret}",
                config,
                output_root=directory,
            )
            log.write_json("tools.json", {
                "password": "private-password",
                "columns": ["order_id"],
            })
            log.event(
                "model_response",
                response={"text": f"Key: {secret}"},
                total_input_tokens=123,
                total_output_tokens=45,
            )
            log.event(
                "diagnostic",
                content=json.dumps({
                    "access_token": "private-token",
                    "category": "ACCESS_DENIED",
                }),
            )
            log.save_report(f"Report for user@example.com; {secret}")
            log.finish("completed")

            for path in log.directory.iterdir():
                text = path.read_text(encoding="utf-8")
                for forbidden in (
                    secret,
                    "private-password",
                    "private-token",
                    "user@example.com",
                ):
                    self.assertNotIn(forbidden, text, path.name)

            summary = json.loads(
                (log.directory / "run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(summary["metrics"]["input_tokens"], 123)
            self.assertEqual(summary["metrics"]["output_tokens"], 45)
            self.assertEqual(summary["status"], "completed")

            tools = json.loads(
                (log.directory / "tools.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(tools["columns"], ["order_id"])

            events = [
                json.loads(line)
                for line in (
                    log.directory / "events.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            diagnostic = json.loads(events[1]["content"])
            self.assertEqual(diagnostic["category"], "ACCESS_DENIED")
            self.assertEqual(diagnostic["access_token"], MASK)


if __name__ == "__main__":
    unittest.main(verbosity=2)