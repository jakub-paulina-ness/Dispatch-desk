"""S-03 unittest suite for the dispatch engine stdout contract."""

from __future__ import annotations

import contextlib
import inspect
import io
import json
import re
import subprocess
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_KIT = _ROOT / "instructions"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
import dispatch  # noqa: E402

_ENGINE_FILE = (_SRC / "dispatch.py").resolve()
if Path(dispatch.__file__).resolve() != _ENGINE_FILE:
    raise ImportError(
        f"import dispatch resolved to {dispatch.__file__!r}, expected {_ENGINE_FILE}"
    )

_ALLOWED_VEHICLES = frozenset({"T-11", "T-12", "T-14"})
_FORBIDDEN_SRC = (
    "out of service",
    "hours_ok true",
    "less than vehicle range",
)
_JOB_HEADER = re.compile(r"^=== JOB (\S+) (\S+) (\d+) km ===$")
_VEHICLE_LINE = re.compile(r"^(ASSIGN|SKIP|REFUSE) vehicle=(\S+)$")
_RULE_LINE = re.compile(r"^  RULE (DSP-[1-4]): (.+)$")


@dataclass
class VehicleLine:
    kind: str
    vehicle_id: str
    rules: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class JobBlock:
    job_id: str
    city: str
    km: int
    vehicles: list[VehicleLine] = field(default_factory=list)


def setUpModule() -> None:
    actual = Path(dispatch.__file__).resolve()
    if actual != _ENGINE_FILE:
        raise AssertionError(f"dispatch.__file__ is {actual}, expected {_ENGINE_FILE}")


def _kit_handle_lookup(query: str) -> str:
    if str(_KIT) not in sys.path:
        sys.path.insert(0, str(_KIT))
    from rules_mcp import handle

    resp = handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "lookup_rule",
                "arguments": {"query": query},
            },
        }
    )
    return resp["result"]["content"][0]["text"]


def _run_main(argv: list[str] | None = None) -> tuple[int, str, str]:
    if argv is None:
        argv = []
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = dispatch.main(list(argv))
    except SystemExit as exc:
        code = 0 if exc.code is None else exc.code
        if not isinstance(code, int):
            stderr.write(str(code))
            code = 1
        return code, stdout.getvalue(), stderr.getvalue()
    if result is None:
        result = 0
    return int(result), stdout.getvalue(), stderr.getvalue()


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_ROOT / "dispatch.py"), *args],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def _parse_stdout(text: str) -> list[JobBlock]:
    lines = text.splitlines()
    blocks: list[JobBlock] = []
    current: JobBlock | None = None
    current_veh: VehicleLine | None = None

    def finish_vehicle() -> None:
        nonlocal current_veh
        if current_veh is None:
            return
        assert current is not None
        current.vehicles.append(current_veh)
        current_veh = None

    def finish_block() -> None:
        nonlocal current
        finish_vehicle()
        if current is None:
            return
        if not current.vehicles:
            raise AssertionError(f"job {current.job_id} has no vehicle lines")
        blocks.append(current)
        current = None

    for i, line in enumerate(lines, start=1):
        if line == "":
            continue
        header = _JOB_HEADER.match(line)
        if header:
            finish_block()
            current = JobBlock(
                job_id=header.group(1),
                city=header.group(2),
                km=int(header.group(3)),
            )
            continue
        if current is None:
            raise AssertionError(f"line {i}: expected JOB header, got {line!r}")
        vehicle = _VEHICLE_LINE.match(line)
        if vehicle:
            finish_vehicle()
            current_veh = VehicleLine(kind=vehicle.group(1), vehicle_id=vehicle.group(2))
            continue
        rule = _RULE_LINE.match(line)
        if rule:
            if current_veh is None:
                raise AssertionError(f"line {i}: RULE without vehicle: {line!r}")
            current_veh.rules.append((rule.group(1), rule.group(2)))
            continue
        raise AssertionError(f"line {i}: does not match stdout grammar: {line!r}")

    finish_block()
    if not blocks:
        raise AssertionError(f"no JOB blocks in stdout:\n{text}")
    return blocks


def _blocks_from_main(argv: list[str] | None = None) -> tuple[str, list[JobBlock]]:
    code, out, err = _run_main(argv)
    if code != 0:
        raise AssertionError(
            f"dispatch.main({argv!r}) exited {code}\nstderr:\n{err}\nstdout:\n{out}"
        )
    return out, _parse_stdout(out)


def _job(blocks: list[JobBlock], job_id: str) -> JobBlock:
    found = [block for block in blocks if block.job_id == job_id]
    if len(found) != 1:
        ids = [block.job_id for block in blocks]
        raise AssertionError(f"expected one {job_id} block, got {ids}")
    return found[0]


