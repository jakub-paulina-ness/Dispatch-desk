"""Tests for S-02 (dispatch engine) and S-11 (dispatcher agent) only."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
import dispatch  # noqa: E402
import dispatcher  # noqa: E402

PY = sys.executable
FORBIDDEN_SRC = (
    "out of service",
    "hours_ok true",
    "less than vehicle range",
)
S00_EVENTS = [
    ("J-01", "T-11", "ASSIGN", ["DSP-1", "DSP-2"]),
    ("J-01", "T-12", "SKIP", ["DSP-1"]),
    ("J-01", "T-14", "REFUSE", ["DSP-3"]),
    ("J-02", "T-11", "ASSIGN", ["DSP-1", "DSP-2"]),
    ("J-02", "T-12", "SKIP", ["DSP-1"]),
    ("J-02", "T-14", "REFUSE", ["DSP-3"]),
]


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(_ROOT / "dispatch.py"), *args],
        cwd=_ROOT,
        text=True,
        capture_output=True,
    )


class S02DispatchEngine(unittest.TestCase):
    """S-02: first-fit engine, quotes from handle(), T-14 refused."""

    def test_both_jobs_assign_t11_skip_t12_refuse_t14(self) -> None:
        proc = cli()
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout
        self.assertIn("=== JOB J-01 Cluj 40 km ===", out)
        self.assertIn("=== JOB J-02 Oradea 160 km ===", out)
        for job in ("J-01", "J-02"):
            block = out.split("=== JOB ")[1 if job == "J-01" else 2]
            self.assertIn("ASSIGN vehicle=T-11", block)
            self.assertIn("SKIP vehicle=T-12", block)
            self.assertIn("REFUSE vehicle=T-14", block)
            self.assertNotIn("ASSIGN vehicle=T-12", block)
            self.assertNotIn("ASSIGN vehicle=T-14", block)

    def test_dsp3_quote_equals_lookup_rule(self) -> None:
        quote = dispatch.lookup_rule("DSP-3")
        proc = cli()
        self.assertIn("RULE DSP-3: " + quote, proc.stdout)

    def test_j01_only(self) -> None:
        proc = cli("J-01")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("=== JOB J-01 Cluj 40 km ===", proc.stdout)
        self.assertNotIn("J-02", proc.stdout)

    def test_source_has_no_rule_sentence_literals(self) -> None:
        src = (_SRC / "dispatch.py").read_text(encoding="utf-8")
        for needle in FORBIDDEN_SRC:
            self.assertNotIn(needle, src)


class S11DispatcherAgent(unittest.TestCase):
    """S-11: six events, start_driver only on ASSIGN, no locations.json."""

    def test_six_events_roster_order(self) -> None:
        dispatcher.reset_started()
        events = dispatcher.collect_events(start=False)
        self.assertEqual(len(events), 6)
        got = [(e["job_id"], e["vehicle_id"], e["kind"], e["dsp_ids"]) for e in events]
        self.assertEqual(got, S00_EVENTS)

    def test_start_driver_twice_never_t12_or_t14(self) -> None:
        dispatcher.reset_started()
        dispatcher.collect_events(start=True)
        self.assertEqual(dispatcher.STARTED, [("T-11", "J-01"), ("T-11", "J-02")])

    def test_kind_and_dsp_ids_match_s00(self) -> None:
        dispatcher.reset_started()
        events = dispatcher.collect_events(start=False)
        for event, (job_id, vehicle_id, kind, dsp_ids) in zip(events, S00_EVENTS):
            self.assertEqual(event["job_id"], job_id)
            self.assertEqual(event["vehicle_id"], vehicle_id)
            self.assertEqual(event["kind"], kind)
            self.assertEqual(event["dsp_ids"], dsp_ids)
            for dsp_id in dsp_ids:
                self.assertEqual(event["quotes"][dsp_id], dispatch.lookup_rule(dsp_id))

    def test_no_locations_json(self) -> None:
        src = (_SRC / "dispatcher.py").read_text(encoding="utf-8")
        self.assertNotIn("locations.json", src)


if __name__ == "__main__":
    unittest.main()
