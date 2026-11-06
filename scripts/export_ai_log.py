#!/usr/bin/env python3
"""Export this project's visible conversation and tool exchanges from a local session."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("session", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
records = []
models = set()
for line in args.session.read_text().splitlines():
    record = json.loads(line)
    payload = record.get("payload", {})
    if record.get("type") == "turn_context":
        if payload.get("model"):
            models.add(payload["model"])
        continue
    if record.get("type") != "response_item":
        continue
    kind = payload.get("type")
    entry = {"timestamp": record.get("timestamp"), "type": kind}
    if kind == "message" and payload.get("role") in ("user", "assistant"):
        if payload.get("channel") == "analysis":
            continue
        entry.update(role=payload["role"], phase=payload.get("phase"), content=payload.get("content", []))
    elif kind in ("custom_tool_call", "custom_tool_call_output", "function_call", "function_call_output"):
        entry.update({key: payload[key] for key in ("call_id", "name", "input", "arguments", "output") if key in payload})
    else:
        continue
    records.append(entry)
out = root / "ai"
out.mkdir(exist_ok=True)
with (out / "visible-session.jsonl").open("w") as handle:
    for record in records:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
metadata = {
    "models_observed": sorted(models),
    "interface": "Codex desktop app, local tools",
    "exported_records": len(records),
    "scope": "Visible user/assistant messages and tool exchanges. Excludes private reasoning and system/developer instructions.",
    "refresh": "Run this exporter again before submission to include later work and the final response.",
}
(out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print("Exported", len(records), "visible records; observed models:", ", ".join(sorted(models)))
