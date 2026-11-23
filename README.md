# DWH MCP Explorer

**AI-assisted Data Warehouse metadata exploration, lineage analysis, and knowledge integration using Model Context Protocol (MCP).**

A Python-based MCP server that connects an AI client to PostgreSQL metadata, SQL transformation definitions, and Azure Databricks Unity Catalog.

The project demonstrates how engineering knowledge from heterogeneous data platforms can be collected, investigated, reconciled, and exposed through a unified tool interface.

## 1. Project Overview

Data warehouse knowledge is frequently distributed across multiple systems:

- Database schemas, tables, columns, and constraints
- SQL transformations and business logic
- Data lineage and object dependencies
- Cloud data platform metadata
- Data quality and validation results

Investigating an analytical data object often requires switching between database clients, SQL repositories, notebooks, and platform interfaces.

**DWH MCP Explorer addresses this challenge by exposing structured metadata and analysis capabilities through MCP tools.**

An AI client such as Claude Desktop can use these tools to investigate DWH objects and produce technical explanations grounded in retrieved metadata.

## 2. Architecture

```text
                    Claude Desktop
                     (MCP Client)
                           |
                     MCP Protocol
                           |
                   Python MCP Server
                       server.py
                           |
          +----------------+----------------+
          |                                 |
    PostgreSQL Services              Databricks Services
          |                                 |
  Database Metadata                  Unity Catalog
  SQL Repository                     Table Metadata
  Table Relationships                Table Lineage
  SQL Lineage                        Column Lineage
  Reconciliation                     Grain Validation
          |                                 |
          +----------------+----------------+
                           |
                 Knowledge Composition
                           |
                 Structured MCP Results
                           |
                    Claude Desktop
```

The architecture separates the MCP interface from platform-specific metadata providers and analytical services.

### Main design principles

- Modular Python implementation
- Separation of MCP tools and provider logic
- Structured tool responses
- Read-only metadata investigation
- Reusable reconciliation and knowledge composition
- Automated testing
- Environment-based credential management

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.11 |
| AI integration | Model Context Protocol (MCP) |
| MCP client | Claude Desktop |
| Relational database | PostgreSQL |
| Database driver | Psycopg |
| Cloud data platform | Azure Databricks |
| Metadata catalog | Unity Catalog |
| Data lineage | Databricks system tables |
| Databricks integration | Databricks Python SDK |
| SQL execution | Databricks SQL Warehouse |
| Dependency management | uv |
| Version control | Git / GitHub |

## 4. Main Capabilities

### PostgreSQL Metadata Exploration

Discover database objects and inspect schema definitions, including tables, columns, primary keys, and foreign keys.

### SQL Repository Investigation

Read SQL transformation definitions and investigate their relationships with source and target DWH objects.

### Data Lineage

Analyze table-level and column-level dependencies.

For Azure Databricks, lineage information is retrieved from:

- `system.access.table_lineage`
- `system.access.column_lineage`

Results describe observed relationships rather than guaranteeing a complete dependency graph.

### DWH Reconciliation

Compare metadata, SQL mappings, constraints, and available technical knowledge to identify potential inconsistencies.

### Databricks Knowledge Base Integration

Build a unified Knowledge Object combining:

- Unity Catalog table metadata
- Table-level lineage
- Column-level lineage
- Source evidence
- Analysis limitations

### Grain Validation

Validate whether a data warehouse table conforms to its expected business grain.

For example, the `marketplace_lab.gold.fact_orders` table uses `order_id` as its declared grain.

A validation checks total rows, distinct business keys, duplicate rows, and NULL keys.

### MCP Integration

The completed implementation includes **21 registered MCP tools**, covering PostgreSQL and Databricks metadata exploration, reconciliation, lineage investigation, and validation.

## 5. Example Use Case

**Investigating an order fact table**

Target object:

`marketplace_lab.gold.fact_orders`

The MCP workflow can:

1. Retrieve the table definition from Unity Catalog.
2. Identify columns and available table properties.
3. Retrieve observed upstream and downstream lineage.
4. Investigate available column-level mappings.
5. Assemble the findings into a structured Knowledge Object.
6. Validate the business grain using `order_id`.
7. Provide results to Claude Desktop for technical analysis.

