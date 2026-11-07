
import psycopg
from unittest.mock import patch

from dwh_mcp import composition
from dwh_mcp import database as db


def test_missing_sql_file():
    """SQL unavailable, PostgreSQL metadata still available."""

    result = composition.investigate_dwh_object(
        "gold",
        "fact_orders",
        "missing_transformation.sql"
    )

    assert result["investigation_status"] == "partial"
    assert result["overall_status"] == "UNKNOWN"

    assert result["metadata"] is not None
    assert result["lineage"] is None
    assert result["reconciliation"] is None

    assert len(result["errors"]) == 1
    assert (
        result["errors"][0]["category"]
        == "SQL_FILE_NOT_FOUND"
    )
    assert result["errors"][0]["retryable"] is False

    print("PASS: Missing SQL file classified")
    print("PASS: Available PostgreSQL metadata preserved")


def test_database_unavailable():
    """Simulate PostgreSQL connection failure."""

    with patch.object(
        db,
        "get_connection",
        side_effect=psycopg.OperationalError(
            "Simulated connection failure"
        )
    ):
        result = composition.investigate_dwh_object(
            "gold",
            "fact_orders",
            "fact_orders.sql"
        )

    assert result["investigation_status"] == "failed"
    assert result["overall_status"] == "UNKNOWN"

    assert result["metadata"] is None
    assert result["lineage"] is None

    assert len(result["errors"]) == 2

    assert all(
        error["category"] == "SOURCE_UNAVAILABLE"
        for error in result["errors"]
    )

    assert all(
        error["retryable"] is True
        for error in result["errors"]
    )

    print("PASS: PostgreSQL outage classified")
    print("PASS: Failed investigation returned safely")


def main():
    test_missing_sql_file()
    test_database_unavailable()

    print("STAGE 5.3.3 FAILURE SCENARIOS: PASSED")


if __name__ == "__main__":
    main()
