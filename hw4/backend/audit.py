"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

One entry per chat turn: when it ran, every tool call with short args/result, retries,
the stop reason, and token usage. Entries are only ever appended, never edited or
wiped between runs. The file stays a valid JSON array so it opens in any JSON viewer.

Privacy: no emails, names or passwords are logged. Shoppers are "guest" or
"logged_in", the message is the guard-redacted text, and long values are truncated.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_CHARS = 200  # "short" args/results
_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _short(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS] + f"… (+{len(text) - MAX_CHARS} chars)"


def _ts(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds") if dt else None


def steps_from(messages: list[ModelMessage]) -> list[dict]:
    """Turn this run's PydanticAI messages into a readable step list."""
    steps: list[dict] = []
    for msg in messages:
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    steps.append({
                        "time": _ts(msg.timestamp),
                        "type": "tool_call",
                        "tool": part.tool_name,
                        "args": _short(part.args),
                    })
            if msg.finish_reason:
                steps.append({"time": _ts(msg.timestamp), "type": "model_response", "finish_reason": msg.finish_reason})
        elif isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    steps.append({
                        "time": _ts(part.timestamp),
                        "type": "tool_result",
                        "tool": part.tool_name,
                        "result": _short(part.content),
                    })
                elif isinstance(part, RetryPromptPart):
                    steps.append({
                        "time": _ts(part.timestamp),
                        "type": "retry",
                        "tool": part.tool_name,
                        "reason": _short(part.content),
                    })
    return steps


def record(entry: dict) -> None:
    """Append one entry. Never truncates the file; a damaged file is set aside, not deleted."""
    entry = {"run_id": uuid.uuid4().hex[:12], **entry}
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_PATH.exists():
            try:
                entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
                if not isinstance(entries, list):
                    raise ValueError("audit trail is not a JSON array")
            except ValueError:
                AUDIT_PATH.rename(AUDIT_PATH.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.json"))
                entries = []
        entries.append(entry)
        tmp = AUDIT_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, AUDIT_PATH)  # atomic: readers never see a half-written file