def _vehicle(block: JobBlock, vehicle_id: str) -> VehicleLine:
    found = [row for row in block.vehicles if row.vehicle_id == vehicle_id]
    if len(found) != 1:
        ids = [row.vehicle_id for row in block.vehicles]
        raise AssertionError(f"{block.job_id}: expected one {vehicle_id}, got {ids}")
    return found[0]


def _assigned_ids(block: JobBlock) -> list[str]:
    return [row.vehicle_id for row in block.vehicles if row.kind == "ASSIGN"]


def _rule_payloads(blocks: list[JobBlock]) -> list[str]:
    payloads: list[str] = []
    for block in blocks:
        for row in block.vehicles:
            payloads.extend(payload for _dsp, payload in row.rules)
    return payloads


class TestDispatch(unittest.TestCase):
    def test_T_J01_T11(self) -> None:
        """T-J01-T11 — J-01 ASSIGN T-11."""
        _out, blocks = _blocks_from_main(["J-01"])
        block = _job(blocks, "J-01")
        self.assertEqual(_assigned_ids(block), ["T-11"])
        self.assertEqual(_vehicle(block, "T-11").kind, "ASSIGN")

    def test_T_J02_T11(self) -> None:
        """T-J02-T11 — J-02 ASSIGN T-11."""
        _out, blocks = _blocks_from_main(["J-02"])
        block = _job(blocks, "J-02")
        self.assertEqual(_assigned_ids(block), ["T-11"])
        self.assertEqual(_vehicle(block, "T-11").kind, "ASSIGN")

    def test_T_14_J01(self) -> None:
        """T-14-J01 — J-01 never ASSIGN T-14; has REFUSE T-14."""
        out, blocks = _blocks_from_main(["J-01"])
        block = _job(blocks, "J-01")
        t14 = _vehicle(block, "T-14")
        self.assertNotEqual(t14.kind, "ASSIGN")
        self.assertEqual(t14.kind, "REFUSE")
        self.assertNotIn("ASSIGN vehicle=T-14", out)

    def test_T_14_J02(self) -> None:
        """T-14-J02 — J-02 never ASSIGN T-14; has REFUSE T-14."""
        out, blocks = _blocks_from_main(["J-02"])
        block = _job(blocks, "J-02")
        t14 = _vehicle(block, "T-14")
        self.assertNotEqual(t14.kind, "ASSIGN")
        self.assertEqual(t14.kind, "REFUSE")
        self.assertNotIn("ASSIGN vehicle=T-14", out)

    def test_T_12_NEVER(self) -> None:
        """T-12-NEVER — neither job ASSIGN T-12."""
        out, blocks = _blocks_from_main([])
        self.assertNotIn("ASSIGN vehicle=T-12", out)
        for block in blocks:
            with self.subTest(job=block.job_id):
                t12 = _vehicle(block, "T-12")
                self.assertNotEqual(t12.kind, "ASSIGN")
                self.assertNotIn("T-12", _assigned_ids(block))

    def test_T_QUOTE_SUBSET(self) -> None:
        """T-QUOTE-SUBSET — every RULE payload ⊆ instructions/dispatch_rules.md."""
        out, blocks = _blocks_from_main([])
        rules_md = (_KIT / "dispatch_rules.md").read_text(encoding="utf-8")
        self.assertNotIn("No rule line matched", out)
        payloads = _rule_payloads(blocks)
        self.assertTrue(payloads, "stdout has no RULE payloads")
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertIn(payload, rules_md)

    def test_T_QUOTE_HANDLE(self) -> None:
        """T-QUOTE-HANDLE — lookup_rule('DSP-3') equals the stdout DSP-3 line."""
        _out, blocks = _blocks_from_main([])
        quoted = dispatch.lookup_rule("DSP-3")
        found = False
        for block in blocks:
            for row in block.vehicles:
                for dsp_id, payload in row.rules:
                    if dsp_id != "DSP-3":
                        continue
                    found = True
                    self.assertEqual(payload, quoted)
        self.assertTrue(found, "stdout has no RULE DSP-3 line")

    def test_T_QUOTE_DSP3(self) -> None:
        """T-QUOTE-DSP3 — T-14 block cites DSP-3 and the exact handle() line."""
        handle_line = _kit_handle_lookup("DSP-3")
        _out, blocks = _blocks_from_main([])
        for job_id in ("J-01", "J-02"):
            with self.subTest(job=job_id):
                t14 = _vehicle(_job(blocks, job_id), "T-14")
                self.assertEqual(t14.kind, "REFUSE")
                self.assertEqual([dsp for dsp, _payload in t14.rules], ["DSP-3"])
                self.assertEqual(t14.rules[0][1], handle_line)

    def test_T_QUOTE_ASSIGN(self) -> None:
        """T-QUOTE-ASSIGN — ASSIGN T-11 RULE order is DSP-1 then DSP-2."""
        _out, blocks = _blocks_from_main([])
        for job_id in ("J-01", "J-02"):
            with self.subTest(job=job_id):
                assigned = _vehicle(_job(blocks, job_id), "T-11")
                self.assertEqual(assigned.kind, "ASSIGN")
                self.assertEqual([dsp for dsp, _payload in assigned.rules], ["DSP-1", "DSP-2"])
                for dsp_id, payload in assigned.rules:
                    self.assertEqual(payload, dispatch.lookup_rule(dsp_id))

    def test_T_QUOTE_SRC(self) -> None:
        """T-QUOTE-SRC — src/dispatch.py has no DSP sentence bodies as literals."""
        self.assertTrue(_ENGINE_FILE.is_file(), "src/dispatch.py is missing")
        source = _ENGINE_FILE.read_text(encoding="utf-8")
        for needle in _FORBIDDEN_SRC:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_T_LOAD_PATH(self) -> None:
        """T-LOAD-PATH — KIT_DIR is instructions/; loaders read kit JSON from there."""
        expected = Path(dispatch.__file__).resolve().parent.parent / "instructions"
        self.assertEqual(dispatch.KIT_DIR, expected)
        self.assertEqual(dispatch.KIT_DIR.resolve(), _KIT.resolve())

        source = Path(dispatch.__file__).read_text(encoding="utf-8")
        self.assertNotIn(".docs/reference", source)
        self.assertNotIn(".docs\\reference", source)

        vehicles_src = inspect.getsource(dispatch.load_vehicles)
        jobs_src = inspect.getsource(dispatch.load_jobs)
        self.assertIn("KIT_DIR", vehicles_src)
        self.assertIn("vehicles.json", vehicles_src)
        self.assertNotIn(".docs/reference", vehicles_src)
        self.assertIn("KIT_DIR", jobs_src)
        self.assertIn("jobs.json", jobs_src)
        self.assertNotIn(".docs/reference", jobs_src)

        kit_vehicles = json.loads((expected / "vehicles.json").read_text(encoding="utf-8"))
        kit_jobs = json.loads((expected / "jobs.json").read_text(encoding="utf-8"))
        self.assertEqual(dispatch.load_vehicles(), kit_vehicles)
        self.assertEqual(dispatch.load_jobs(), kit_jobs)

    def test_T_NO_INVENT(self) -> None:
        """T-NO-INVENT — vehicles in stdout ⊆ {T-11, T-12, T-14}."""
        _out, blocks = _blocks_from_main([])
        seen = {row.vehicle_id for block in blocks for row in block.vehicles}
        self.assertTrue(seen, "stdout named no vehicles")
        self.assertTrue(seen <= _ALLOWED_VEHICLES, f"invented vehicles: {seen - _ALLOWED_VEHICLES}")

    def test_T_ORDER(self) -> None:
        """T-ORDER — vehicles in each block appear T-11, T-12, T-14."""
        _out, blocks = _blocks_from_main([])
        self.assertEqual([block.job_id for block in blocks], ["J-01", "J-02"])
        for block in blocks:
            with self.subTest(job=block.job_id):
                self.assertEqual(
                    [row.vehicle_id for row in block.vehicles],
                    ["T-11", "T-12", "T-14"],
                )

    def test_T_INDEPENDENT(self) -> None:
        """T-INDEPENDENT — both jobs ASSIGN T-11 in one python dispatch.py run."""
        proc = _run_cli([])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        blocks = _parse_stdout(proc.stdout)
        self.assertEqual([block.job_id for block in blocks], ["J-01", "J-02"])
        for block in blocks:
            with self.subTest(job=block.job_id):
                self.assertEqual(_assigned_ids(block), ["T-11"])

    def test_T_CLI_ALL(self) -> None:
        """T-CLI-ALL — subprocess python dispatch.py exit 0, two JOB blocks."""
        proc = _run_cli([])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        blocks = _parse_stdout(proc.stdout)
        self.assertEqual([block.job_id for block in blocks], ["J-01", "J-02"])

    def test_T_CLI_ONE(self) -> None:
        """T-CLI-ONE — subprocess python dispatch.py J-01 has J-01, not J-02."""
        proc = _run_cli(["J-01"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        blocks = _parse_stdout(proc.stdout)
        self.assertEqual([block.job_id for block in blocks], ["J-01"])
        self.assertNotIn("J-02", proc.stdout)

    def test_T_CLI_HELP(self) -> None:
        """T-CLI-HELP — python dispatch.py --help exit 0 and lists the four invocations."""
        proc = _run_cli(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = proc.stdout
        self.assertTrue(text.strip(), "help stdout is empty")
        for token in ("dispatch.py", "J-01", "J-02", "--help"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_T_CLI_BAD(self) -> None:
        """T-CLI-BAD — python dispatch.py J-99 exit 2."""
        proc = _run_cli(["J-99"])
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        self.assertIn("unknown job:", proc.stderr)
        self.assertNotIn("can't open file", (proc.stderr + proc.stdout).lower())
