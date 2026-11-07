
from unittest.mock import patch

from dwh_mcp import lineage as lineage_service
from dwh_mcp import reconciliation as reconciliation_service


def main():
    filename = "fact_orders.sql"

    # Calculate lineage once.
    lineage_data = lineage_service.get_table_lineage(filename)

    # Prevent any additional SQL parsing through this function.
    with patch.object(
        reconciliation_service.lineage_service,
        "get_table_lineage",
        side_effect=AssertionError("Unexpected repeated lineage parsing")
    ):
        mapping = reconciliation_service.reconcile_table_mapping(
            "gold",
            "fact_orders",
            filename,
            lineage_data=lineage_data
        )

        constraints = (
            reconciliation_service.reconcile_column_constraints(
                "gold",
                "fact_orders",
                filename,
                lineage_data=lineage_data
            )
        )

    assert mapping["mapping_complete"] is True
    assert constraints["check_count"] == 5

    print("PASS: Shared lineage accepted by reconciliation")
    print("PASS: No repeated lineage parsing")
    print("STAGE 5.3.2 SHARED LINEAGE: PASSED")


if __name__ == "__main__":
    main()
