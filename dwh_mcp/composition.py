
from dwh_mcp import reporting as reporting_service

from dwh_mcp import reporting as reporting_service
from dwh_mcp.errors import classify_error

def investigate_dwh_object(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Investigate a DWH object with partial-result support."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    target = f"{schema}.{table}"

    try:
        report = reporting_service.generate_reconciliation_report(
            schema, table, filename
        )

    except Exception as report_error:
        # Try to preserve metadata when reporting fails.
        errors = [
            classify_error("reporting", report_error)
        ]

        try:
            knowledge = reporting_service.get_table_knowledge(
                schema, table
            )

        except Exception as knowledge_error:
            errors.append(
                classify_error("knowledge", knowledge_error)
            )

            return {
                "investigation_type": "DWH_OBJECT",
                "object": target,
                "sql_file": filename,
                "overall_status": "UNKNOWN",
                "investigation_status": "failed",
                "metadata": None,
                "lineage": None,
                "reconciliation": None,
                "summary": None,
                "findings": [],
                "evidence_sources": [],
                "limitations": [],
                "knowledge_status": "unavailable",
                "errors": errors
            }

        return {
            "investigation_type": "DWH_OBJECT",
            "object": target,
            "sql_file": filename,
            "overall_status": "UNKNOWN",
            "investigation_status": "partial",
            "metadata": knowledge["metadata"],
            "lineage": None,
            "reconciliation": None,
            "summary": None,
            "findings": [],
            "evidence_sources": knowledge["sources"],
            "limitations": [
                "Reconciliation report could not be generated"
            ],
            "knowledge_status": knowledge["knowledge_status"],
            "errors": errors
        }

    knowledge_status = (
        "metadata_and_sql_collected"
        if report["transformation"]["available"]
        else "metadata_only"
    )

    return {
        "investigation_type": "DWH_OBJECT",
        "object": target,
        "sql_file": filename,
        "knowledge_status": knowledge_status,
        "overall_status": report["overall_status"],
        "metadata": report["metadata"],
        "lineage": report["lineage"],
        "reconciliation": report["reconciliation"],
        "summary": report["summary"],
        "findings": report["findings"],
        "evidence_sources": report["evidence_sources"],
        "limitations": report["limitations"],
        "investigation_status": "completed",
        "errors": []
    }