In a validated project run, the grain check reported:

| Metric | Value |
|---|---:|
| Total rows | 10,000 |
| Distinct order IDs | 10,000 |
| Duplicate rows | 0 |
| NULL business keys | 0 |
| Validation status | PASSED |

These values represent the tested dataset, not a permanent property of the table.

## 6. Example MCP Tools

| Tool | Purpose |
|---|---|
| `list_schemas` | Explore PostgreSQL schemas |
| `describe_table` | Inspect PostgreSQL table metadata |
| `get_primary_keys` | Retrieve primary-key information |
| `get_foreign_keys` | Retrieve foreign-key information |
| `read_sql_file` | Retrieve SQL transformation definitions |
| `investigate_dwh_object` | Investigate a DWH object |
| `databricks_list_catalogs` | Explore Unity Catalog |
| `databricks_describe_table` | Inspect a Databricks table |
| `databricks_get_table_lineage` | Retrieve table lineage |
| `databricks_get_column_lineage` | Retrieve column lineage |
| `databricks_investigate_object` | Build a unified Knowledge Object |
| `databricks_validate_grain` | Validate table grain |

The table highlights selected tools rather than listing the complete tool registry.

## 7. Project Structure

```text
dwh-mcp-explorer/
├── dwh_mcp/
│   ├── database.py
│   ├── sql_repository.py
│   ├── lineage.py
│   ├── reconciliation.py
│   ├── composition.py
│   ├── databricks_provider.py
│   ├── databricks_lineage_provider.py
│   ├── databricks_knowledge.py
│   ├── databricks_grain_provider.py
│   └── databricks_reconciliation.py
├── sql_sources/
├── tests/
├── server.py
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── README.md
```

## 8. Local Setup

### Prerequisites

- Python 3.11
- uv package manager
- PostgreSQL instance for database-specific functionality
- Azure Databricks workspace for cloud-specific functionality
- Databricks CLI authentication
- An MCP-compatible client such as Claude Desktop

### Clone the repository

```bash
git clone https://github.com/KonstantinOgnev/dwh-mcp-explorer.git
cd dwh-mcp-explorer
```

### Install dependencies

```bash
uv sync
```

### Configure PostgreSQL

Copy `.env.example` to `.env` and supply your local connection settings.

Do not commit `.env` or credentials to version control.

### Configure Databricks

Authenticate using Databricks CLI and a named profile such as:

```bash
databricks auth login --profile MARKETPLACE_LAB
```

### Databricks SQL Warehouse Configuration

The SQL Warehouse ID is configured using an environment variable rather than being hardcoded in the source code.

Add the following setting to your local `.env` file:

```dotenv
DATABRICKS_WAREHOUSE_ID=your_warehouse_id
```

Replace `your_warehouse_id` with the ID of a SQL Warehouse accessible to your Databricks account.

The application loads `.env` through `python-dotenv` when `server.py` starts.

The `DatabricksGrainProvider` and `DatabricksLineageProvider` classes use this configuration for SQL execution. An explicit `warehouse_id` constructor argument can also be provided.

The `.env` file must remain local and must not be committed to Git.


The current project implementation uses the `MARKETPLACE_LAB` profile and a configured SQL Warehouse. Adapt these settings to your own workspace before running Databricks-specific functionality.

### Start the MCP server

```bash
uv run python server.py
```

For Claude Desktop, configure the MCP server as a local process using the project's Python environment and the absolute path to `server.py`.

See the Deployment and Configuration Guide for environment-specific instructions.

## 9. Testing

The project includes tests covering:

- Metadata provider behavior
- SQL repository operations
- Lineage and reconciliation
- MCP tool registration
- Knowledge Object composition
- Grain validation
- Error handling
- Cross-platform integration

Selected tests can be executed with:

```bash
uv run python -m tests.test_stage6_knowledge
uv run python -m tests.test_stage6_grain_provider
uv run python -m tests.test_stage6_cross_platform_registry
```

Integration tests requiring real PostgreSQL or Databricks connections need valid credentials and accessible services.

## 10. Security

The project follows a read-oriented metadata exploration design.

