
from unittest.mock import patch

from dwh_mcp import composition
from dwh_mcp import database as db
from dwh_mcp import lineage


def main():
    original_describe = db.describe_table
    original_lineage = lineage.get_table_lineage

    metadata_calls = []

    def traced_describe(schema, table):
        metadata_calls.append((schema, table))
        return original_describe(schema, table)

    with (
        patch.object(
            db,
            "describe_table",
            side_effect=traced_describe
        ),
        patch.object(
            lineage,
            "get_table_lineage",
            wraps=original_lineage
        ) as lineage_mock
    ):
        investigation = composition.investigate_dwh_object(
            "gold",
            "fact_orders",
            "fact_orders.sql"
        )

        lineage_calls = lineage_mock.call_count

    assert investigation["investigation_status"] == "completed"
    assert investigation["overall_status"] == "WARNING"
    assert investigation["summary"]["column_count"] == 5

    assert lineage_calls == 1, (
        f"Expected 1 lineage call, got {lineage_calls}"
    )

    expected_metadata_calls = {
        ("gold", "fact_orders"),
        ("staging", "orders"),
        ("gold", "dim_customer")
    }

    assert set(metadata_calls) == expected_metadata_calls
    assert len(metadata_calls) == 3, metadata_calls

    print("PASS: Composite investigation completed")
    print("PASS: SQL lineage parsed once")
    print("PASS: PostgreSQL metadata reused")
    print("Lineage calls:", lineage_calls)
    print("Metadata calls:", metadata_calls)
    print("STAGE 5.3.2 DEPENDENCY EXECUTION: PASSED")


if __name__ == "__main__":
    main()
