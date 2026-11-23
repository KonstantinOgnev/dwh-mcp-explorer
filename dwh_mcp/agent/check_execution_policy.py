import unittest

from dwh_mcp.agent.execution_policy import (
    ExecutionPolicy,
    ExecutionPolicyError,
)


TABLE = "marketplace_lab.gold.fact_orders"
DESCRIBE = "databricks_describe_table"
LINEAGE = "databricks_get_table_lineage"
ALLOWED = {DESCRIBE, LINEAGE}


class ExecutionPolicyTests(unittest.TestCase):
    def make_policy(self, limit=8):
        return ExecutionPolicy(TABLE, ALLOWED, limit)

    def record_error(self, policy, category, retryable):
        policy.after_call(
            DESCRIBE,
            {"full_name": TABLE},
            is_error=True,
            payload={
                "status": "failed",
                "error": {
                    "category": category,
                    "retryable": retryable,
                },
            },
        )

    def test_allowed_call(self):
        policy = self.make_policy()
        policy.before_call(DESCRIBE, {"full_name": TABLE})
        self.assertEqual(policy.tool_calls, 1)

    def test_other_table_blocked(self):
        policy = self.make_policy()
        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(
                DESCRIBE,
                {"full_name": "marketplace_lab.gold.fact_payments"},
            )
        self.assertEqual(policy.tool_calls, 0)

    def test_unknown_tool_blocked(self):
        policy = self.make_policy()
        with self.assertRaises(ExecutionPolicyError):
            policy.before_call("execute_sql", {"full_name": TABLE})
        self.assertEqual(policy.tool_calls, 0)

    def test_extra_arguments_blocked(self):
        policy = self.make_policy()
        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(
                DESCRIBE,
                {"full_name": TABLE, "sql": "SELECT 1"},
            )
        self.assertEqual(policy.tool_calls, 0)

    def test_successful_repeat_blocked(self):
        policy = self.make_policy()
        arguments = {"full_name": TABLE}
        policy.before_call(DESCRIBE, arguments)
        policy.after_call(
            DESCRIBE,
            arguments,
            is_error=False,
            payload={"full_name": TABLE},
        )
        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(DESCRIBE, arguments)
        self.assertEqual(policy.tool_calls, 1)

    def test_transient_error_allows_only_one_retry(self):
        policy = self.make_policy()
        arguments = {"full_name": TABLE}
        policy.before_call(DESCRIBE, arguments)
        self.record_error(policy, "SOURCE_UNAVAILABLE", True)

        policy.before_call(DESCRIBE, arguments)
        self.record_error(policy, "SOURCE_UNAVAILABLE", True)

        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(DESCRIBE, arguments)
        self.assertEqual(policy.tool_calls, 2)

    def test_non_transient_errors_block_retry(self):
        for category in (
            "ACCESS_DENIED",
            "AUTHENTICATION_FAILED",
            "INTERNAL_ERROR",
        ):
            with self.subTest(category=category):
                policy = self.make_policy()
                arguments = {"full_name": TABLE}
                policy.before_call(DESCRIBE, arguments)
                self.record_error(policy, category, False)

                with self.assertRaises(ExecutionPolicyError):
                    policy.before_call(DESCRIBE, arguments)
                self.assertEqual(policy.tool_calls, 1)

    def test_not_found_blocks_further_tools(self):
        policy = self.make_policy()
        policy.before_call(DESCRIBE, {"full_name": TABLE})
        self.record_error(policy, "OBJECT_NOT_FOUND", False)

        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(LINEAGE, {"full_name": TABLE})
        self.assertEqual(policy.tool_calls, 1)

    def test_total_limit_includes_retry(self):
        policy = self.make_policy(limit=2)
        arguments = {"full_name": TABLE}
        policy.before_call(DESCRIBE, arguments)
        self.record_error(policy, "RATE_LIMITED", True)
        policy.before_call(DESCRIBE, arguments)

        with self.assertRaises(ExecutionPolicyError):
            policy.before_call(LINEAGE, arguments)
        self.assertEqual(policy.tool_calls, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)