- PostgreSQL connection settings are loaded from environment variables.
- Local credentials are excluded from Git.
- Databricks authentication uses a named CLI profile.
- Metadata and validation results are exposed through MCP tools.
- Source files were checked using Gitleaks before the initial GitHub publication.

The project should be reviewed and configured appropriately before use against production systems.

## 11. Known Limitations

- Databricks lineage reflects observed, captured operations and may be incomplete.
- Lineage queries have lookback and row-count limits.
- Column lineage does not necessarily provide complete transformation expressions.
- Some investigations require a running Databricks SQL Warehouse.
- Local execution requires external PostgreSQL and/or Databricks resources.
- Platform-specific authentication and permissions must be configured separately.

## 12. Documentation and Demonstrations

The repository is being prepared with additional material covering:

- Solution Architecture
- Technical Implementation
- Deployment and Configuration
- Testing and Validation
- Demo Scenarios

The complete technical documentation is available here:

**[Technical Documentation — Architecture, Implementation, Deployment and Testing](docs/README.md)**

Documentation is provided in English and Russian.


### Demo Scenarios

Explore four practical MCP-based data engineering workflows:

- PostgreSQL Metadata Exploration
- DWH SQL Mapping and Reconciliation
- Azure Databricks Knowledge Object Investigation
- Data Grain Validation

**[Explore Demo Scenarios](demo/README.md)**

## 13. Autonomous Databricks Investigation Agent

The project also includes a command-line agent that uses the Claude API
to select and execute a restricted set of MCP tools.

Claude Desktop is not required for this mode. The runner connects to the
MCP server in process; a separate `server.py` process is not required.

### Configuration

Install the locked project dependencies:

```bash
uv sync --locked
```

Configure these values in the local `.env` file:

```dotenv
ANTHROPIC_API_KEY=your_api_key
DWH_AGENT_MODEL=your_available_model_id
DATABRICKS_WAREHOUSE_ID=your_warehouse_id
```

Databricks authentication uses the `MARKETPLACE_LAB` CLI profile.
The authenticated identity needs access to the target table, lineage
system tables, and SQL Warehouse used by the requested operations.

The agent requires the API key and model settings for real runs.
The offline tests below use test configuration and substituted clients.

Optional cost estimation settings:

```dotenv
DWH_INPUT_USD_PER_MILLION=
DWH_OUTPUT_USD_PER_MILLION=
```

Supply current USD prices per million standard input and output tokens
for the exact configured model. When either price is missing, the
estimated cost is `null`, not zero.

The estimate excludes cache-specific pricing, other API charges,
and Databricks compute costs. It is not a billing statement.

Never commit `.env`, API keys, credentials, or private run artifacts.

### Run an investigation

```bash
uv run python -m dwh_mcp.agent marketplace_lab.gold.fact_orders
```

This is a real run: it sends retrieved information to the Claude API
and may incur both Claude API and Databricks compute charges.

The agent can use:

- `databricks_describe_table`
- `databricks_validate_grain`
- `databricks_get_table_lineage`
- `databricks_get_column_lineage`

The final report is requested in Russian and distinguishes retrieved
evidence, validation results, unknowns, and recommendations.

### Execution controls

The current defaults are defined in `dwh_mcp/agent/config.py`:

| Setting | Default |
|---|---:|
| Model turns | 10 |
| Tool-call attempts | 8 |
| Maximum output tokens per model response | 8192 |
| MCP call timeout | 120 seconds |

The output-token setting is not a total token or monetary budget.

Execution policy checks run before MCP calls:

- Only the explicitly supplied target table is allowed.
- Only the allowed tools and expected argument names are accepted.
- Identical successful calls cannot be repeated.
- A matching call may be retried once only after a structured,
  explicitly retryable `SOURCE_UNAVAILABLE` or `RATE_LIMITED` result.
- Retries count toward the tool-call limit.
- Metadata `OBJECT_NOT_FOUND` blocks subsequent tool execution.
- Policy violations stop the run and are recorded as failures.
- No tools are executed on the last allowed model turn.

The runner marks truncated responses and exhausted model-turn limits
as incomplete rather than saving them as completed reports.

