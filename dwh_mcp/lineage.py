
from sqlglot import parse_one, exp

from dwh_mcp import sql_repository as sql_repo


def get_table_lineage(filename: str) -> dict:
    """Extract table-level and column-level SQL lineage."""

    sql_data = sql_repo.read_sql_file(filename)
    sql_content = sql_data["content"]

    tree = parse_one(sql_content, read="postgres")

    if not isinstance(tree, exp.Insert):
        raise ValueError("Only INSERT statements are supported")

    # INSERT target may include a column list.
    target_node = tree.this
    if isinstance(target_node, exp.Schema):
        target_node = target_node.this

    if not isinstance(target_node, exp.Table):
        raise ValueError("Cannot identify target table")

    target_table = target_node.sql(dialect="postgres")

    # Extract source tables, excluding INSERT target.
    sources = []

    for table_node in tree.find_all(exp.Table):
        if table_node is target_node:
            continue

        sources.append({
            "table": ".".join(
                part for part in (table_node.db, table_node.name)
                if part
            ),
            "alias": table_node.alias_or_name
        })

    # Extract JOIN conditions.
    joins = []

    for join_node in tree.find_all(exp.Join):
        condition = join_node.args.get("on")

        joins.append({
            "table": join_node.this.sql(dialect="postgres"),
            "condition": (
                condition.sql(dialect="postgres")
                if condition is not None else None
            )
        })

    # Extract column-level mapping.
    column_mapping = []

    target_schema = tree.this
    target_columns = []

    if isinstance(target_schema, exp.Schema):
        target_columns = [
            col.name
            for col in target_schema.expressions
        ]

    select_node = tree.expression

    if isinstance(select_node, exp.Select):
        select_expressions = select_node.expressions

        if len(target_columns) != len(select_expressions):
            raise ValueError(
                "Target and source column counts do not match"
            )

        for target_col, source_expr in zip(
            target_columns, select_expressions
        ):
            column_mapping.append({
                "target_column": target_col,
                "source_expression": source_expr.sql(
                    dialect="postgres"
                ),
                "source_columns": [
                    col.sql(dialect="postgres")
                    for col in source_expr.find_all(exp.Column)
                ]
            })

    return {
        "column_mapping": column_mapping,
        "target_table": target_table,
        "source_tables": sources,
        "joins": joins,
        "source_file": filename,
        "source_type": "local_sql",
        "lineage_level": "table_and_column",
        "status": "parsed"
    }
