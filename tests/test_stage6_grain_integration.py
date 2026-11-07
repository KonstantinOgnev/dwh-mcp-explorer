
from dwh_mcp.databricks_grain_provider import (
    DatabricksGrainProvider,
)


def main():
    provider = DatabricksGrainProvider()

    result = provider.validate_grain(
        full_name="marketplace_lab.gold.fact_orders",
        key_column="order_id",
    )

    assert result["status"] == "passed"
    assert result["total_rows"] == 10000
    assert result["distinct_keys"] == 10000
    assert result["duplicate_rows"] == 0
    assert result["null_keys"] == 0

    print("TABLE:", result["table_name"])
    print("KEY COLUMN:", result["key_column"])
    print("TOTAL ROWS:", result["total_rows"])
    print("DISTINCT KEYS:", result["distinct_keys"])
    print("DUPLICATE ROWS:", result["duplicate_rows"])
    print("NULL KEYS:", result["null_keys"])
    print("VALIDATION STATUS:", result["status"])

    print("STAGE 6.7.6: PASSED")


if __name__ == "__main__":
    main()
