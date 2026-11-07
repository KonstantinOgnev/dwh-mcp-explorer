from typing import Any
import re


def reconcile_grain(
    full_name: str,
    key_column: str,
    total_rows: int,
    distinct_keys: int,
    null_keys: int,
) -> dict[str, Any]:
    """
    Validate table grain using exact aggregate counts.
    """

    duplicate_rows = total_rows - distinct_keys - null_keys

    passed = duplicate_rows == 0 and null_keys == 0

    return {
        "table_name": full_name,
        "key_column": key_column,
        "total_rows": total_rows,
        "distinct_keys": distinct_keys,
        "duplicate_rows": duplicate_rows,
        "null_keys": null_keys,
        "status": "passed" if passed else "failed",
    }

def build_grain_validation_sql(
    full_name: str,
    key_column: str,
) -> str:
    """
    Build a read-only SQL query for grain validation.

    Accepts only simple catalog.schema.table identifiers
    and a single simple key column.
    """

    identifier_pattern = r"[A-Za-z_][A-Za-z0-9_]*"

    table_parts = full_name.split(".")

    if len(table_parts) != 3 or not all(
        re.fullmatch(identifier_pattern, part)
        for part in table_parts
    ):
        raise ValueError("Invalid fully qualified table name")

    if not re.fullmatch(identifier_pattern, key_column):
        raise ValueError("Invalid key column name")

    table_sql = ".".join(f"`{part}`" for part in table_parts)
    key_sql = f"`{key_column}`"

    return f"""
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT {key_sql}) AS distinct_keys,
    SUM(CASE WHEN {key_sql} IS NULL THEN 1 ELSE 0 END) AS null_keys
FROM {table_sql}
""".strip()