#!/usr/bin/env python3
"""API helpers still match the kit desk decisions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server  # noqa: E402


class WebUsesDesk(unittest.TestCase):
    def setUp(self) -> None:
        server.STATE["busy"] = set()
        server.STATE["log"] = []

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
        self.assertIn("T-11", server.STATE["busy"])
        after = server.board_payload("J-01", "T-11")
        self.assertEqual(after["recommendation"]["decision"], "Refuse")
        undone = server.undo()
        self.assertTrue(undone["ok"])
        self.assertNotIn("T-11", server.STATE["busy"])

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


if __name__ == "__main__":
    unittest.main()
