"""S-11: six events, driver only on ASSIGN T-11."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import dispatcher  # noqa: E402
from dispatch import lookup_rule  # noqa: E402

FIXTURE = ROOT / "pipelines" / "fixtures" / "dispatch_events.json"


class DispatcherLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.played: list[tuple[str, str]] = []

        def play(event):
            cls.played.append((event["vehicle_id"], event["job_id"]))
            return []

        cls.result = dispatcher.run(play=play)
        cls.events = cls.result["events"]

    def test_six_events_roster_order(self) -> None:
        self.assertEqual(len(self.events), 6)
        self.assertEqual(
            [(e["job_id"], e["vehicle_id"], e["kind"]) for e in self.events],
            [
                ("J-01", "T-11", "ASSIGN"),
                ("J-01", "T-12", "SKIP"),
                ("J-01", "T-14", "REFUSE"),
                ("J-02", "T-11", "ASSIGN"),
                ("J-02", "T-12", "SKIP"),
                ("J-02", "T-14", "REFUSE"),
            ],
        )

    def test_dsp_ids_match_s00(self) -> None:
        by_key = {(e["job_id"], e["vehicle_id"]): e for e in self.events}
        self.assertEqual(by_key[("J-01", "T-11")]["dsp_ids"], ["DSP-1", "DSP-2"])
        self.assertEqual(by_key[("J-02", "T-11")]["dsp_ids"], ["DSP-1", "DSP-2"])
        self.assertEqual(by_key[("J-01", "T-12")]["dsp_ids"], ["DSP-1"])
        self.assertEqual(by_key[("J-02", "T-12")]["dsp_ids"], ["DSP-1"])
        self.assertEqual(by_key[("J-01", "T-14")]["dsp_ids"], ["DSP-3"])
        self.assertEqual(by_key[("J-02", "T-14")]["dsp_ids"], ["DSP-3"])

    def test_quotes_from_lookup_rule(self) -> None:
        for event in self.events:
            for dsp in event["dsp_ids"]:
                self.assertEqual(event["quotes"][dsp], lookup_rule(dsp))

    def test_start_driver_twice_only_assign(self) -> None:
        self.assertEqual(
            self.result["drivers_started"],
            [
                {"vehicle_id": "T-11", "job_id": "J-01"},
                {"vehicle_id": "T-11", "job_id": "J-02"},
            ],
        )
        self.assertEqual(self.played, [("T-11", "J-01"), ("T-11", "J-02")])

    def test_start_driver_skips_non_assign(self) -> None:
        refuse = {
            "job_id": "J-01",
            "city": "Cluj",
            "km": 40,
            "vehicle_id": "T-14",
            "kind": "REFUSE",
            "dsp_ids": ["DSP-3"],
        }
        skip = dict(refuse, vehicle_id="T-12", kind="SKIP", dsp_ids=["DSP-1"])
        self.assertEqual(dispatcher.start_driver(refuse, play=lambda e: ["tick"]), [])
        self.assertEqual(dispatcher.start_driver(skip, play=lambda e: ["tick"]), [])

    def test_fixture_kinds_stay_in_sync(self) -> None:
        seeded = json.loads(FIXTURE.read_text(encoding="utf-8"))["events"]
        self.assertEqual(
            [(e["job_id"], e["vehicle_id"], e["kind"], e["dsp_ids"]) for e in seeded],
            [(e["job_id"], e["vehicle_id"], e["kind"], e["dsp_ids"]) for e in self.events],
        )

    def test_no_locations_for_eligibility(self) -> None:
        src = (SRC / "dispatcher.py").read_text(encoding="utf-8")
        self.assertNotIn("locations.json", src)
        self.assertNotIn("hours_ok", src)
        self.assertNotIn("range_km", src)
        self.assertNotIn("evaluate_vehicle", src)

    def test_does_not_reimplement_dsp(self) -> None:
        src = (SRC / "dispatcher.py").read_text(encoding="utf-8")
        self.assertIn("dispatch_job", src)
        self.assertNotIn("status == \"red\"", src)

    def test_events_only_does_not_drive(self) -> None:
        with patch.object(dispatcher, "start_driver") as started:
            with patch.object(dispatcher.sys, "stdout"):
                code = dispatcher.main(["--events-only"])
        self.assertEqual(code, 0)
        started.assert_not_called()


if __name__ == "__main__":
    unittest.main()
