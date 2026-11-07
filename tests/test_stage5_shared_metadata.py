
from unittest.mock import patch

from dwh_mcp import database as db
from dwh_mcp import reporting as reporting_service


def main():
    original = db.describe_table
    calls = []

    def traced_describe_table(schema, table):
        calls.append((schema, table))
        return original(schema, table)

    with patch.object(
        db,
        "describe_table",
        side_effect=traced_describe_table
    ):
        report = reporting_service.generate_reconciliation_report(
            "gold",
            "fact_orders",
            "fact_orders.sql"
        )

    target_calls = calls.count(("gold", "fact_orders"))

    assert target_calls == 1, (
        f"Expected one target metadata request, "
        f"got {target_calls}: {calls}"
    )

    assert report["overall_status"] == "WARNING"
    assert report["summary"]["column_count"] == 5
    assert report["summary"]["status_counts"]["PASS"] == 4
    assert report["summary"]["status_counts"]["WARNING"] == 1

    print("PASS: Target metadata requested only once")
    print("PASS: Reporting contract preserved")
    print("Metadata calls:", calls)
    print("STAGE 5.3.2 SHARED METADATA: PASSED")


if __name__ == "__main__":
    main()