These controls apply to this agent runner. They do not replace
Databricks permissions or impose the same policy on other MCP clients.

### Run artifacts and observability

Each run creates a directory under `runs/<run_id>/`.

| File | Contents |
|---|---|
| `run.json` | Task, settings, final status, duration, metrics, latency statistics, estimated cost |
| `events.jsonl` | Model responses, tool requests/results, policy blocks, progress events |
| `tools.json` | Tool definitions available to the agent |
| `prompt.json` | System instruction used for the run |
| `report.md` | Completed report, when available |
| `partial_report.md` | Available response text when generation hits the output-token limit |

The `runs/` directory is excluded from Git.

Metrics include model responses received, tool attempts, tool errors,
retries, blocked calls, and reported input/output tokens.
Requests that fail before a model response is received are not counted
as received model responses and may have unknown token usage.

Latency summaries use nearest-rank p50/p95 and include sample counts.
They describe recorded observations within one run, not a historical
service-level benchmark. Tool latency includes failed completed attempts.

Correlation information links:

- Agent `run_id`
- Model `tool_use_id`
- MCP request ID
- Databricks SQL `statement_id`, when returned

The `_trace` field in tool results contains diagnostic correlation data.
This is correlation tracing, without a separate distributed-tracing backend.
Unity Catalog metadata reads do not produce SQL statement IDs.

Console progress reports operation start, periodic waiting, completion,
and errors. Waiting notifications are emitted approximately every
15 seconds while the event loop can run. They do not estimate a
completion percentage. An API response finishing does not imply that
the underlying tool operation succeeded.

### Redaction scope

New artifacts written through `RunLogger` mask:

- The configured Claude API key
- Recognized password, token, secret, authorization, and cookie fields
- Bearer-token patterns and email addresses

Nested JSON stored inside strings is also inspected.
Reports and partial reports apply text redaction.

This is a defined rule set, not comprehensive personal-data detection.
Historical artifacts are not rewritten. Redaction at artifact-write time
does not sanitize tool data before it is sent to Claude.
Progress messages are redacted; other console output and third-party
logs are not comprehensively covered.

### Offline validation

Run the explicitly selected offline suite:

```bash
uv run python -m unittest dwh_mcp.agent.check_execution_policy dwh_mcp.agent.check_runner dwh_mcp.agent.check_observability dwh_mcp.agent.check_redaction dwh_mcp.agent.check_run_statistics dwh_mcp.agent.check_trace_context dwh_mcp.agent.check_sql_trace dwh_mcp.agent.check_progress
```

These tests cover execution policy, runner behavior, artifacts,
redaction, latency/cost calculations, MCP correlation, SQL statement IDs,
and progress-task cleanup.

Claude and Databricks calls are substituted. MCP correlation tests
use the real local MCP transport with substituted providers or SDK clients.

Other diagnostic scripts are not necessarily offline:
`check_error_response` queries Databricks, and `test_model` calls Claude.
Avoid broad test discovery when only offline execution is intended.

### Current limitations

- Prompt instructions guide evidence interpretation but do not guarantee
  factual correctness of every generated statement.
- The runner does not programmatically verify that every selected grain
  column was obtained from metadata.
- Structured SDK error classification does not fully classify SQL errors
  converted by providers into generic runtime exceptions.
- `NotFound` indicates that the object was not found for the request;
  it does not independently rule out visibility restrictions.
- Lineage queries currently use a 90-day lookback and return at most
  50 records per call. Missing edges do not prove missing dependencies.
- Token accounting and cost estimates are limited to recorded usage.
- Run logs support diagnosis; they are not a response cache or a
  resumable execution checkpoint.

## 14. Project Background

DWH MCP Explorer was developed as a practical engineering project exploring the use of Model Context Protocol in data engineering.

Its purpose is to demonstrate how an MCP server can become an integration layer between AI-assisted investigation and existing enterprise data platforms.

The implementation combines traditional data warehouse engineering practices with modern AI tooling, with an emphasis on metadata discovery, evidence-based analysis, lineage, and validation.

---

**Project focus:** Data Engineering · Data Architecture · MCP · Python · PostgreSQL · Azure Databricks · Unity Catalog · AI Integration
