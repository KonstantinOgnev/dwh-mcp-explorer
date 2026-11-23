import json


class ExecutionPolicyError(RuntimeError):
    """A tool call was blocked by execution rules."""


class ExecutionPolicy:
    def __init__(
        self,
        target_table: str,
        allowed_tools: set[str],
        max_tool_calls: int = 8,
    ):
        if not target_table or len(target_table.split(".")) != 3:
            raise ValueError("Expected table name: catalog.schema.table")

        if max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")

        self.target_table = target_table
        self.allowed_tools = frozenset(allowed_tools)
        self.max_tool_calls = max_tool_calls
        self.tool_calls = 0

        self._attempts = {}
        self._retryable = {}
        self._stopped = False

    @staticmethod
    def _call_key(tool: str, arguments: dict) -> str:
        return json.dumps(
            [tool, arguments],
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def before_call(self, tool: str, arguments: dict) -> None:
        """Validate and reserve one actual tool-call attempt."""
        if self._stopped:
            raise ExecutionPolicyError(
                "Investigation stopped: target table was not found"
            )

        if tool not in self.allowed_tools:
            raise ExecutionPolicyError("Tool is not allowed")

        if not isinstance(arguments, dict):
            raise ExecutionPolicyError("Tool arguments must be an object")

        if arguments.get("full_name") != self.target_table:
            raise ExecutionPolicyError(
                "Only the explicitly requested table is allowed"
            )

        expected_arguments = {"full_name"}
        if tool == "databricks_validate_grain":
            expected_arguments.add("key_column")
            key_column = arguments.get("key_column")
            if not isinstance(key_column, str) or not key_column.strip():
                raise ExecutionPolicyError("key_column must be non-empty")

        if set(arguments) != expected_arguments:
            raise ExecutionPolicyError("Unexpected or missing arguments")

        if self.tool_calls >= self.max_tool_calls:
            raise ExecutionPolicyError("Tool-call limit reached")

        key = self._call_key(tool, arguments)
        attempts = self._attempts.get(key, 0)

        if attempts:
            if attempts >= 2 or not self._retryable.get(key, False):
                raise ExecutionPolicyError(
                    "Repeated call is not allowed"
                )

        self.tool_calls += 1
        self._attempts[key] = attempts + 1

        # A retry requires explicit permission from the latest result.
        self._retryable[key] = False

    def after_call(
        self,
        tool: str,
        arguments: dict,
        *,
        is_error: bool,
        payload,
    ) -> None:
        """Record the outcome without treating unknown errors as transient."""
        key = self._call_key(tool, arguments)

        error = (
            payload.get("error")
            if isinstance(payload, dict)
            else None
        )

        category = (
            error.get("category")
            if isinstance(error, dict)
            else None
        )

        self._retryable[key] = (
            is_error
            and isinstance(error, dict)
            and error.get("retryable") is True
            and category in {"SOURCE_UNAVAILABLE", "RATE_LIMITED"}
        )

        if (
            tool == "databricks_describe_table"
            and is_error
            and category == "OBJECT_NOT_FOUND"
        ):
            self._stopped = True