
import psycopg
from sqlglot.errors import ParseError


def classify_error(
    component: str,
    error: Exception
) -> dict:
    """Convert an exception into a structured diagnostic."""

    result = {
        "component": component,
        "error_type": type(error).__name__,
        "category": "INTERNAL_ERROR",
        "message": "Unexpected component failure",
        "retryable": False
    }

    if isinstance(error, psycopg.OperationalError):
        result.update({
            "category": "SOURCE_UNAVAILABLE",
            "message": "PostgreSQL connection failed",
            "retryable": True
        })

    elif isinstance(error, FileNotFoundError):
        result.update({
            "category": "SQL_FILE_NOT_FOUND",
            "message": "Required SQL file was not found",
            "retryable": False
        })

    elif isinstance(error, ParseError):
        result.update({
            "category": "SQL_PARSE_ERROR",
            "message": "SQL parsing failed",
            "retryable": False
        })

    elif isinstance(error, ValueError):
        result.update({
            "category": "INVALID_INPUT",
            "message": str(error),
            "retryable": False
        })

    return result
