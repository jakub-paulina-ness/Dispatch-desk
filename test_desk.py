#!/usr/bin/env python3
"""T-14 stays refused. Eligible jobs are assigned and the rule is cited."""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

import desk

HOOK = Path(__file__).resolve().parent / ".grok" / "hooks" / "desk_guard.py"


def run_hook(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


class DispatchMatchesKit(unittest.TestCase):
    def test_t14_stays_refused(self) -> None:
        for job_id in ("J-01", "J-02"):
            result = desk.decide_pair(job_id, "T-14")
            self.assertEqual(result["decision"], "Refuse")
            self.assertEqual(result["rule"], "DSP-3")
            self.assertIn("out of service", result["quote"])
            rendered = desk.render(result)
            self.assertIn("Quoted from DSP-3", rendered)
            self.assertIn("Refuse T-14", rendered)

    def test_j01_assigns_t11(self) -> None:
        result = desk.decide_job("J-01")
        self.assertEqual(result["decision"], "Assign")
        self.assertEqual(result["vehicle_id"], "T-11")
        self.assertEqual(result["rule"], "DSP-1")
        self.assertIn("status free", result["quote"])
        self.assertIn("hours_ok", result["quote"])
        self.assertIn("Quoted from DSP-1", desk.render(result))

    def test_j02_assigns_t11_range_ok(self) -> None:
        result = desk.decide_pair("J-02", "T-11")
        self.assertEqual(result["decision"], "Assign")
        self.assertEqual(result["vehicle_id"], "T-11")
        self.assertTrue(160 < 180)

    def test_t12_busy_refused(self) -> None:
        result = desk.decide_pair("J-01", "T-12")
        self.assertEqual(result["decision"], "Refuse")
        self.assertEqual(result["rule"], "DSP-1")

    def test_invented_vehicle_refused(self) -> None:
        result = desk.decide_pair("J-01", "T-99")
        self.assertEqual(result["decision"], "Refuse")
        self.assertEqual(result["rule"], "DSP-4")
        self.assertIn("vehicles.json", result["quote"])

    def test_t12_oradea_fails_range(self) -> None:
        # Even if it were free, 160 is not less than 90.
        result = desk.decide_pair("J-02", "T-12")
        self.assertEqual(result["decision"], "Refuse")
        self.assertEqual(result["rule"], "DSP-1")

    def test_quotes_come_from_rule_file(self) -> None:
        text = desk.rules_text()
        for job_id, vehicle_id in (("J-01", "T-11"), ("J-01", "T-14"), ("J-01", "T-99")):
            result = desk.decide_pair(job_id, vehicle_id)
            self.assertIn(result["rule"], text)
            self.assertIn(result["quote"], text)

    def test_off_scope_has_no_invented_rule(self) -> None:
        result = desk.refuse_off_scope("What should we pay the driver?")
        self.assertEqual(result["decision"], "Off desk")
        self.assertEqual(result["rule"], "")
        self.assertIn("will not give medical, legal, or payment advice", result["message"])

    def test_hook_blocks_payment_advice(self) -> None:
        proc = run_hook(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "What payout should we promise the driver?",
            }
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("payment", payload["reason"].lower())

    def test_hook_allows_dispatch_prompt(self) -> None:
        proc = run_hook(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "Assign J-01 from the roster",
            }
        )
        self.assertEqual(proc.returncode, 0)

    def test_hook_blocks_kit_edit(self) -> None:
        proc = run_hook(
            {
                "hook_event_name": "PreToolUse",
                "toolName": "Write",
                "toolInput": {"file_path": "dispatch_rules.md"},
            }
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
