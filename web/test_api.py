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
        sim.set_speed(1)

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

    def test_agents_on_board_assign_t11(self) -> None:
        pack = server.board_payload("J-01")["agents"]
        self.assertEqual(pack["plugin"], "dispatch-desk")
        self.assertEqual(len(pack["events"]), 6)
        self.assertEqual(
            [(row["job_id"], row["vehicle_id"], row["kind"]) for row in pack["events"]],
            [
                ("J-01", "T-11", "ASSIGN"),
                ("J-01", "T-12", "SKIP"),
                ("J-01", "T-14", "REFUSE"),
                ("J-02", "T-11", "ASSIGN"),
                ("J-02", "T-12", "SKIP"),
                ("J-02", "T-14", "REFUSE"),
            ],
        )
        ticket = pack["dispatcher"]
        self.assertEqual(ticket["kind"], "ASSIGN")
        self.assertEqual(ticket["vehicle_id"], "T-11")
        self.assertEqual(ticket["decision"], "Assign")
        self.assertIn("DSP-1", ticket["dsp_ids"])
        self.assertEqual(pack["driver"]["action"], "Accept")
        self.assertEqual(pack["driver"]["status"], "en_route")
        self.assertEqual(pack["driver"]["city"], "Cluj")

    def test_agent_refuses_t14_driver_declines(self) -> None:
        pack = server.board_payload("J-01", "T-14")["agents"]
        self.assertEqual(pack["dispatcher"]["kind"], "REFUSE")
        self.assertEqual(pack["dispatcher"]["rule"], "DSP-3")
        self.assertEqual(pack["driver"]["action"], "Decline")
        self.assertEqual(pack["driver"]["status"], "idle")
        self.assertEqual(pack["driver"]["city"], "-")

    def test_agent_skips_t12_driver_declines(self) -> None:
        pack = server.board_payload("J-01", "T-12")["agents"]
        self.assertEqual(pack["dispatcher"]["kind"], "SKIP")
        self.assertEqual(pack["driver"]["action"], "Decline")

    def test_confirm_starts_driver_agent(self) -> None:
        sent = server.confirm("J-01", "T-11")
        self.assertTrue(sent["ok"])
        started = sent["board"]["agents"]["started"]
        self.assertEqual(started[0]["action"], "Accept")
        self.assertEqual(started[0]["job_id"], "J-01")
        self.assertEqual(started[0]["vehicle_id"], "T-11")
        refused = server.confirm("J-01", "T-14")
        self.assertFalse(refused["ok"])
        self.assertEqual(len(server.STATE["started"]), 1)
        undone = server.undo()
        self.assertTrue(undone["ok"])
        self.assertEqual(undone["board"]["agents"]["started"], [])

    def test_plugin_packs_agents(self) -> None:
        plugin = ROOT / ".grok" / "plugins" / "dispatch-desk"
        self.assertTrue((plugin / "agents" / "dispatcher.md").is_file())
        self.assertTrue((plugin / "agents" / "driver.md").is_file())
        text = (plugin / "agents" / "dispatcher.md").read_text(encoding="utf-8")
        self.assertNotIn("python3 -c", text)
        self.assertIn("python -c", text)

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
        self.assertTrue(any("CS-2" in note or "charger" in note.lower() for note in before["warnings"]))
        sent = server.confirm("J-02", "T-11")
        self.assertTrue(sent["ok"])
        sim.advance(12_000)
        parked = sim.vehicle("T-11")
        self.assertEqual(sim.dsp_status(parked), "free")
        self.assertLess(parked["range_km"], 40)
        before = parked["range_km"]
        charged = server.send_charge("T-11", "CS-2")
        self.assertTrue(charged["ok"])
        sim.advance(8_000)
        self.assertGreater(sim.vehicle("T-11")["range_km"], before)

    def test_map_uses_locations_json(self) -> None:
        board = server.board_payload("J-01")
        ids = {row["id"] for row in board["map"]["chargers"]}
        self.assertEqual(ids, {"G-0", "CS-1", "CS-2", "CS-3", "CS-4", "CS-5"})
        cs2 = next(row for row in board["map"]["chargers"] if row["id"] == "CS-2")
        self.assertEqual(cs2["power_kw"], 150)
        self.assertTrue(cs2["reachable"])
        cs4 = next(row for row in board["map"]["chargers"] if row["id"] == "CS-4")
        self.assertEqual(cs4["power_kw"], 350)
        self.assertFalse(cs4["reachable"])
        loc = server.locations_payload()
        self.assertEqual(loc["source"], ".docs/reference/locations.json")
        self.assertTrue(loc["not_a_dispatch_rule"])
        self.assertEqual(loc["garage"]["id"], "G-0")
        blocked = server.send_charge("T-11", "CS-4")
        self.assertFalse(blocked["ok"])

    def test_reset_keeps_selected_speed(self) -> None:
        sim.set_speed(16)
        sim.reset()
        self.assertEqual(sim.S["speed"], 16)
        sim.set_speed(0)
        server.reset()
        self.assertEqual(sim.S["speed"], 0)
        sim.reset(1)
        self.assertEqual(sim.S["speed"], 1)
        sim.set_speed(0.5)
        sim.reset()
        self.assertEqual(sim.S["speed"], 0.5)

    def test_half_speed_is_allowed(self) -> None:
        out = server.set_speed(0.5)
        self.assertEqual(sim.S["speed"], 0.5)
        self.assertEqual(out["board"]["sim"]["speed"], 0.5)
        start = sim.S["sim_s"]
        sim.sync_wall(10.0)
        sim.sync_wall(10.2)
        self.assertGreater(sim.S["sim_s"], start)
        self.assertAlmostEqual(sim.S["sim_s"] - start, 0.2 * 0.5 * sim.SIM_PER_WALL_1X, delta=0.05)

    def test_drive_follows_path_linearly(self) -> None:
        sent = server.confirm("J-01", "T-11")
        self.assertTrue(sent["ok"])
        truck = sim.vehicle("T-11")
        task = truck["queue"][0]
        self.assertEqual(task["kind"], "drive")
        start = (truck["x"], truck["y"])
        sim.advance(30)
        mid_done = truck["queue"][0]["done"]
        expected = (sim.CRUISE_KMH / 3600.0) * 30
        self.assertAlmostEqual(mid_done, expected, delta=0.05)
        self.assertLess(mid_done, task["km"] * 0.5)
        mid = (truck["x"], truck["y"])
        self.assertGreater(sim._hypot(start, mid), 0.5)
        pub = sim.public_vehicle("T-11")
        self.assertGreater(pub["speed_kmh"], 0)
        self.assertGreater(len(pub["path"]), 1)
        self.assertAlmostEqual(pub["path_done"], mid_done, delta=0.05)

    def test_kit_files_unchanged(self) -> None:
        kit = ROOT / "instructions"
        vehicles = json.loads((kit / "vehicles.json").read_text(encoding="utf-8"))
        jobs = json.loads((kit / "jobs.json").read_text(encoding="utf-8"))
        self.assertEqual([row["id"] for row in vehicles], ["T-11", "T-12", "T-14"])
        self.assertEqual(vehicles[2]["status"], "red")
        self.assertEqual([row["id"] for row in jobs], ["J-01", "J-02"])
        server.confirm("J-01", "T-11")
        server.call_service("T-14")
        vehicles_after = json.loads((kit / "vehicles.json").read_text(encoding="utf-8"))
        self.assertEqual(vehicles, vehicles_after)


if __name__ == "__main__":
    unittest.main()
