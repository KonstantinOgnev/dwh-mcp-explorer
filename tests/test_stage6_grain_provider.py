from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwh_mcp.databricks_grain_provider import (
    DatabricksGrainProvider,
)


def main():
    mock_response = SimpleNamespace(
        status=SimpleNamespace(
            state=SimpleNamespace(value="SUCCEEDED")
        ),
        result=SimpleNamespace(
            data_array=[["10000", "10000", "0"]]
        ),
    )

    with patch(
        "dwh_mcp.databricks_grain_provider.WorkspaceClient"
    ) as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.statement_execution.execute_statement.return_value = (
            mock_response
        )

        provider = DatabricksGrainProvider()

        result = provider.validate_grain(
            full_name="marketplace_lab.gold.fact_orders",
            key_column="order_id",
        )

        assert result["status"] == "passed"
        assert result["total_rows"] == 10000
        assert result["distinct_keys"] == 10000
        assert result["duplicate_rows"] == 0
        assert result["null_keys"] == 0

        mock_client.statement_execution.execute_statement.assert_called_once()

        sql = (
            mock_client.statement_execution
            .execute_statement.call_args.kwargs["statement"]
        )

        assert "COUNT(DISTINCT `order_id`)" in sql
        assert "`marketplace_lab`.`gold`.`fact_orders`" in sql

    print("GRAIN VALIDATION STATUS:", result["status"])
    print("TOTAL ROWS:", result["total_rows"])
    print("DUPLICATE ROWS:", result["duplicate_rows"])
    print("STAGE 6.7.5: PASSED")


if __name__ == "__main__":
    main()