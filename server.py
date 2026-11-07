
import os

import psycopg
from dotenv import load_dotenv
from mcp.server import MCPServer
from pathlib import Path
from dwh_mcp import database as db
from dwh_mcp import sql_repository as sql_repo
from dwh_mcp import lineage as lineage_service
from dwh_mcp import reconciliation as reconciliation_service
from dwh_mcp import reporting as reporting_service
from dwh_mcp import composition as composition_service
from dwh_mcp.databricks_provider import DatabricksMetadataProvider
from dwh_mcp.databricks_lineage_provider import DatabricksLineageProvider

from dwh_mcp.databricks_knowledge import (
    investigate_databricks_object,
)

from dwh_mcp.databricks_grain_provider import (
    DatabricksGrainProvider,
)

load_dotenv()

# Initialize MCP Server
mcp = MCPServer("DWH Metadata Explorer")


def get_connection():
    return db.get_connection()

@mcp.tool()
def list_schemas() -> dict[str, list[str]]:
    """List available DWH schemas as structured JSON."""
    return db.list_schemas()


@mcp.tool()
def list_tables(schema: str) -> dict:
    """List DWH tables in structured JSON format."""
    return db.list_tables(schema)


@mcp.tool()
def describe_table(schema: str, table: str) -> list[dict]:
    """Retrieve column metadata from PostgreSQL."""
    return db.describe_table(schema, table)


@mcp.tool()
def get_primary_keys(schema: str, table: str) -> list[dict]:
    """Return primary key columns for a DWH table."""
    return db.get_primary_keys(schema, table)


@mcp.tool()
def get_foreign_keys(schema: str, table: str) -> list[dict]:
    """Return foreign key relationships for a DWH table."""
    return db.get_foreign_keys(schema, table)

@mcp.tool()
def list_sql_files() -> dict:
    """List SQL transformation files available for DWH discovery."""
    return sql_repo.list_sql_files()

@mcp.tool()
def read_sql_file(filename: str) -> dict:
    """Read a SQL transformation file from the approved directory."""
    return sql_repo.read_sql_file(filename)

@mcp.tool()
def get_table_knowledge(schema: str, table: str) -> dict:
    """Collect DWH metadata and SQL transformation knowledge."""
    return reporting_service.get_table_knowledge(
        schema, table
    )

@mcp.tool()
def get_table_lineage(filename: str) -> dict:
    """Extract table-level and column-level SQL lineage."""
    return lineage_service.get_table_lineage(filename)

