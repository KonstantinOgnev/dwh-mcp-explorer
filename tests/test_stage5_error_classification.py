
import psycopg
from sqlglot.errors import ParseError

from dwh_mcp.errors import classify_error


def main():
    cases = [
        (
            FileNotFoundError("missing.sql"),
            "SQL_FILE_NOT_FOUND",
            False
        ),
        (
            ParseError("Invalid SQL"),
            "SQL_PARSE_ERROR",
            False
        ),
        (
            psycopg.OperationalError("Connection refused"),
            "SOURCE_UNAVAILABLE",
            True
        ),
        (
            ValueError("Invalid filename"),
            "INVALID_INPUT",
            False
        ),
        (
            RuntimeError("Unexpected failure"),
            "INTERNAL_ERROR",
            False
        )
    ]

    for error, expected_category, expected_retryable in cases:
        result = classify_error("test_component", error)

        assert result["category"] == expected_category
        assert result["retryable"] is expected_retryable
        assert result["component"] == "test_component"

        print(f"PASS: {expected_category}")

    print("STAGE 5.3.3 ERROR CLASSIFICATION: PASSED")


if __name__ == "__main__":
    main()
