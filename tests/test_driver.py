"""S-12: T-11 telemetry after ASSIGN. No charge on J-01. CS-2 150 kW on J-02."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sim.driver import (  # noqa: E402
    TELEMETRY_KEYS,
    iter_telemetry,
    load_dispatch_events,
    play_job,
)

STATUSES = {
    "en_route",
    "junction_stop",
    "divert_charge",
    "charging",
    "delivered",
    "returning",
}


class DriverPlayback(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.events = load_dispatch_events()
        cls.ticks = list(iter_telemetry(cls.events, realtime=False))

    def test_schema(self) -> None:
        self.assertTrue(self.ticks)
        for tick in self.ticks:
            self.assertEqual(tuple(tick.keys()), TELEMETRY_KEYS)
            self.assertIn(tick["status"], STATUSES)
            self.assertEqual(tick["vehicle_id"], "T-11")

    def test_j01_no_charge(self) -> None:
        j01 = [t for t in self.ticks if t["job_id"] == "J-01"]
        self.assertTrue(any(t["status"] == "delivered" for t in j01))
        self.assertTrue(any(t["status"] == "returning" for t in j01))
        self.assertFalse(any(t["status"] in ("charging", "divert_charge") for t in j01))
        self.assertTrue(all(t["charger_id"] is None for t in j01))
        self.assertTrue(all(t["charger_power_kw"] is None for t in j01))

    def test_j02_charges_cs2_150kw(self) -> None:
        charging = [
            t
            for t in self.ticks
            if t["job_id"] == "J-02" and t["status"] == "charging"
        ]
        self.assertTrue(charging)
        self.assertTrue(all(t["charger_id"] == "CS-2" for t in charging))
        self.assertTrue(all(t["charger_power_kw"] == 150 for t in charging))
        self.assertTrue(all(t["speed_kmh"] == 0 for t in charging))
        self.assertTrue(all(t["drive_power_kw"] == 0 for t in charging))
        leftover = next(
            t
            for t in self.ticks
            if t["job_id"] == "J-02" and t["status"] == "delivered"
        )
        self.assertAlmostEqual(leftover["range_km"], 20.0, places=1)

    def test_cs4_never_selected(self) -> None:
        ids = {t["charger_id"] for t in self.ticks}
        self.assertNotIn("CS-4", ids)
        self.assertNotIn("CS-5", ids)

    def test_t14_never_emits(self) -> None:
        self.assertTrue(any(e["vehicle_id"] == "T-14" for e in self.events))
        self.assertTrue(all(t["vehicle_id"] != "T-14" for t in self.ticks))
        refuse = {
            "job_id": "J-01",
            "city": "Cluj",
            "km": 40,
            "vehicle_id": "T-14",
            "kind": "REFUSE",
        }
        self.assertEqual(list(play_job(refuse)), [])

    def test_junctions_on_outbound(self) -> None:
        stops = [
            t["km_from_garage"]
            for t in self.ticks
            if t["job_id"] == "J-01" and t["status"] == "junction_stop"
        ]
        self.assertIn(10.0, stops)
        self.assertIn(20.0, stops)
        self.assertIn(30.0, stops)

    def test_source_is_not_an_assigner(self) -> None:
        src = (ROOT / "src" / "sim" / "driver.py").read_text(encoding="utf-8")
        self.assertNotIn("lookup_rule", src)
        self.assertNotIn("rules_mcp", src)
        self.assertNotIn("dispatch_rules", src)
        self.assertNotIn("DSP-1", src)


if __name__ == "__main__":
    unittest.main()
