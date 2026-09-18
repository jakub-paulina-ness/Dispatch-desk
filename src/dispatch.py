#!/usr/bin/env python3
"""Deterministic dispatch engine. Quotes come from kit handle(), not literals."""
from __future__ import annotations

import json
import sys
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent.parent / "instructions"
if str(KIT_DIR) not in sys.path:
    sys.path.insert(0, str(KIT_DIR))

from rules_mcp import handle  # noqa: E402  — kit module, not a copy

KIND_ASSIGN = "ASSIGN"
KIND_SKIP = "SKIP"
KIND_REFUSE = "REFUSE"

USAGE = (
    "python dispatch.py\n"
    "python dispatch.py J-01\n"
    "python dispatch.py J-02\n"
    "python dispatch.py --help\n"
)


def load_vehicles() -> list[dict]:
    path = KIT_DIR / "vehicles.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"{path}\n")
        raise SystemExit(1)


def load_jobs() -> list[dict]:
    path = KIT_DIR / "jobs.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"{path}\n")
        raise SystemExit(1)


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
        sys.stderr.write(f"lookup_rule missed {query!r}: {text}\n")
        raise SystemExit(1)
    return text


def evaluate_vehicle(job: dict, vehicle: dict) -> tuple[str, list[str]]:
    """Per-vehicle DSP-3 then DSP-1 then DSP-2. No first-fit."""
    status = str(vehicle.get("status") or "")
    if status == "red":
        return KIND_REFUSE, ["DSP-3"]
    if status != "free" or vehicle.get("hours_ok") is not True:
        return KIND_SKIP, ["DSP-1"]
    km = int(job.get("km") or 0)
    range_km = int(vehicle.get("range_km") or 0)
    if not (km < range_km):
        return KIND_SKIP, ["DSP-2"]
    return KIND_ASSIGN, ["DSP-1", "DSP-2"]


def dispatch_job(
    job: dict, vehicles: list[dict]
) -> list[tuple[str, dict, list[str]]]:
    """Roster order. First ASSIGN is kept; later ASSIGN becomes SKIP with no ids."""
    assigned = None
    rows: list[tuple[str, dict, list[str]]] = []
    for vehicle in vehicles:
        kind, dsp_ids = evaluate_vehicle(job, vehicle)
        if kind == KIND_ASSIGN:
            if assigned is None:
                assigned = vehicle
                rows.append((kind, vehicle, dsp_ids))
            else:
                rows.append((KIND_SKIP, vehicle, []))
        else:
            rows.append((kind, vehicle, dsp_ids))
    return rows


def format_job_block(job: dict, outcomes: list[tuple[str, dict, list[str]]]) -> str:
    lines = [f"=== JOB {job['id']} {job['city']} {job['km']} km ==="]
    for kind, vehicle, dsp_ids in outcomes:
        lines.append(f"{kind} vehicle={vehicle['id']}")
        for dsp_id in dsp_ids:
            lines.append(f"  RULE {dsp_id}: {lookup_rule(dsp_id)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args in (["-h"], ["--help"]):
        sys.stdout.write(USAGE)
        return 0
    if len(args) > 1:
        sys.stderr.write(USAGE)
        return 2

    vehicles = load_vehicles()
    jobs = load_jobs()
    if args:
        job_id = args[0]
        jobs = [row for row in jobs if row.get("id") == job_id]
        if not jobs:
            sys.stderr.write(f"unknown job: {job_id}\n")
            return 2

    blocks = [
        format_job_block(job, dispatch_job(job, vehicles)) for job in jobs
    ]
    sys.stdout.write("\n\n".join(blocks) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
