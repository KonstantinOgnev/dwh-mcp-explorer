import asyncio
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from dwh_mcp.agent import progress
from dwh_mcp.agent.redaction import Redactor


class ProgressTests(unittest.IsolatedAsyncioTestCase):
    def make_log(self):
        log = MagicMock()
        log.redactor = Redactor(secrets=("test-secret-123",))
        return log

    def statuses(self, log):
        return [
            call.kwargs["status"]
            for call in log.event.call_args_list
            if call.args[0] == "progress"
        ]

    async def test_success(self):
        log = self.make_log()
        with redirect_stdout(io.StringIO()):
            async with progress.operation_progress(
                log, "Test", operation_id="call-1"
            ):
                pass

        self.assertEqual(self.statuses(log), ["started", "finished"])

    async def test_exception(self):
        log = self.make_log()
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                async with progress.operation_progress(
                    log, "Test", operation_id="call-1"
                ):
                    raise ValueError("Simulated failure")

        self.assertEqual(self.statuses(log), ["started", "failed"])

    async def test_waiting_stops_after_completion(self):
        log = self.make_log()
        waiting_seen = asyncio.Event()
        heartbeat_stopped = asyncio.Event()
        sleep_calls = []
        real_sleep = asyncio.sleep

        def record_event(event_type, **data):
            if data.get("status") == "waiting":
                waiting_seen.set()

        log.event.side_effect = record_event

        async def controlled_sleep(delay):
            sleep_calls.append(delay)
            if len(sleep_calls) == 1:
                return
            try:
                await asyncio.Event().wait()
            finally:
                heartbeat_stopped.set()

        with (
            redirect_stdout(io.StringIO()),
            patch.object(
                progress.asyncio, "sleep",
                side_effect=controlled_sleep,
            ),
        ):
            async with progress.operation_progress(
                log, "Test", operation_id="call-1", interval=15
            ):
                await asyncio.wait_for(waiting_seen.wait(), timeout=1)

        self.assertTrue(heartbeat_stopped.is_set())
        self.assertEqual(
            self.statuses(log), ["started", "waiting", "finished"]
        )
        self.assertTrue(all(delay == 15 for delay in sleep_calls))

        event_count = log.event.call_count
        await real_sleep(0)
        self.assertEqual(log.event.call_count, event_count)

    async def test_cancellation(self):
        log = self.make_log()
        entered = asyncio.Event()

        async def operation():
            async with progress.operation_progress(
                log, "Test", operation_id="call-1"
            ):
                entered.set()
                await asyncio.Event().wait()

        with redirect_stdout(io.StringIO()):
            task = asyncio.create_task(operation())
            await asyncio.wait_for(entered.wait(), timeout=1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        self.assertEqual(
            self.statuses(log), ["started", "interrupted"]
        )

    async def test_console_masks_secret(self):
        log = self.make_log()
        output = io.StringIO()
        with redirect_stdout(output):
            progress.notify(
                log,
                "Operation test-secret-123",
                "started",
                operation_id="call-1",
            )

        self.assertNotIn("test-secret-123", output.getvalue())
        self.assertIn("[REDACTED]", output.getvalue())
        self.assertEqual(
            log.event.call_args.kwargs["operation_id"], "call-1"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)