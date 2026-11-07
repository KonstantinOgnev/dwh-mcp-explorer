
from unittest.mock import patch

from dwh_mcp import reporting as reporting_service


def main():
    original = reporting_service.lineage_service.get_table_lineage

    with patch.object(
        reporting_service.lineage_service,
        "get_table_lineage",
        wraps=original
    ) as mocked_lineage:

        report = reporting_service.generate_reconciliation_report(
            "gold",
            "fact_orders",
            "fact_orders.sql"
        )

        assert mocked_lineage.call_count == 1, (
            f"Expected 1 lineage call, got "
            f"{mocked_lineage.call_count}"
        )

    assert report["overall_status"] == "WARNING"
    assert report["summary"]["column_count"] == 5
    assert report["summary"]["status_counts"]["PASS"] == 4
    assert report["summary"]["status_counts"]["WARNING"] == 1

    print("PASS: Lineage calculated only once")
    print("PASS: Reporting output unchanged")
    print("STAGE 5.3.2 REPORTING REUSE: PASSED")


if __name__ == "__main__":
    main()
