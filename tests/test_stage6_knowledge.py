from unittest.mock import Mock

from dwh_mcp.databricks_knowledge import (
    investigate_databricks_object,
)


def main():
    metadata_provider = Mock()
    lineage_provider = Mock()

    metadata_provider.describe_table.return_value = {
        "full_name": "marketplace_lab.gold.fact_orders",
        "table_type": "MANAGED",
        "data_source_format": "DELTA",
    }

    lineage_provider.get_table_lineage.return_value = {
        "status": "completed",
        "row_count": 1,
        "events": [
            {
                "source_table_full_name": "marketplace_lab.silver.orders",
                "target_table_full_name": "marketplace_lab.gold.fact_orders",
            }
        ],
    }

    lineage_provider.get_column_lineage.return_value = {
        "status": "completed",
        "row_count": 0,
        "events": [],
    }

    full_name = "marketplace_lab.gold.fact_orders"

    result = investigate_databricks_object(
        full_name=full_name,
        metadata_provider=metadata_provider,
        lineage_provider=lineage_provider,
    )

    assert result["status"] == "completed"
    assert result["metadata"]["table_type"] == "MANAGED"
    assert result["table_lineage"]["row_count"] == 1
    assert result["column_lineage"]["row_count"] == 0

    metadata_provider.describe_table.assert_called_once_with(
        full_name
    )

    lineage_provider.get_table_lineage.assert_called_once_with(
        full_name
    )

    lineage_provider.get_column_lineage.assert_called_once_with(
        full_name
    )

    print("STAGE 6.6.2: PASSED")


if __name__ == "__main__":
    main()