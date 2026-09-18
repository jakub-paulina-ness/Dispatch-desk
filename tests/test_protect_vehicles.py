"""T-HOOK-FIXTURE: PreToolUse stdin → deny writes to vehicles.json; allow Get-Content."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = (
    ROOT / ".grok" / "hooks" / "protect_vehicles.py",
    ROOT / ".grok" / "plugins" / "dispatch-desk" / "hooks" / "protect_vehicles.py",
)
JSON_FILES = (
    ROOT / ".grok" / "hooks" / "protect-vehicles.json",
)


def run_hook(script: Path, event: dict | str) -> dict:
    payload = event if isinstance(event, str) else json.dumps(event)
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"{script} exit {proc.returncode} stderr={proc.stderr!r} stdout={proc.stdout!r}"
        )
    return json.loads(proc.stdout)


class ProtectVehiclesFixture(unittest.TestCase):
    def test_scripts_exist(self) -> None:
        for path in (*SCRIPTS, *JSON_FILES):
            self.assertTrue(path.is_file(), path)

    def test_search_replace_vehicles_denied(self) -> None:
        event = {
            "toolName": "search_replace",
            "toolInput": {"file_path": "instructions/vehicles.json"},
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "deny", script)
            self.assertIn("vehicles.json", out["reason"])

    def test_write_vehicles_denied(self) -> None:
        event = {
            "toolName": "write",
            "toolInput": {"file_path": r"C:\kit\Vehicles.json"},
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "deny", script)

    def test_old_string_path_denied(self) -> None:
        event = {
            "toolName": "search_replace",
            "toolInput": {
                "file_path": "src/dispatch.py",
                "old_string": "instructions/vehicles.json",
            },
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "deny", script)

    def test_get_content_command_allowed(self) -> None:
        event = {
            "toolName": "run_terminal_command",
            "toolInput": {"command": "Get-Content instructions/vehicles.json"},
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "allow", script)

    def test_rules_write_allowed(self) -> None:
        event = {
            "toolName": "write",
            "toolInput": {"file_path": "instructions/dispatch_rules.md"},
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "allow", script)

    def test_jobs_write_not_this_hook(self) -> None:
        event = {
            "toolName": "write",
            "toolInput": {"file_path": "instructions/jobs.json"},
        }
        for script in SCRIPTS:
            out = run_hook(script, event)
            self.assertEqual(out["decision"], "allow", script)

    def test_malformed_stdin_denied(self) -> None:
        for script in SCRIPTS:
            out = run_hook(script, "{not-json")
            self.assertEqual(out["decision"], "deny", script)
            self.assertIn("protect_vehicles hook error", out["reason"])


if __name__ == "__main__":
    unittest.main()
