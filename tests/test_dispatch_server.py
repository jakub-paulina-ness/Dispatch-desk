"""S-14: stdlib desk on 127.0.0.1, same engine as CLI."""

from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import dispatch_server  # noqa: E402
from dispatch import lookup_rule  # noqa: E402


class DeskServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = dispatch_server.make_server("127.0.0.1", 0, drive=True)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.httpd.server_address[:2]
        cls.base = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def get(self, path: str):
        with urllib.request.urlopen(self.base + path, timeout=5) as resp:
            body = resp.read()
            return resp.status, resp.headers.get_content_type(), body

    def test_bind_localhost_only(self) -> None:
        self.assertEqual(dispatch_server.HOST, "127.0.0.1")
        self.assertEqual(dispatch_server.PORT, 8765)
        self.assertEqual(self.httpd.server_address[0], "127.0.0.1")
        with self.assertRaises(ValueError):
            dispatch_server.make_server("0.0.0.0", 0, drive=False)

    def test_api_dispatch_matches_cli(self) -> None:
        status, ctype, body = self.get("/api/dispatch")
        self.assertEqual(status, 200)
        self.assertEqual(ctype, "application/json")
        events = json.loads(body)["events"]
        self.assertEqual(len(events), 6)
        by_key = {(e["job_id"], e["vehicle_id"]): e for e in events}
        self.assertEqual(by_key[("J-01", "T-11")]["kind"], "ASSIGN")
        self.assertEqual(by_key[("J-02", "T-11")]["kind"], "ASSIGN")
        self.assertEqual(by_key[("J-01", "T-14")]["kind"], "REFUSE")
        self.assertEqual(by_key[("J-02", "T-14")]["kind"], "REFUSE")
        self.assertEqual(by_key[("J-01", "T-12")]["kind"], "SKIP")
        quote = by_key[("J-01", "T-14")]["quotes"]["DSP-3"]
        self.assertEqual(quote, lookup_rule("DSP-3"))

    def test_api_locations(self) -> None:
        status, _, body = self.get("/api/locations")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        stations = {row["id"]: row for row in payload["charging_stations"]}
        self.assertEqual(stations["CS-2"]["power_kw"], 150)
        self.assertEqual(stations["CS-4"]["power_kw"], 350)

    def test_api_telemetry_t11_only(self) -> None:
        status, _, body = self.get("/api/telemetry")
        self.assertEqual(status, 200)
        events = json.loads(body)["events"]
        self.assertTrue(events)
        self.assertTrue(all(tick["vehicle_id"] == "T-11" for tick in events))
        self.assertTrue(all(tick["vehicle_id"] != "T-14" for tick in events))
        jobs = {tick["job_id"] for tick in events}
        self.assertEqual(jobs, {"J-01", "J-02"})

    def test_index_is_s10_desk(self) -> None:
        status, ctype, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(ctype, "text/html")
        text = body.decode("utf-8")
        self.assertIn("Dispatch desk", text)
        self.assertIn("id=\"kit\"", text)
        self.assertIn("id=\"telemetry\"", text)
        css_status, _, css = self.get("/desk.css")
        self.assertEqual(css_status, 200)
        self.assertTrue(css)

    def test_no_path_escape(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/../../instructions/dispatch_rules.md")
        self.assertEqual(ctx.exception.code, 404)

    def test_empty_telemetry_without_drive(self) -> None:
        httpd = dispatch_server.make_server("127.0.0.1", 0, drive=False)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = httpd.server_address[:2]
            with urllib.request.urlopen(
                f"http://{host}:{port}/api/telemetry", timeout=5
            ) as resp:
                events = json.loads(resp.read())["events"]
            self.assertEqual(events, [])
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_stdlib_only(self) -> None:
        src = (SRC / "dispatch_server.py").read_text(encoding="utf-8")
        self.assertIn("http.server", src)
        self.assertNotIn("flask", src.lower())
        self.assertNotIn("pip", src)


if __name__ == "__main__":
    unittest.main()
