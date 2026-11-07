
from pathlib import Path


# SQL files are stored in the project root/sql_sources.
# This module is located in project root/dwh_mcp.
SQL_SOURCE_DIR = (
    Path(__file__).resolve().parent.parent / "sql_sources"
)


def list_sql_files() -> dict:
    """List SQL transformation files available for DWH discovery."""

    files = sorted(
        path.name
        for path in SQL_SOURCE_DIR.glob("*.sql")
        if path.is_file()
    )

    return {
        "source_type": "local_sql",
        "files": files,
        "file_count": len(files)
    }


def read_sql_file(filename: str) -> dict:
    """Read a SQL transformation file from the approved directory."""

    if not filename.endswith(".sql"):
        raise ValueError("Only .sql files are allowed")

    if Path(filename).name != filename:
        raise ValueError("Invalid filename")

    file_path = (SQL_SOURCE_DIR / filename).resolve()
    source_dir = SQL_SOURCE_DIR.resolve()

    if not file_path.is_relative_to(source_dir):
        raise ValueError(
            "Access outside sql_sources is forbidden"
        )

    if not file_path.is_file():
        raise FileNotFoundError(
            f"SQL file not found: {filename}"
        )

    sql_content = file_path.read_text(encoding="utf-8")

    return {
        "source_type": "local_sql",
        "filename": filename,
        "content": sql_content,
        "line_count": len(sql_content.splitlines())
    }
