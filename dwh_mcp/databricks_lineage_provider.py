
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    StatementParameterListItem,
    ExecuteStatementRequestOnWaitTimeout,
)


class DatabricksLineageProvider:
    """Read-only access to Databricks system lineage tables."""

    def __init__(
        self,
        profile: str = "MARKETPLACE_LAB",
        warehouse_id: str = "25ad047cd183f06d",
    ):
        self.client = WorkspaceClient(profile=profile)
        self.warehouse_id = warehouse_id

    def _execute_query(
        self,
        statement: str,
        table_name: str,
        source: str = "system.access.table_lineage",
    ) -> dict:
        response = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=statement,
            parameters=[
                StatementParameterListItem(
                    name="table_name",
                    value=table_name,
                    type="STRING",
                )
            ],
            wait_timeout="30s",
            on_wait_timeout=(
                ExecuteStatementRequestOnWaitTimeout.CANCEL
            ),
            row_limit=50,
        )

        state = (
            response.status.state.value
            if response.status and response.status.state
            else "UNKNOWN"
        )

        if state != "SUCCEEDED":
            error = (
                response.status.error.message
                if response.status and response.status.error
                else "No error details"
            )
            raise RuntimeError(
                f"Lineage query failed: {state}: {error}"
            )

        if not response.manifest or not response.result:
            raise RuntimeError("Missing query result metadata")

        columns = [
            column.name
            for column in response.manifest.schema.columns
        ]

        rows = [
            dict(zip(columns, values))
            for values in (response.result.data_array or [])
        ]

        return {
            "status": "completed",
            "source": source,
            "table_name": table_name,
            "row_count": len(rows),
            "truncated": bool(response.manifest.truncated),
            "events": rows,
        }

    def get_table_lineage(
        self,
        full_name: str,
    ) -> dict:
        sql = """
        SELECT
            event_time,
            source_table_full_name,
            target_table_full_name,
            entity_type,
            entity_id,
            created_by
        FROM system.access.table_lineage
        WHERE event_date >= date_sub(current_date(), 45)
          AND (
            source_table_full_name = :table_name
            OR target_table_full_name = :table_name
          )
        ORDER BY event_time DESC
        LIMIT 50
        """

        return self._execute_query(
            statement=sql,
            table_name=full_name,
            source="system.access.table_lineage",
        )

    def get_column_lineage(
        self,
        full_name: str,
    ) -> dict:
        """Read registered column-level lineage events."""

        sql = """
        SELECT
            event_time,
            source_table_full_name,
            source_column_name,
            target_table_full_name,
            target_column_name,
            entity_type,
            entity_id
        FROM system.access.column_lineage
        WHERE event_date >= date_sub(current_date(), 45)
        AND (
            source_table_full_name = :table_name
            OR target_table_full_name = :table_name
        )
        ORDER BY event_time DESC
        LIMIT 50
        """

        return self._execute_query(
            statement=sql,
            table_name=full_name,
            source="system.access.column_lineage",
        )
