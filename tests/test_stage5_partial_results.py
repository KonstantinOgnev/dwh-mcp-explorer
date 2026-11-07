
from unittest.mock import patch

from dwh_mcp import composition


def main():
    with patch.object(
        composition.reporting_service,
        "generate_reconciliation_report",
        side_effect=ValueError("Simulated SQL parsing failure")
    ):
        result = composition.investigate_dwh_object(
            "gold",
            "fact_orders",
            "fact_orders.sql"
        )

    assert result["investigation_status"] == "partial"
    assert result["overall_status"] == "UNKNOWN"
    assert result["metadata"] is not None
    assert result["lineage"] is None

    assert len(result["errors"]) == 1
    assert result["errors"][0]["component"] == "reporting"

    print("PASS: Reporting failure isolated")
    print("PASS: PostgreSQL knowledge preserved")
    print("PASS: Partial investigation returned")
    print("STAGE 5.3.3 PARTIAL RESULTS: PASSED")


if __name__ == "__main__":
    main()
