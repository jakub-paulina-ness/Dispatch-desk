#!/usr/bin/env python3
"""API helpers still match the kit desk decisions."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server  # noqa: E402
import sim  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class WebUsesDesk(unittest.TestCase):
    def setUp(self) -> None:
        server.reset()

    def test_j01_recommends_t11(self) -> None:
        board = server.board_payload("J-01")
        rec = board["recommendation"]
        self.assertEqual(rec["decision"], "Assign")
        self.assertEqual(rec["vehicle_id"], "T-11")
        self.assertEqual(rec["rule"], "DSP-1")
        self.assertTrue(board["can_send"])

    def test_t14_stays_refused(self) -> None:
        board = server.board_payload("J-01", "T-14")
        rec = board["recommendation"]
        self.assertEqual(rec["decision"], "Refuse")
        self.assertEqual(rec["rule"], "DSP-3")
        self.assertFalse(board["can_send"])

    def test_quotes_come_from_rule_file(self) -> None:
        import desk

        text = desk.rules_text()
        for job_id, vehicle_id in (("J-01", "T-11"), ("J-01", "T-14")):
            rec = server.board_payload(job_id, vehicle_id)["recommendation"]
            self.assertIn(rec["rule"], text)
            self.assertIn(rec["quote"], text)

    def test_confirm_then_undo(self) -> None:
        sent = server.confirm("J-01", "T-11")
        self.assertTrue(sent["ok"])
        self.assertIn("T-11", server.busy_ids())
        after = server.board_payload("J-01", "T-11")
        self.assertEqual(after["recommendation"]["phase"], "assigned")
        self.assertFalse(after["can_send"])
        undone = server.undo()
        self.assertTrue(undone["ok"])
        self.assertNotIn("T-11", server.busy_ids())
        opened = server.board_payload("J-01", "T-11")
        self.assertEqual(opened["recommendation"]["decision"], "Assign")
        self.assertTrue(opened["can_send"])

    def test_confirm_refuses_t14(self) -> None:
        sent = server.confirm("J-01", "T-14")
        self.assertFalse(sent["ok"])
        self.assertEqual(server.STATE["log"], [])

    def test_ask_refuses_payout(self) -> None:
        result = server.ask_payload("What should we pay the driver?", "J-01", "T-11")
        self.assertEqual(result["kind"], "off_desk")
        self.assertEqual(result["label"], "Off desk")
        self.assertEqual(result["rule"], "")
        self.assertIn("payment", result["detail"].lower())

    def test_ask_t14_quotes_dsp3(self) -> None:
        result = server.ask_payload("Can we send T-14?", "J-01", None)
        self.assertEqual(result["label"], "Refuse")
        self.assertEqual(result["rule"], "DSP-3")

    def test_dispatcher_is_who_clicks(self) -> None:
        board = server.board_payload("J-01")
        self.assertEqual(board["who_clicks"], board["dispatcher"])
        self.assertEqual(board["dispatcher"], "A. Pop")

    def test_idle_range_holds(self) -> None:
        start = sim.vehicle("T-11")["range_km"]
        sim.advance(600)
        self.assertAlmostEqual(sim.vehicle("T-11")["range_km"], start)
        self.assertEqual(sim.dsp_status(sim.vehicle("T-11")), "free")

    def test_pause_keeps_speed_zero(self) -> None:
        out = server.set_speed(0)
        self.assertEqual(sim.S["speed"], 0)
        self.assertEqual(out["board"]["sim"]["speed"], 0)
        start = sim.S["sim_s"]
        sim.sync_wall(__import__("time").monotonic())
        sim.sync_wall(__import__("time").monotonic() + 2)
        self.assertEqual(sim.S["sim_s"], start)

    def test_long_clock_does_not_fail_hours(self) -> None:
        sim.advance(80_000)
        self.assertTrue(sim.hours_ok(sim.vehicle("T-11")))
        rec = server.board_payload("J-01", "T-11")["recommendation"]
        self.assertEqual(rec["decision"], "Assign")

    def test_busy_range_drops(self) -> None:
        start = sim.vehicle("T-12")["range_km"]
        sim.advance(180)
        self.assertLess(sim.vehicle("T-12")["range_km"], start)
        self.assertEqual(sim.dsp_status(sim.vehicle("T-12")), "busy")

    def test_t14_service_then_assignable(self) -> None:
        board = server.board_payload("J-01", "T-14")
        self.assertEqual(board["recommendation"]["rule"], "DSP-3")
        out = server.call_service("T-14")
        self.assertTrue(out["ok"])
        self.assertTrue(sim.van()["active"])
        self.assertEqual(server.board_payload("J-01", "T-14")["recommendation"]["rule"], "DSP-3")
        sim.advance(12_000)
        rec = server.board_payload("J-01", "T-14")["recommendation"]
        self.assertEqual(rec["decision"], "Assign")
        self.assertEqual(rec["vehicle_id"], "T-14")
        self.assertTrue(sim.vehicle("T-14")["hours_flag"])
        self.assertEqual(sim.dsp_status(sim.vehicle("T-14")), "free")

    def test_service_van_not_on_roster(self) -> None:
        import desk

        ids = {row["id"] for row in desk.load_vehicles()}
        self.assertEqual(ids, {"T-11", "T-12", "T-14"})
        server.call_service("T-14")
        self.assertTrue(sim.van()["active"])
        self.assertNotIn(sim.van()["id"], ids)

    def test_invented_service_target_quotes_dsp4(self) -> None:
        out = server.call_service("T-99")
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "DSP-4")

    def test_oradea_warns_then_charge_restores_range(self) -> None:
        before = server.board_payload("J-02", "T-11")
        self.assertTrue(any("Supercharger" in note or "charger" in note.lower() for note in before["warnings"]))
        sent = server.confirm("J-02", "T-11")
        self.assertTrue(sent["ok"])
        sim.advance(12_000)
        parked = sim.vehicle("T-11")
        self.assertEqual(sim.dsp_status(parked), "free")
        self.assertLess(parked["range_km"], 40)
        before = parked["range_km"]
        charged = server.send_charge("T-11", "sc-oradea")
        self.assertTrue(charged["ok"])
        sim.advance(8_000)
        self.assertGreater(sim.vehicle("T-11")["range_km"], before)

    def test_kit_files_unchanged(self) -> None:
        vehicles = json.loads((ROOT / "vehicles.json").read_text(encoding="utf-8"))
        jobs = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
        self.assertEqual([row["id"] for row in vehicles], ["T-11", "T-12", "T-14"])
        self.assertEqual(vehicles[2]["status"], "red")
        self.assertEqual([row["id"] for row in jobs], ["J-01", "J-02"])
        server.confirm("J-01", "T-11")
        server.call_service("T-14")
        vehicles_after = json.loads((ROOT / "vehicles.json").read_text(encoding="utf-8"))
        self.assertEqual(vehicles, vehicles_after)


if __name__ == "__main__":
    unittest.main()
