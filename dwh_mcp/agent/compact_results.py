import json


IMPORTANT_PROPERTIES = {
    "fact_grain",
    "quality",
    "delta.enableChangeDataFeed",
    "delta.enableDeletionVectors",
    "delta.enableRowTracking",
    "delta.appendOnly",
}


def compact_tool_content(tool_name: str, content: str) -> str:
    """Build model-facing content from a full MCP result."""
    envelope = json.loads(content)

    # Do not simplify error responses.
    if envelope.get("is_error"):
        return content

    payload = envelope.get("structured_content")

    if payload is None:
        blocks = envelope.get("content", [])

        # Preserve unfamiliar result formats unchanged.
        if len(blocks) != 1 or blocks[0].get("type") != "text":
            return content

        try:
            payload = json.loads(blocks[0]["text"])
        except (json.JSONDecodeError, KeyError):
            return content

    if tool_name != "databricks_describe_table":
        return json.dumps(payload, ensure_ascii=False)

    if not isinstance(payload, dict) or "columns" not in payload:
        return content

    properties = payload.get("properties", {})

    if not isinstance(properties, dict):
        return content

    compact = {
        key: payload[key]
        for key in (
            "full_name",
            "table_type",
            "data_source_format",
            "comment",
            "columns",
        )
        if key in payload
    }

    compact["properties"] = {
        key: value
        for key, value in properties.items()
        if key in IMPORTANT_PROPERTIES
    }

    compact["representation"] = {
        "compacted": True,
        "omitted_property_count": (
            len(properties) - len(compact["properties"])
        ),
        "limitations": [
            "Statistics and other unselected properties are omitted.",
            "Missing properties do not prove a feature is disabled.",
            "Full tool response is retained in the local run log.",
        ],
    }

    return json.dumps(compact, ensure_ascii=False)