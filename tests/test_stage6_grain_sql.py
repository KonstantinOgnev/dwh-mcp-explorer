from dwh_mcp.databricks_reconciliation import (
    build_grain_validation_sql,
)


def main():
    sql = build_grain_validation_sql(
        "marketplace_lab.gold.fact_orders",
        "order_id",
    )

    assert "COUNT(DISTINCT `order_id`)" in sql
    assert "`marketplace_lab`.`gold`.`fact_orders`" in sql

    try:
        build_grain_validation_sql(
            "marketplace_lab.gold.fact_orders;DROP TABLE x",
            "order_id",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Unsafe identifier was accepted")

    print(sql)
    print("STAGE 6.7.3: PASSED")


if __name__ == "__main__":
    main()