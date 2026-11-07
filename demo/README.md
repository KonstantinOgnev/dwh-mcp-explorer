# DWH MCP Explorer — Demo Scenarios

This document demonstrates practical data engineering workflows supported by **DWH MCP Explorer**, a Python-based Model Context Protocol (MCP) server integrated with PostgreSQL, SQL transformation repositories, and Azure Databricks.

The scenarios illustrate how an AI client, such as Claude Desktop, can use structured MCP tools to investigate data warehouse objects.

All examples are intended for demonstration and technical evaluation. Actual results depend on the connected environment.

## Demo 1 — PostgreSQL Metadata Exploration

### Objective

Investigate the structure of an existing data warehouse table, including its columns, primary key, foreign keys, and relationships with other objects.

### Target Object

`gold.fact_orders`

### MCP Tools

- `list_schemas`
- `list_tables`
- `describe_table`
- `get_primary_keys`
- `get_foreign_keys`

### Claude Desktop Prompt

> Using the connected DWH MCP Explorer server, investigate the PostgreSQL table `gold.fact_orders`.
>
> Retrieve its metadata, columns, primary key, and foreign keys. Identify the relationships with other DWH objects and prepare a concise technical report.
>
> Use only information returned by the MCP tools. Clearly identify any missing metadata.

### Expected Result

A structured report containing:

- Table schema and definition
- Column names and types
- Primary-key information
- Foreign-key relationships
- Related tables
- Technical observations

### Engineering Value

Accelerates schema discovery and dependency investigation without requiring the user to manually inspect multiple PostgreSQL system catalogs.

---

## Demo 2 — DWH SQL Mapping and Reconciliation

### Objective

Compare a SQL transformation definition with the target DWH metadata to identify inconsistencies in column mappings or constraints.

### Target Objects

- Target table: `gold.fact_orders`
- SQL transformation: `fact_orders.sql`

### MCP Tools

- `list_sql_files`
- `read_sql_file`
- `get_table_knowledge`
- `get_table_lineage`
- `reconcile_table_mapping`
- `reconcile_column_constraints`
- `investigate_dwh_object`

### Claude Desktop Prompt

> Using DWH MCP Explorer, investigate the target table `gold.fact_orders` and its SQL transformation definition `fact_orders.sql`.
>
> Review the available metadata, SQL mapping, lineage, and column constraints.
>
> Identify confirmed inconsistencies, potential mapping risks, and any areas where additional evidence is required.
>
> Produce a reconciliation report, distinguishing confirmed findings from assumptions.

### Expected Result

- Source and target mapping overview
- Available lineage information
- Column constraint comparison
- Identified discrepancies
- Reconciliation findings and evidence limitations

### Engineering Value

Supports impact analysis, SQL migration validation, and investigation of data warehouse transformation logic.

---

## Demo 3 — Azure Databricks Knowledge Object Investigation

### Objective

Collect and combine Unity Catalog metadata, table-level lineage, and column-level lineage into a unified technical Knowledge Object.

### Target Object

`marketplace_lab.gold.fact_orders`

### MCP Tools

- `databricks_describe_table`
- `databricks_get_table_lineage`
- `databricks_get_column_lineage`
- `databricks_investigate_object`

### Claude Desktop Prompt

> Using the connected DWH MCP Explorer server, execute `databricks_investigate_object` for `marketplace_lab.gold.fact_orders`.
>
> Analyze the returned Knowledge Object and prepare a technical report covering:
>
> 1. Table metadata and storage format.
> 2. Column definitions.
> 3. Confirmed upstream dependencies.
> 4. Confirmed downstream dependencies.
> 5. Examples of column-level lineage.
> 6. Available job, notebook, and SQL query identifiers.
> 7. Evidence sources and limitations.
>
> Do not invent transformation logic or dependencies that are not supported by the returned metadata.

### Expected Result

A unified technical report based on Unity Catalog and Databricks lineage system tables.

### Example Findings from Project Validation

During an earlier project investigation, the following upstream dependencies were observed:

- `marketplace_lab.silver.orders`
- `marketplace_lab.silver.order_items`
- `marketplace_lab.gold.dim_user`
- `marketplace_lab.gold.dim_seller`

Observed downstream objects included marketplace fact tables and analytical aggregates.

These observations belong to the tested environment and may change as pipelines execute.

### Engineering Value

Demonstrates metadata integration across a cloud data platform and evidence-based AI-assisted investigation of data dependencies.

---

## Demo 4 — Data Grain Validation

### Objective

Verify whether a fact table satisfies the expected business grain of one row per business key.

### Target Object

`marketplace_lab.gold.fact_orders`

### Business Key

`order_id`

### MCP Tool

- `databricks_validate_grain`

### Claude Desktop Prompt

> Using the connected DWH MCP Explorer server, execute `databricks_validate_grain` with the following parameters:
>
> - `full_name`: `marketplace_lab.gold.fact_orders`
> - `key_column`: `order_id`
>
> Prepare a concise validation report including total rows, distinct business keys, duplicate rows, NULL keys, and the overall validation status.
>
> Use only the result of this MCP tool and do not modify any data.

### Validated Project Result

| Metric | Result |
|---|---:|
| Total rows | 10,000 |
| Distinct `order_id` values | 10,000 |
| Duplicate rows | 0 |
| NULL keys | 0 |
| Validation status | PASSED |

### Interpretation

The observed dataset satisfies the declared grain of one row per `order_id`.

This result validates the tested snapshot only. It does not guarantee that future pipeline executions will preserve the same grain.

### Engineering Value

Demonstrates how MCP-based tooling can support automated data quality investigation and validation of dimensional modeling assumptions.

---

## Running the Demonstrations

### Prerequisites

- The DWH MCP Explorer Python environment is configured.
- Claude Desktop is connected to the MCP server.
- PostgreSQL connectivity is available for Demos 1 and 2.
- Databricks authentication, Unity Catalog permissions, and SQL Warehouse access are available for Demos 3 and 4.

### Execution Procedure

1. Open Claude Desktop.
2. Confirm that the DWH MCP Explorer connector is available.
3. Start a new conversation.
4. Copy one of the prompts above.
5. Allow the requested MCP tools to execute.
6. Review the returned results and generated technical report.
7. Verify any significant technical findings against source metadata when necessary.

## Important Limitations

- MCP results depend on the connected environment and available permissions.
- Databricks lineage is observational and may be incomplete.
- SQL mapping reconciliation may identify risks requiring additional investigation.
- AI-generated explanations must be distinguished from directly retrieved evidence.
- SQL Warehouse execution can incur cloud compute costs.
- Demonstration results should not expose credentials, tokens, or confidential business data.

## Related Documentation

- [Main Project README](../README.md)
- [Technical Documentation Index](../docs/README.md)
- [Solution Architecture](../docs/architecture/DWH_MCP_Explorer_Architecture_EN.pdf)
- [Technical Implementation Guide](../docs/implementation/DWH_MCP_Explorer_Technical_Guide_EN.pdf)
- [Testing and Validation Guide](../docs/testing/DWH_MCP_Explorer_Testing_Validation_EN.pdf)

---

**DWH MCP Explorer** — Practical MCP applications for Data Engineering, Data Warehouse Architecture, Metadata Management, Data Lineage, and Data Quality.
