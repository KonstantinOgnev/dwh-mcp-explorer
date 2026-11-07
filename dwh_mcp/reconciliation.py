
from dwh_mcp import database as db
from dwh_mcp import lineage as lineage_service



def reconcile_table_mapping(
    schema: str,
    table: str,
    filename: str,
    lineage_data: dict | None = None,
    target_columns_data: list[dict] | None = None
) -> dict:
    """Compare SQL target columns with PostgreSQL metadata."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    lineage = (
        lineage_data
        if lineage_data is not None
        else lineage_service.get_table_lineage(filename)
    )

    expected_target = f"{schema}.{table}"

    if lineage["target_table"] != expected_target:
        raise ValueError(
            "SQL target does not match requested table"
        )

    target_metadata = (
        target_columns_data
        if target_columns_data is not None
        else db.describe_table(schema, table)
    )

    db_columns = {
        col["name"]
        for col in target_metadata
    }

    mapped_columns = {
        item["target_column"]
        for item in lineage["column_mapping"]
    }

    missing_in_sql = sorted(db_columns - mapped_columns)
    missing_in_database = sorted(mapped_columns - db_columns)

    return {
        "object": expected_target,
        "source_file": filename,
        "database_columns": sorted(db_columns),
        "mapped_columns": sorted(mapped_columns),
        "missing_in_sql": missing_in_sql,
        "missing_in_database": missing_in_database,
        "mapping_complete": (
            not missing_in_sql
            and not missing_in_database
        ),
        "reconciliation_level": "target_columns"
    }

def reconcile_column_constraints(
    schema: str,
    table: str,
    filename: str,
    lineage_data: dict | None = None,
    target_columns_data: list[dict] | None = None
) -> dict:

    """Compare source and target column types and nullability."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    lineage = (
    lineage_data
    if lineage_data is not None
    else lineage_service.get_table_lineage(filename)
    )
    target_name = f"{schema}.{table}"

    if lineage["target_table"] != target_name:
        raise ValueError("SQL target does not match requested table")

    target_metadata = (
        target_columns_data
        if target_columns_data is not None
        else db.describe_table(schema, table)
    )

    target_columns = {
        col["name"]: col
        for col in target_metadata
    }

    source_aliases = {}
    for source in lineage["source_tables"]:
        source_aliases[source["alias"]] = source["table"]

    source_metadata = {}

    for full_name in set(source_aliases.values()):
        parts = full_name.split(".")

        if len(parts) != 2 or parts[0] not in ("staging", "gold"):
            raise ValueError(f"Unsupported source: {full_name}")

        src_schema, src_table = parts

        source_metadata[full_name] = {
            col["name"]: col
            for col in db.describe_table(
                src_schema, src_table
            )
        }

    results = []

    for mapping in lineage["column_mapping"]:
        target_col = mapping["target_column"]
        expression = mapping["source_expression"]
        refs = mapping["source_columns"]

        item = {
            "target_column": target_col,
            "source_expression": expression,
            "checks": [],
            "status": "UNKNOWN"
        }

        if target_col not in target_columns:
            item["checks"].append("Target column not found")
            item["status"] = "FAIL"
            results.append(item)
            continue

        # This version supports basic direct-column checks.
        if len(refs) != 1:
            item["checks"].append(
                "Expression needs advanced type analysis"
            )
            results.append(item)
            continue

        reference = refs[0].split(".")

        if len(reference) != 2:
            item["checks"].append(
                "Unqualified source column"
            )
            results.append(item)
            continue

        alias, source_col = reference
        source_table = source_aliases.get(alias)

        if not source_table:
            item["checks"].append("Source alias not resolved")
            results.append(item)
            continue

        source = source_metadata[source_table].get(source_col)

        if not source:
            item["checks"].append("Source column not found")
            item["status"] = "FAIL"
            results.append(item)
            continue

        target = target_columns[target_col]

        source_type = source["type"].lower()
        target_type = target["type"].lower()

        # Conservative comparison: exact matches only.
        type_status = (
            "PASS" if source_type == target_type
            else "WARNING"
        )

        source_nullable = source["nullable"] == "YES"
        target_nullable = target["nullable"] == "YES"

        if source_nullable and not target_nullable:
            null_status = "WARNING"
            null_message = "Potential NOT NULL violation"
        elif not source_nullable and target_nullable:
            null_status = "WARNING"
            null_message = "Target allows NULL; source does not"
        else:
            null_status = "PASS"
            null_message = "Nullability compatible"

        item["source_table"] = source_table
        item["source_column"] = source_col
        item["source_type"] = source_type
        item["target_type"] = target_type
        item["type_status"] = type_status
        item["nullability_status"] = null_status
        item["checks"].append(null_message)

        # Preserve existing direct-reference validation.
        if expression.replace(" ", "") not in (
            f"{alias}.{source_col}",
            f"{alias}.{source_col}AS{target_col}"
        ):
            item["status"] = "UNKNOWN"
            item["checks"].append(
                "Expression requires further validation"
            )
        elif "WARNING" in (type_status, null_status):
            item["status"] = "WARNING"
        else:
            item["status"] = "PASS"

        results.append(item)

    return {
        "target_table": target_name,
        "source_file": filename,
        "checks": results,
        "check_count": len(results),
        "status": "completed",
        "validation_scope": "direct_column_metadata"
    }
