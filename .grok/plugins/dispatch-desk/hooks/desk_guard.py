#!/usr/bin/env python3
"""Pre-check: refuse off-scope advice; do not let Grok edit kit data/rules."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROTECTED = {
    "dispatch_rules.md",
    "vehicles.json",
    "jobs.json",
    "rules_mcp.py",
}

WRITE_TOOLS = {
    "search_replace",
    "write",
    "Write",
    "Edit",
    "MultiEdit",
}

OFF_SCOPE = re.compile(
    r"\b("
    r"payout|settlement|we will pay|how much (do we|to) pay|"
    r"prescribe|prescription|dosage|\bdose\b|"
    r"medical advice|legal advice|"
    r"what (medicine|medication|drug)s?"
    r")\b",
    re.I,
)

REFUSAL = (
    "The desk only assigns jobs from the roster. "
    "It will not give medical, legal, or payment advice."
)


def payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def event_name(data: dict) -> str:
    return str(
        data.get("hook_event_name")
        or data.get("hookEventName")
        or ""
    )


def prompt_text(data: dict) -> str:
    for key in ("prompt", "userPrompt", "text"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def target_path(data: dict) -> str:
    inp = data.get("toolInput") or data.get("tool_input") or {}
    if not isinstance(inp, dict):
        return ""
    for key in ("file_path", "path", "target_file"):
        value = inp.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def emit(obj: dict, code: int) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    raise SystemExit(code)


def main() -> None:
    data = payload()
    event = event_name(data)

    if event in {"UserPromptSubmit", "user_prompt_submit"}:
        if OFF_SCOPE.search(prompt_text(data)):
            emit({"decision": "block", "reason": REFUSAL}, 2)
        raise SystemExit(0)

    tool = str(data.get("toolName") or data.get("tool_name") or "")
    name = Path(target_path(data)).name
    if name in PROTECTED and tool in WRITE_TOOLS:
        emit(
            {
                "decision": "deny",
                "reason": (
                    f"Kit file {name} is data and rules only. "
                    "Do not edit it. Made-up rules fail the lab."
                ),
            },
            2,
        )
    emit({"decision": "allow"}, 0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail open
        sys.stderr.write(f"desk_guard: {exc}\n")
        raise SystemExit(0)
