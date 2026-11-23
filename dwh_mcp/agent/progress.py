import asyncio
from contextlib import asynccontextmanager, suppress
from time import perf_counter


def notify(log, operation, status, *, operation_id, elapsed_seconds=0):
    record = {
        "operation": operation,
        "operation_id": operation_id,
        "status": status,
        "elapsed_seconds": round(elapsed_seconds, 1),
    }
    log.event("progress", **record)

    message = (
        f"[Progress] {operation}: {status} "
        f"({record['elapsed_seconds']:.1f}s)"
    )
    print(log.redactor.text(message), flush=True)


@asynccontextmanager
async def operation_progress(
    log,
    operation,
    *,
    operation_id,
    interval=15.0,
):
    if interval <= 0:
        raise ValueError("Progress interval must be positive")

    started = perf_counter()

    def emit(status):
        notify(
            log,
            operation,
            status,
            operation_id=operation_id,
            elapsed_seconds=perf_counter() - started,
        )

    async def heartbeat():
        while True:
            await asyncio.sleep(interval)
            emit("waiting")

    emit("started")
    task = asyncio.create_task(heartbeat())
    outcome = "finished"

    try:
        yield
    except asyncio.CancelledError:
        outcome = "interrupted"
        raise
    except BaseException:
        outcome = "failed"
        raise
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        emit(outcome)