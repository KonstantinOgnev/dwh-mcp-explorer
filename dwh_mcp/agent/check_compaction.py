import json
from pathlib import Path

from dwh_mcp.agent.compact_results import compact_tool_content


def main():
    directory = Path("runs/20261117T162422Z_26e0c3d0")
    events = [
        json.loads(line)
        for line in (directory / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    for event in events:
        if event["type"] != "tool_result":
            continue

        original = event["content"]
        compact = compact_tool_content(event["tool"], original)

        # Confirm that compact content remains valid JSON.
        payload = json.loads(compact)

        if event["tool"] == "databricks_describe_table":
            envelope = json.loads(original)
            source = envelope.get("structured_content")
            if source is None:
                source = json.loads(envelope["content"][0]["text"])

            assert payload["columns"] == source["columns"]
            assert payload["comment"] == source["comment"]
            assert (
                payload["properties"]["fact_grain"]
                == source["properties"]["fact_grain"]
            )

        reduction = 100 * (1 - len(compact) / len(original))

        print(event["tool"])
        print(f"  Original: {len(original):,} characters")
        print(f"  Compact:  {len(compact):,} characters")
        print(f"  Reduction: {reduction:.1f}%")

    print("\nCompaction checks passed")


if __name__ == "__main__":
    main()