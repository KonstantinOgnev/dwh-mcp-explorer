import psycopg
from sqlglot.errors import ParseError
from databricks.sdk import errors as dbx_errors

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

def classify_databricks_error(
    component: str,
    error: Exception,
) -> dict:
    """Convert Databricks exceptions into safe diagnostics."""

    result = {
        "component": component,
        "error_type": type(error).__name__,
        "category": "INTERNAL_ERROR",
        "message": "Unexpected Databricks operation failure",
        "retryable": False,
    }

    if isinstance(error, dbx_errors.NotFound):
        result.update({
            "category": "OBJECT_NOT_FOUND",
            "message": "The requested Databricks object was not found",
        })

    elif isinstance(error, dbx_errors.PermissionDenied):
        result.update({
            "category": "ACCESS_DENIED",
            "message": "Access to the Databricks operation was denied",
        })

    elif isinstance(error, dbx_errors.Unauthenticated):
        result.update({
            "category": "AUTHENTICATION_FAILED",
            "message": "Databricks authentication failed",
        })

    elif isinstance(
        error,
        (dbx_errors.TooManyRequests, dbx_errors.RequestLimitExceeded),
    ):
        result.update({
            "category": "RATE_LIMITED",
            "message": "Databricks request limit was exceeded",
            "retryable": True,
        })

    elif isinstance(
        error,
        (dbx_errors.TemporarilyUnavailable, dbx_errors.OperationTimeout),
    ):
        result.update({
            "category": "SOURCE_UNAVAILABLE",
            "message": "Databricks is temporarily unavailable or timed out",
            "retryable": True,
        })

    return result