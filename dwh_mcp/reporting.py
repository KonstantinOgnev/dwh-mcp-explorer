
from dwh_mcp import database as db
from dwh_mcp import sql_repository as sql_repo
from dwh_mcp import lineage as lineage_service
from dwh_mcp import reconciliation as reconciliation_service


def get_table_knowledge(schema: str, table: str) -> dict:
    """Collect DWH metadata and SQL transformation knowledge."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    columns = db.describe_table(schema, table)
    primary_keys = db.get_primary_keys(schema, table)
    foreign_keys = db.get_foreign_keys(schema, table)

    sql_filename = f"{table}.sql"
    sql_files = sql_repo.list_sql_files()["files"]

    transformation = None

    if sql_filename in sql_files:
        sql_data = sql_repo.read_sql_file(sql_filename)

        transformation = {
            "filename": sql_filename,
            "content": sql_data["content"],
            "line_count": sql_data["line_count"]
        }

    return {
        "object": f"{schema}.{table}",
        "metadata": {
            "source_type": "postgresql",
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys
        },
        "transformation": transformation,
        "sources": [
            {
                "source_type": "postgresql",
                "object": f"{schema}.{table}"
            },
            {
                "source_type": "local_sql",
                "file": sql_filename,
                "available": transformation is not None
            }
        ],
        "knowledge_status": (
            "metadata_and_sql_collected"
            if transformation is not None
            else "metadata_only"
        )
    }


def generate_reconciliation_report(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Generate a structured DWH reconciliation report."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    target = f"{schema}.{table}"

    # 1. Collect knowledge, lineage and reconciliation.

    knowledge = get_table_knowledge(schema, table)

    # Parse SQL once and share the result.
    lineage = lineage_service.get_table_lineage(filename)


    # Reuse metadata already collected for the target table.
    target_columns_data = knowledge["metadata"]["columns"]

    mapping = reconciliation_service.reconcile_table_mapping(
        schema,
        table,
        filename,
        lineage_data=lineage,
        target_columns_data=target_columns_data
    )

    constraints = reconciliation_service.reconcile_column_constraints(
        schema,
        table,
        filename,
        lineage_data=lineage,
        target_columns_data=target_columns_data
    )

    # 2. Verify requested target.
    if lineage["target_table"] != target:
        raise ValueError("Target table mismatch")

    # 3. Build findings.
    findings = []

    for column in mapping["missing_in_sql"]:
        findings.append({
            "severity": "FAIL",
            "category": "MISSING_IN_SQL",
            "column": column,
            "message": "Database column is not mapped",
            "evidence": [
                f"postgresql:{target}",
                f"sql:{filename}"
            ]
        })

    for column in mapping["missing_in_database"]:
        findings.append({
            "severity": "FAIL",
            "category": "MISSING_IN_DATABASE",
            "column": column,
            "message": "SQL target column not found in database",
            "evidence": [
                f"postgresql:{target}",
                f"sql:{filename}"
            ]
        })

    for check in constraints["checks"]:
        if check["status"] == "PASS":
            continue

        findings.append({
            "severity": check["status"],
            "category": "COLUMN_CONSTRAINT",
            "column": check["target_column"],
            "message": (
                "; ".join(check["checks"])
                or "Column constraint requires review"
            ),
            "source_expression": check["source_expression"],
            "evidence": [
                f"sql:{filename}",
                f"postgresql:{target}",
                f"postgresql:{check['source_table']}"
            ] if check.get("source_table") else [
                f"sql:{filename}",
                f"postgresql:{target}"
            ]
        })

    # 4. Calculate summary.
    status_counts = {
        "PASS": 0,
        "WARNING": 0,
        "FAIL": 0,
        "UNKNOWN": 0
    }

    for check in constraints["checks"]:
        status_counts[check["status"]] += 1

    if findings:
        if any(f["severity"] == "FAIL" for f in findings):
            overall_status = "FAIL"
        elif any(f["severity"] == "WARNING" for f in findings):
            overall_status = "WARNING"
        else:
            overall_status = "UNKNOWN"
    else:
        overall_status = "PASS"

    # 5. Build report without changing existing JSON contract.
    return {
        "report_type": "DWH_RECONCILIATION",
        "report_version": "1.0",
        "object": target,
        "source_file": filename,
        "overall_status": overall_status,

        "metadata": knowledge["metadata"],

        "transformation": {
            "filename": filename,
            "available": knowledge["transformation"] is not None
        },

        "lineage": {
            "source_tables": lineage["source_tables"],
            "joins": lineage["joins"],
            "column_mapping": lineage["column_mapping"]
        },

        "reconciliation": {
            "mapping_complete": mapping["mapping_complete"],
            "missing_in_sql": mapping["missing_in_sql"],
            "missing_in_database": mapping["missing_in_database"],
            "column_checks": constraints["checks"]
        },

        "summary": {
            "column_count": constraints["check_count"],
            "status_counts": status_counts,
            "finding_count": len(findings)
        },

        "findings": findings,

        "evidence_sources": knowledge["sources"],

        "limitations": [
            "Static SQL analysis only",
            "No SQL transformations executed",
            "No row-level data quality validation",
            "No complete SQL expression type inference",
            "Evidence references are logical identifiers"
        ]
    }
