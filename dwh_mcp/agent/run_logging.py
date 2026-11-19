import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4


class RunLogger:
    def __init__(self, task: str, config, *, output_root=None):
        project_root = Path(__file__).resolve().parents[2]
        root = (
            Path(output_root)
            if output_root is not None
            else project_root / "runs"
        )

        self.run_id = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "_"
            + uuid4().hex[:8]
        )
        self._started = perf_counter()

        self.metrics = {
            "model_calls": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "tool_retries": 0,
            "blocked_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
        }

        self.directory = root / self.run_id
        self.directory.mkdir(parents=True, exist_ok=False)

        self.write_json("run.json", {
            "run_id": self.run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "task": task,
            "model": config.model,
            "max_steps": config.max_steps,
            "max_tokens": config.max_tokens,
            "max_tool_calls": config.max_tool_calls,
            "status": "started",
        })

    def write_json(self, filename: str, data):
        path = self.directory / filename
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def event(self, event_type: str, **data):
        record = {
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "type": event_type,
        }

        with (self.directory / "events.jsonl").open(
            "a", encoding="utf-8"
        ) as stream:
            stream.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

        # Update counters after the event has been written.
        if event_type == "model_response":
            self.metrics["model_calls"] += 1
            self.metrics["input_tokens"] = data["total_input_tokens"]
            self.metrics["output_tokens"] = data["total_output_tokens"]

        elif event_type == "tool_started":
            self.metrics["tool_calls"] += 1
            if data.get("is_retry") is True:
                self.metrics["tool_retries"] += 1

        elif event_type == "tool_result":
            if data.get("is_error") is True:
                self.metrics["tool_errors"] += 1

        elif event_type == "tool_call_blocked":
            self.metrics["blocked_calls"] += 1

    def save_report(self, report: str):
        (self.directory / "report.md").write_text(
            report,
            encoding="utf-8",
        )

    def finish(self, status: str, **details):
        path = self.directory / "run.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        data.update(details)
        data.update({
            "status": status,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(
                (perf_counter() - self._started) * 1000, 3
            ),
            "metrics": dict(self.metrics),
        })

        self.write_json("run.json", data)