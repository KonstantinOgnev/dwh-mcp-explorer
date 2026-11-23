import asyncio
import json

from anthropic import AsyncAnthropic
from mcp import Client
from time import perf_counter

from server import mcp
from dwh_mcp.agent.config import load_agent_config
from dwh_mcp.agent.mcp_client import get_agent_tools, ALLOWED_TOOLS
from dwh_mcp.agent.prompts import SYSTEM_PROMPT
from dwh_mcp.agent.run_logging import RunLogger
from dwh_mcp.agent.compact_results import compact_tool_content
from dwh_mcp.agent.execution_policy import (
ExecutionPolicy,
ExecutionPolicyError,
)
from dwh_mcp.agent.progress import operation_progress, notify


async def _run_agent(
    task: str,
    config,
    log: RunLogger,
    policy: ExecutionPolicy,
) -> str:
    messages = [{"role": "user", "content": task}]
    total_input = 0
    total_output = 0
    call_attempts = {}

    async with (
        AsyncAnthropic(
            api_key=config.api_key,
            max_retries=0,
            timeout=120.0,
        ) as model,
        Client(mcp, raise_exceptions=True) as tools_client,
    ):
        tools = await get_agent_tools(tools_client)
        log.write_json("tools.json", tools)
        log.write_json("prompt.json", {"system": SYSTEM_PROMPT})

        for step in range(1, config.max_steps + 1):
            print(f"\n[Step {step}] Calling Claude...", flush=True)

            model_started = perf_counter()

            async with operation_progress(
                log,
                "Claude request",
                operation_id=f"model-{step}",
            ):
                response = await model.messages.create(
                    model=config.model,
                    system=SYSTEM_PROMPT,
                    max_tokens=config.max_tokens,
                    tools=tools,
                    messages=messages,
                )

            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens
            log.event(
                "model_response",
                step=step,
                status="completed",
                duration_ms=round(
                    (perf_counter() - model_started) * 1000, 3
                ),
                response=response.model_dump(
                    mode="json", exclude_none=True
                ),
                total_input_tokens=total_input,
                total_output_tokens=total_output,
            )

            # Preserve every response block, including thinking blocks.
            messages.append({
                "role": "assistant",
                "content": [
                    block.model_dump(mode="json", exclude_none=True)
                    for block in response.content
                ],
            })

            print(
                f"[Usage] input={total_input}, "
                f"output={total_output}",
                flush=True,
            )

            if response.stop_reason == "end_turn":
                return "\n".join(
                    block.text
                    for block in response.content
                    if block.type == "text"
                )

            if response.stop_reason == "max_tokens":
                partial_report = "\n".join(
                    block.text
                    for block in response.content
                    if block.type == "text"
                )

                (log.directory / "partial_report.md").write_text(
                    log.redactor.text(partial_report),
                    encoding="utf-8",
                )

            if response.stop_reason != "tool_use":
                raise RuntimeError(
                    "Investigation stopped without a completed report: "
                    f"{response.stop_reason}"
                )

            # Do not execute more tools if no model turn remains
            # to interpret their results.
            if step == config.max_steps:
                break

            results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                print(
                    f"[Tool] {block.name}: "
                    f"{json.dumps(block.input, ensure_ascii=False)}",
                    flush=True,
                )

                log.event(
                    "tool_call",
                    step=step,
                    tool=block.name,
                    arguments=block.input,
                )

                try:
                    policy.before_call(block.name, block.input)
                except ExecutionPolicyError as error:
                    log.event(
                        "tool_call_blocked",
                        step=step,
                        tool=block.name,
                        tool_use_id=block.id,
                        reason=str(error),
                        tool_calls=policy.tool_calls,
                    )
                    raise
                call_key = json.dumps(
                    [block.name, block.input],
                    sort_keys=True,
                    ensure_ascii=False,
                )
                attempt = call_attempts.get(call_key, 0) + 1
                call_attempts[call_key] = attempt

                log.event(
                    "tool_started",
                    step=step,
                    tool=block.name,
                    tool_use_id=block.id,
                    attempt=attempt,
                    is_retry=attempt > 1,
                    status="started",
                )

                tool_started = perf_counter()
                error_code = None
                payload = None

                try:
                    async with operation_progress(
                        log,
                        block.name,
                        operation_id=block.id,
                    ):
                        result = await asyncio.wait_for(
                            tools_client.call_tool(
                                block.name,
                                block.input,
                                meta={
                                    "dwh_trace": {
                                        "run_id": log.run_id,
                                        "tool_use_id": block.id,
                                    },
                                },
                            ),
                            timeout=120.0,
                        )

                    payload = result.structured_content

                    if payload is None:
                        for item in result.content:
                            if item.type == "text":
                                try:
                                    payload = json.loads(item.text)
                                except json.JSONDecodeError:
                                    pass
                                break

                    operation_failed = (
                        isinstance(payload, dict)
                        and payload.get("status") == "failed"
                    )

                    is_error = bool(result.is_error) or operation_failed
                    if is_error:
                        diagnostic = (
                            payload.get("error")
                            if isinstance(payload, dict)
                            else None
                        )
                        error_code = (
                            diagnostic.get("category")
                            if isinstance(diagnostic, dict)
                            else None
                        )
                        error_code = error_code or "MCP_TOOL_ERROR"
                    content = json.dumps(
                        result.model_dump(
                            mode="json",
                            exclude_none=True,
                        ),
                        ensure_ascii=False,
                    )

                except Exception as error:
                    is_error = True
                    error_code = (
                        "TOOL_TIMEOUT"
                        if isinstance(error, TimeoutError)
                        else "TOOL_EXECUTION_ERROR"
                    )
                    content = json.dumps({
                        "error_type": type(error).__name__,
                        "message": "Tool execution failed; "
                                   "no evidence was obtained.",
                    })

                notify(
                    log,
                    block.name,
                    "tool_failed" if is_error else "tool_succeeded",
                    operation_id=block.id,
                )

                policy.after_call(
                    block.name,
                    block.input,
                    is_error=is_error,
                    payload=payload,
                )

                log.event(
                    "tool_result",
                    step=step,
                    tool=block.name,
                    tool_use_id=block.id,
                    is_error=is_error,
                    content=content,
                    status="failed" if is_error else "completed",
                    error_code=error_code,
                    duration_ms=round(
                        (perf_counter() - tool_started) * 1000, 3
                    ),
                    attempt=attempt,
                )

                model_content = compact_tool_content(
                    block.name,
                    content,
                )

                log.event(
                    "model_tool_result",
                    step=step,
                    tool=block.name,
                    tool_use_id=block.id,
                    content=model_content,
                    original_characters=len(content),
                    model_characters=len(model_content),
                )

                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": model_content,
                    "is_error": is_error,
                })

            if not results:
                raise RuntimeError(
                    "Claude requested tool use but supplied no tool calls"
                )

            messages.append({
                "role": "user",
                "content": results,
            })

    raise RuntimeError(
        f"Reached the limit of {config.max_steps} model calls. "
        "The investigation is incomplete."
    )

async def run_agent(task: str, *, target_table: str) -> str:
    config = load_agent_config()
    policy = ExecutionPolicy(
        target_table=target_table,
        allowed_tools=ALLOWED_TOOLS,
        max_tool_calls=config.max_tool_calls,
    )
    log = RunLogger(task, config)

    log.event(
        "execution_policy",
        target_table=target_table,
        max_tool_calls=config.max_tool_calls,
    )

    print(f"[Run directory] {log.directory}", flush=True)

    try:
        report = await _run_agent(task, config, log, policy)
        log.save_report(report)
        log.finish("completed")
        notify(
            log,
            "Investigation",
            "completed",
            operation_id="run",
        )
        return report

    except BaseException as error:
        status = (
            "interrupted"
            if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError))
            else "failed"
        )

        log.finish(
            status,
            error_type=type(error).__name__,
        )
        notify(
            log,
            "Investigation",
            status,
            operation_id="run",
        )
        raise