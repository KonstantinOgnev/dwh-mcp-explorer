
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwh_mcp.databricks_grain_provider import (
    DatabricksGrainProvider,
)


def make_provider():
    patcher = patch(
        "dwh_mcp.databricks_grain_provider.WorkspaceClient"
    )
    client_class = patcher.start()
    client = Mock()
    client_class.return_value = client

    provider = DatabricksGrainProvider()
    return provider, client, patcher


def main():
    provider, client, patcher = make_provider()

    try:
        # Case 1: unsafe table identifier
        try:
            provider.validate_grain(
                "marketplace_lab.gold.fact_orders;DROP",
                "order_id",
            )
            raise AssertionError("Unsafe identifier accepted")
        except ValueError:
            print("PASS: Invalid table identifier rejected")

        client.statement_execution.execute_statement.assert_not_called()

        # Case 2: failed SQL execution
        client.statement_execution.execute_statement.return_value = (
            SimpleNamespace(
                status=SimpleNamespace(
                    state=SimpleNamespace(value="FAILED")
                ),
                result=None,
            )
        )

        try:
            provider.validate_grain(
                "marketplace_lab.gold.fact_orders",
                "order_id",
            )
            raise AssertionError("Failed SQL was accepted")
        except RuntimeError:
            print("PASS: Failed SQL execution detected")

        # Case 3: empty SQL result
        client.statement_execution.execute_statement.return_value = (
            SimpleNamespace(
                status=SimpleNamespace(
                    state=SimpleNamespace(value="SUCCEEDED")
                ),
                result=SimpleNamespace(data_array=[]),
            )
        )

        try:
            provider.validate_grain(
                "marketplace_lab.gold.fact_orders",
                "order_id",
            )
            raise AssertionError("Empty SQL result accepted")
        except RuntimeError:
            print("PASS: Empty SQL result detected")

    finally:
        patcher.stop()

    print("STAGE 6.8.3: PASSED")


if __name__ == "__main__":
    main()
