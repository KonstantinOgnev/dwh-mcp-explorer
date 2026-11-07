from __future__ import annotations

from typing import Any


def build_knowledge_object(
    full_name: str,
    metadata: dict[str, Any],
    table_lineage: dict[str, Any],
    column_lineage: dict[str, Any],
) -> dict[str, Any]:
    """
    Combine Databricks metadata and lineage into
    a unified DWH knowledge object.
    """

    return {
        "object_name": full_name,
        "platform": "azure_databricks",
        "metadata": metadata,
        "table_lineage": table_lineage,
        "column_lineage": column_lineage,
        "execution_context": {},
        "evidence": {
            "metadata_source": "unity_catalog",
            "table_lineage_source": "system.access.table_lineage",
            "column_lineage_source": "system.access.column_lineage",
        },
        "limitations": [
            "Lineage events may not represent complete dependencies.",
            "Lineage results are limited by query lookback and row count.",
        ],
        "status": "completed",
    }

def investigate_databricks_object(
    full_name: str,
    metadata_provider,
    lineage_provider,
) -> dict:
    """
    Collect metadata and lineage for a Databricks object.
    """

    metadata = metadata_provider.describe_table(full_name)

    table_lineage = lineage_provider.get_table_lineage(
        full_name
    )

    column_lineage = lineage_provider.get_column_lineage(
        full_name
    )

    return build_knowledge_object(
        full_name=full_name,
        metadata=metadata,
        table_lineage=table_lineage,
        column_lineage=column_lineage,
    )