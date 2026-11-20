from time import perf_counter

from dwh_mcp.errors import classify_databricks_error


def traced_databricks_call(
    ctx,
    full_name,
    operation,
    *,
    operation_name="databricks.tables.get",
    component="databricks_metadata",
    ):
    metadata = ctx.request_context.meta or {}
    supplied = metadata.get("dwh_trace", {})
    if not isinstance(supplied, dict):
        supplied = {}

    # Correlation labels only; never use them for authorization or paths.
    trace = {
        "mcp_request_id": str(ctx.request_context.request_id),
        "operation": operation_name,
    }
    for name in ("run_id", "tool_use_id"):
        value = supplied.get(name)
        if isinstance(value, str) and 0 < len(value) <= 128:
            trace[name] = value

    started = perf_counter()
    try:
        payload = dict(operation(trace))
        trace["status"] = "completed"
        trace["error_code"] = None
    except Exception as error:
        diagnostic = classify_databricks_error(
            component, error
        )
        payload = {
            "status": "failed",
            "full_name": full_name,
            "error": diagnostic,
        }
        trace["status"] = "failed"
        trace["error_code"] = diagnostic["category"]

    trace["duration_ms"] = round(
        (perf_counter() - started) * 1000, 3
    )
    payload["_trace"] = trace
    return payload