import json
import sys
from pathlib import Path

DENY_REASON = (
    "Kit roster is immutable (DSP-4). "
    "Refusing write to vehicles.json."
)


def is_protected(name: str) -> bool:
    return Path(str(name)).name.lower() == "vehicles.json"


def paths_from(event: dict) -> list[str]:
    inp = event.get("toolInput") or {}
    out: list[str] = []
    for key in ("file_path", "path", "target_file", "old_string"):
        value = inp.get(key)
        if isinstance(value, str) and value:
            out.append(value)
    return out


def main() -> None:
    event = json.load(sys.stdin)
    for item in paths_from(event):
        if is_protected(item):
            json.dump({"decision": "deny", "reason": DENY_REASON}, sys.stdout)
            return
    json.dump({"decision": "allow"}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        json.dump(
            {"decision": "deny", "reason": f"protect_vehicles hook error: {exc}"},
            sys.stdout,
        )
