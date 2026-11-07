import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    ExecuteStatementRequestOnWaitTimeout,
)

from dwh_mcp.databricks_reconciliation import (
    build_grain_validation_sql,
    reconcile_grain,
)


class DatabricksGrainProvider:
    def __init__(
        self,
        profile: str = "MARKETPLACE_LAB",
        warehouse_id: str | None = None,
    ):
        self.client = WorkspaceClient(profile=profile)

        self.warehouse_id = (
            warehouse_id or os.getenv("DATABRICKS_WAREHOUSE_ID")
        )

        if not self.warehouse_id:
            raise ValueError(
                "DATABRICKS_WAREHOUSE_ID is not configured"
            )

    def validate_grain(
        self,
        full_name: str,
        key_column: str,
    ) -> dict:
        sql = build_grain_validation_sql(full_name, key_column)

        response = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=sql,
            wait_timeout="30s",
            on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CANCEL,
            row_limit=1,
        )

        state = response.status.state.value

        if state != "SUCCEEDED":
            raise RuntimeError(
                f"Grain validation query failed: {state}"
            )

        if not response.result or not response.result.data_array:
            raise RuntimeError(
                "Grain validation returned no data"
            )

        values = response.result.data_array[0]

        if len(values) != 3:
            raise RuntimeError(
                "Unexpected grain validation result"
            )

        total_rows = int(values[0])
        distinct_keys = int(values[1])
        null_keys = int(values[2])

        return reconcile_grain(
            full_name=full_name,
            key_column=key_column,
            total_rows=total_rows,
            distinct_keys=distinct_keys,
            null_keys=null_keys,
        )