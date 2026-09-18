"""S-02 engine + S-11 dispatcher. Kit quotes from handle(); T-14 stays refused."""
from __future__ import annotations

import json
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
KIT = _ROOT / "instructions"
FORBIDDEN_SRC = (
    "out of service",
    "hours_ok true",
    "less than vehicle range",
)


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(_ROOT / "dispatch.py"), *args],
        cwd=_ROOT,
        text=True,
        capture_output=True,
    )


def parse_blocks(stdout: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in stdout.splitlines():
        if line.startswith("=== JOB "):
            if current is not None:
                blocks[current] = "\n".join(buf)
            current = line.split()[2]
            buf = [line]
        else:
            buf.append(line)
    if current is not None:
        blocks[current] = "\n".join(buf)
    return blocks


class DispatchEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        got = Path(dispatch.__file__).resolve()
        want = (_SRC / "dispatch.py").resolve()
        if got != want:
            raise AssertionError(f"imported dispatch from {got}, expected {want}")

    def test_j01_t11(self) -> None:
        jobs = {row["id"]: row for row in dispatch.load_jobs()}
        vehicles = dispatch.load_vehicles()
        kinds = {
            vehicle["id"]: kind
            for kind, vehicle, _ in dispatch.dispatch_job(jobs["J-01"], vehicles)
        }
        self.assertEqual(kinds["T-11"], "ASSIGN")

    def test_j02_t11(self) -> None:
        jobs = {row["id"]: row for row in dispatch.load_jobs()}
        vehicles = dispatch.load_vehicles()
        kinds = {
            vehicle["id"]: kind
            for kind, vehicle, _ in dispatch.dispatch_job(jobs["J-02"], vehicles)
        }
        self.assertEqual(kinds["T-11"], "ASSIGN")

    def test_t14_j01(self) -> None:
        jobs = {row["id"]: row for row in dispatch.load_jobs()}
        vehicles = dispatch.load_vehicles()
        rows = dispatch.dispatch_job(jobs["J-01"], vehicles)
        t14 = next(row for row in rows if row[1]["id"] == "T-14")
        self.assertEqual(t14[0], "REFUSE")
        self.assertEqual(t14[2], ["DSP-3"])
        self.assertNotEqual(t14[0], "ASSIGN")

    def test_t14_j02(self) -> None:
        jobs = {row["id"]: row for row in dispatch.load_jobs()}
        vehicles = dispatch.load_vehicles()
        rows = dispatch.dispatch_job(jobs["J-02"], vehicles)
        t14 = next(row for row in rows if row[1]["id"] == "T-14")
        self.assertEqual(t14[0], "REFUSE")
        self.assertEqual(t14[2], ["DSP-3"])

    def test_t12_never(self) -> None:
        vehicles = dispatch.load_vehicles()
        for job in dispatch.load_jobs():
            for kind, vehicle, _ in dispatch.dispatch_job(job, vehicles):
                if vehicle["id"] == "T-12":
                    self.assertNotEqual(kind, "ASSIGN")
                    self.assertEqual(kind, "SKIP")

    def test_quote_subset(self) -> None:
        rules = (KIT / "dispatch_rules.md").read_text(encoding="utf-8")
        for dsp_id in ("DSP-1", "DSP-2", "DSP-3", "DSP-4"):
            quote = dispatch.lookup_rule(dsp_id)
            self.assertIn(quote, rules)

    def test_quote_handle(self) -> None:
        self.assertEqual(
            dispatch.lookup_rule("DSP-1"),
            dispatch.lookup_rule("DSP-1"),
        )
        proc = cli()
        self.assertEqual(proc.returncode, 0)
        for dsp_id in ("DSP-1", "DSP-2", "DSP-3"):
            self.assertIn(dispatch.lookup_rule(dsp_id), proc.stdout)

    def test_quote_dsp3(self) -> None:
        proc = cli("J-01")
        self.assertIn("REFUSE vehicle=T-14", proc.stdout)
        self.assertIn(dispatch.lookup_rule("DSP-3"), proc.stdout)

    def test_quote_assign(self) -> None:
        proc = cli("J-01")
        block = parse_blocks(proc.stdout)["J-01"]
        assign, _, rest = block.partition("SKIP")
        self.assertIn("ASSIGN vehicle=T-11", assign)
        self.assertIn("RULE DSP-1:", assign)
        self.assertIn("RULE DSP-2:", assign)
        self.assertIn(dispatch.lookup_rule("DSP-1"), assign)
        self.assertIn(dispatch.lookup_rule("DSP-2"), assign)

    def test_quote_src(self) -> None:
        src = (_SRC / "dispatch.py").read_text(encoding="utf-8")
        for needle in FORBIDDEN_SRC:
            self.assertNotIn(needle, src)

    def test_load_path(self) -> None:
        self.assertEqual(dispatch.KIT_DIR.resolve(), KIT.resolve())
        src = (_SRC / "dispatch.py").read_text(encoding="utf-8")
        self.assertNotIn(".docs/reference/", src)
        self.assertTrue(str(dispatch.KIT_DIR).endswith("instructions"))

    def test_no_invent(self) -> None:
        proc = cli("J-99")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown job: J-99", proc.stderr)

    def test_order(self) -> None:
        jobs = {row["id"]: row for row in dispatch.load_jobs()}
        vehicles = dispatch.load_vehicles()
        ids = [vehicle["id"] for _, vehicle, _ in dispatch.dispatch_job(jobs["J-01"], vehicles)]
        self.assertEqual(ids, ["T-11", "T-12", "T-14"])

    def test_independent(self) -> None:
        proc = cli()
        blocks = parse_blocks(proc.stdout)
        self.assertIn("ASSIGN vehicle=T-11", blocks["J-01"])
        self.assertIn("ASSIGN vehicle=T-11", blocks["J-02"])

    def test_cli_all(self) -> None:
        proc = cli()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("=== JOB J-01 Cluj 40 km ===", proc.stdout)
        self.assertIn("=== JOB J-02 Oradea 160 km ===", proc.stdout)
        self.assertIn("SKIP vehicle=T-12", proc.stdout)
        self.assertIn("REFUSE vehicle=T-14", proc.stdout)
        self.assertNotIn("No rule line matched", proc.stdout)

    def test_cli_one(self) -> None:
        proc = cli("J-01")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("J-01", proc.stdout)
        self.assertNotIn("J-02", proc.stdout)

    def test_cli_help(self) -> None:
        proc = cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("python dispatch.py", proc.stdout)
        self.assertIn("python dispatch.py J-01", proc.stdout)
        self.assertIn("python dispatch.py J-02", proc.stdout)
        self.assertIn("python dispatch.py --help", proc.stdout)

    def test_cli_bad(self) -> None:
        proc = cli("J-99")
        self.assertEqual(proc.returncode, 2)


class DispatcherAgent(unittest.TestCase):
    def test_six_events_roster_order(self) -> None:
        dispatcher.reset_started()
        events = dispatcher.collect_events(start=True)
        self.assertEqual(len(events), 6)
        got = [(e["job_id"], e["vehicle_id"], e["kind"], e["dsp_ids"]) for e in events]
        self.assertEqual(
            got,
            [
                ("J-01", "T-11", "ASSIGN", ["DSP-1", "DSP-2"]),
                ("J-01", "T-12", "SKIP", ["DSP-1"]),
                ("J-01", "T-14", "REFUSE", ["DSP-3"]),
                ("J-02", "T-11", "ASSIGN", ["DSP-1", "DSP-2"]),
                ("J-02", "T-12", "SKIP", ["DSP-1"]),
                ("J-02", "T-14", "REFUSE", ["DSP-3"]),
            ],
        )

    def test_start_driver_assign_only(self) -> None:
        dispatcher.reset_started()
        dispatcher.collect_events(start=True)
        self.assertEqual(dispatcher.STARTED, [("T-11", "J-01"), ("T-11", "J-02")])
        self.assertTrue(all(v == "T-11" for v, _ in dispatcher.STARTED))

    def test_quotes_from_lookup(self) -> None:
        dispatcher.reset_started()
        events = dispatcher.collect_events(start=False)
        for event in events:
            for dsp_id in event["dsp_ids"]:
                self.assertEqual(event["quotes"][dsp_id], dispatch.lookup_rule(dsp_id))

    def test_no_locations_read(self) -> None:
        src = (_SRC / "dispatcher.py").read_text(encoding="utf-8")
        self.assertNotIn("locations.json", src)


if __name__ == "__main__":
    unittest.main()
