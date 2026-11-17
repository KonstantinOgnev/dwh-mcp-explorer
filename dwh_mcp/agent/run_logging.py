import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class RunLogger:
    def __init__(self, task: str, config):
        project_root = Path(__file__).resolve().parents[2]
        run_id = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "_"
            + uuid4().hex[:8]
        )

        self.directory = project_root / "runs" / run_id
        self.directory.mkdir(parents=True, exist_ok=False)

        self.write_json("run.json", {
            "run_id": run_id,
            "task": task,
            "model": config.model,
            "max_steps": config.max_steps,
            "max_tokens": config.max_tokens,
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            **data,
        }

        with (self.directory / "events.jsonl").open(
            "a", encoding="utf-8"
        ) as stream:
            stream.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    def save_report(self, report: str):
        (self.directory / "report.md").write_text(
            report,
            encoding="utf-8",
        )

    def finish(self, status: str, **details):
        path = self.directory / "run.json"
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        data.update({
            "status": status,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            **details,
        })

        self.write_json("run.json", data)