@mcp.tool()
def reconcile_table_mapping(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Compare SQL target columns with PostgreSQL metadata."""
    return reconciliation_service.reconcile_table_mapping(
        schema, table, filename
    )

@mcp.tool()
def reconcile_column_constraints(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Compare source and target column types and nullability."""
    return reconciliation_service.reconcile_column_constraints(
        schema, table, filename
    )

@mcp.tool()
def generate_reconciliation_report(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Generate a structured DWH reconciliation report."""
    return reporting_service.generate_reconciliation_report(
        schema, table, filename
    )

@mcp.tool()
def investigate_dwh_object(
    schema: str,
    table: str,
    filename: str
) -> dict:
    """Investigate DWH metadata, lineage and reconciliation."""

    return composition_service.investigate_dwh_object(
        schema, table, filename
    )

@mcp.resource(
    "dwh://explorer/capabilities",
    name="dwh_explorer_capabilities",
    mime_type="application/json"
)
def dwh_explorer_capabilities() -> str:
    """Describe the DWH Metadata Explorer capabilities."""

    import json

    capabilities = {
        "service": "DWH Metadata Explorer",
        "version": "1.0",
        "supported_schemas": ["staging", "gold"],
        "sources": ["postgresql", "local_sql"],
        "capabilities": [
            "schema_discovery",
            "table_metadata",
            "primary_and_foreign_keys",
            "sql_lineage",
            "column_mapping",
            "structural_reconciliation",
            "constraint_validation",
            "composite_investigation",
            "partial_results",
            "error_classification"
        ],
        "analysis_scope": "static_metadata_and_sql",
        "sql_execution": False
    }

    return json.dumps(capabilities, indent=2)


@mcp.resource(
    "dwh://tables/{schema}/{table}",
    name="dwh_table_metadata",
    mime_type="application/json"
)
def dwh_table_metadata(schema: str, table: str) -> str:
    """Expose PostgreSQL DWH table metadata as an MCP resource."""

    import json

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    tables = db.list_tables(schema)["tables"]

    if table not in tables:
        raise ValueError("Table not found")

    metadata = {
        "object": f"{schema}.{table}",
        "source_type": "postgresql",
        "columns": db.describe_table(schema, table),
        "primary_keys": db.get_primary_keys(schema, table),
        "foreign_keys": db.get_foreign_keys(schema, table)
    }

    return json.dumps(metadata, indent=2)

@mcp.prompt()
def investigate_dwh_table(
    schema: str,
    table: str,
    filename: str
) -> str:
    """Investigate a DWH table using metadata and SQL lineage."""

    if schema not in ("staging", "gold"):
        raise ValueError("Schema is not allowed")

    return f"""
Investigate the DWH object {schema}.{table}.

SQL transformation file: {filename}

Use the connected DWH Metadata Explorer MCP server.

1. Call investigate_dwh_object with:
   schema = {schema}
   table = {table}
   filename = {filename}

2. Treat the tool output as the authoritative evidence
   for metadata, lineage, reconciliation and findings.

3. Produce a structured report containing:
   - Overall investigation status
   - Table metadata and primary/foreign keys
   - Table-level and column-level lineage
   - Reconciliation findings and severity
   - Data engineering recommendations
   - Analysis limitations

4. Distinguish confirmed findings from recommendations.

5. If investigation_status is partial or failed,
   explicitly explain missing evidence and errors.

6. Do not claim that SQL transformations were executed.
   Do not invent unavailable metadata or validation results.

Respond in English.
""".strip()

# ---------------------------------------------------------
# Databricks Unity Catalog MCP Tools
# Stage 6.4
# ---------------------------------------------------------

def _databricks_provider() -> DatabricksMetadataProvider:
    return DatabricksMetadataProvider()


@mcp.tool()
def databricks_list_catalogs() -> list[str]:
    """List accessible Databricks Unity Catalog catalogs."""
    return _databricks_provider().list_catalogs()


@mcp.tool()
def databricks_list_schemas(
    catalog_name: str = "marketplace_lab",
) -> list[str]:
    """List schemas in a Databricks Unity Catalog catalog."""
    return _databricks_provider().list_schemas(catalog_name)


@mcp.tool()
def databricks_list_tables(
    catalog_name: str,
    schema_name: str,
) -> list[str]:
    """List tables in a Databricks Unity Catalog schema."""
    return _databricks_provider().list_tables(
        catalog_name,
        schema_name,
    )


@mcp.tool()
def databricks_describe_table(
    full_name: str,
) -> dict:
    """Describe a Unity Catalog table and its columns."""
    return _databricks_provider().describe_table(full_name)


# ---------------------------------------------------------
# Databricks Lineage MCP Tools
# Stage 6.5.7
# ---------------------------------------------------------

def _databricks_lineage_provider() -> DatabricksLineageProvider:
    return DatabricksLineageProvider()


@mcp.tool()
def databricks_get_table_lineage(full_name: str) -> dict:
    """
    Retrieve registered table-level lineage events
    from Databricks system.access.table_lineage.

    Read-only. Results may be limited or incomplete.
    """
    return _databricks_lineage_provider().get_table_lineage(
        full_name
    )


@mcp.tool()
def databricks_get_column_lineage(full_name: str) -> dict:
    """
    Retrieve registered column-level lineage events
    from Databricks system.access.column_lineage.

    Read-only. Results may be limited or incomplete.
    """
    return _databricks_lineage_provider().get_column_lineage(
        full_name
    )

@mcp.tool()
def databricks_investigate_object(full_name: str) -> dict:
    """
    Build a unified Knowledge Object for a Databricks table.

    Combines Unity Catalog metadata, table-level lineage,
    and column-level lineage into one structured response.
    Read-only operation.
    """
    return investigate_databricks_object(
        full_name=full_name,
        metadata_provider=DatabricksMetadataProvider(),
        lineage_provider=DatabricksLineageProvider(),
    )


@mcp.tool()
def databricks_validate_grain(
    full_name: str,
    key_column: str,
) -> dict:
    """
    Validate the grain of a Databricks table.

    Checks business-key uniqueness and NULL values
    using exact SQL aggregate counts.

    Returns a structured reconciliation report.
    Read-only operation.
    """
    return DatabricksGrainProvider().validate_grain(
        full_name=full_name,
        key_column=key_column,
    )

if __name__ == "__main__":
    mcp.run()
