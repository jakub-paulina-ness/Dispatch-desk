"""Deterministic kit assigner. Quotes come from rules_mcp.handle()."""

from __future__ import annotations

import json
import sys
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent.parent / "instructions"
if str(KIT_DIR) not in sys.path:
    sys.path.insert(0, str(KIT_DIR))

from rules_mcp import handle  # noqa: E402

HELP = (
    "python dispatch.py\n"
    "python dispatch.py J-01\n"
    "python dispatch.py J-02\n"
    "python dispatch.py --help\n"
)


def load_vehicles() -> list[dict]:
    return json.loads((KIT_DIR / "vehicles.json").read_text(encoding="utf-8"))


def load_jobs() -> list[dict]:
    return json.loads((KIT_DIR / "jobs.json").read_text(encoding="utf-8"))


def lookup_rule(query: str) -> str:
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
    text = resp["result"]["content"][0]["text"]
    if not text or text.startswith("No rule line matched"):
        raise SystemExit(f"lookup_rule missed {query!r}: {text}")
    return text


def evaluate_vehicle(job: dict, vehicle: dict) -> tuple[str, list[str]]:
    if vehicle["status"] == "red":
        return ("REFUSE", ["DSP-3"])
    if vehicle["status"] != "free" or vehicle["hours_ok"] is not True:
        return ("SKIP", ["DSP-1"])
    if not (job["km"] < vehicle["range_km"]):
        return ("SKIP", ["DSP-2"])
    return ("ASSIGN", ["DSP-1", "DSP-2"])


def dispatch_job(job: dict, vehicles: list[dict]) -> list[tuple[str, dict, list[str]]]:
    assigned = False
    outcomes: list[tuple[str, dict, list[str]]] = []
    for vehicle in vehicles:
        kind, dsp_ids = evaluate_vehicle(job, vehicle)
        if kind == "ASSIGN":
            if assigned:
                kind, dsp_ids = "SKIP", []
            else:
                assigned = True
        outcomes.append((kind, vehicle, dsp_ids))
    return outcomes


def format_job_block(job: dict, outcomes: list) -> str:
    lines = [f"=== JOB {job['id']} {job['city']} {job['km']} km ==="]
    for kind, vehicle, dsp_ids in outcomes:
        lines.append(f"{kind} vehicle={vehicle['id']}")
        for dsp in dsp_ids:
            quote = lookup_rule(dsp)
            lines.append(f"  RULE {dsp}: {quote}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("-h", "--help") for arg in argv):
        sys.stdout.write(HELP)
        return 0
    job_id = next((arg for arg in argv if not arg.startswith("-")), None)
    try:
        vehicles = load_vehicles()
        jobs = load_jobs()
    except FileNotFoundError as exc:
        sys.stderr.write(f"{exc.filename or exc}\n")
        return 1
    if job_id is not None:
        jobs = [job for job in jobs if job["id"] == job_id]
        if not jobs:
            sys.stderr.write(f"unknown job: {job_id}\n")
            return 2
    blocks = [format_job_block(job, dispatch_job(job, vehicles)) for job in jobs]
    sys.stdout.write("\n\n".join(blocks) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
