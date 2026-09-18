#!/usr/bin/env python3
"""Rerun the dispatch desk from the kit files in this folder."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RULE_FILE = ROOT / "dispatch_rules.md"
VEHICLES_FILE = ROOT / "vehicles.json"
JOBS_FILE = ROOT / "jobs.json"

OFF_SCOPE = re.compile(
    r"\b("
    r"payout|settlement|we will pay|how much (do we|to) pay|"
    r"prescribe|prescription|dosage|\bdose\b|"
    r"medical advice|legal advice|"
    r"what (medicine|medication|drug)s?"
    r")\b",
    re.I,
)

OFF_DESK = (
    "The desk only assigns jobs from the roster. "
    "It will not give medical, legal, or payment advice."
)


def rules_text() -> str:
    return RULE_FILE.read_text(encoding="utf-8") if RULE_FILE.exists() else ""


def lookup_rule(query: str) -> str:
    """Same match as rules_mcp.py lookup_rule: lines that mention the query."""
    q = query.lower()
    hits = [ln for ln in rules_text().splitlines() if q and q in ln.lower()]
    return "\n".join(hits) if hits else f"No rule line matched {q!r}."


def parse_rule_line(line: str) -> tuple[str, str]:
    line = line.strip()
    if ". " in line:
        ident, rest = line.split(". ", 1)
        if ident.startswith("DSP-"):
            return ident, rest
    return "", line


def quoted(rule_id: str, query: str) -> tuple[str, str]:
    body = lookup_rule(query)
    for line in body.splitlines():
        ident, rest = parse_rule_line(line)
        if ident == rule_id:
            return ident, rest
    for line in rules_text().splitlines():
        ident, rest = parse_rule_line(line)
        if ident == rule_id:
            return ident, rest
    raise ValueError(f"Rule {rule_id} not found in dispatch_rules.md for {query!r}")


def load_vehicles() -> list[dict]:
    return json.loads(VEHICLES_FILE.read_text(encoding="utf-8"))


def load_jobs() -> list[dict]:
    return json.loads(JOBS_FILE.read_text(encoding="utf-8"))


def get_vehicle(vehicle_id: str, busy: set[str] | None = None) -> dict | None:
    for row in load_vehicles():
        if row.get("id") == vehicle_id:
            overlay = dict(row)
            if busy and vehicle_id in busy:
                overlay["status"] = "busy"
            return overlay
    return None


def get_job(job_id: str) -> dict | None:
    for row in load_jobs():
        if row.get("id") == job_id:
            return dict(row)
    return None


def gates(job: dict, vehicle: dict | None) -> list[dict]:
    if vehicle is None:
        return [
            {"id": "on_roster", "label": "On vehicles.json", "ok": False},
            {"id": "not_red", "label": "Not out of service", "ok": False},
            {"id": "free", "label": "status free", "ok": False},
            {"id": "hours", "label": "hours_ok", "ok": False},
            {"id": "range", "label": "km < range_km", "ok": False},
        ]
    km = int(job.get("km") or 0)
    range_km = int(vehicle.get("range_km") or 0)
    status = str(vehicle.get("status") or "")
    return [
        {"id": "on_roster", "label": "On vehicles.json", "ok": True},
        {"id": "not_red", "label": "Not out of service", "ok": status != "red"},
        {"id": "free", "label": "status free", "ok": status == "free"},
        {"id": "hours", "label": "hours_ok", "ok": bool(vehicle.get("hours_ok"))},
        {"id": "range", "label": "km < range_km", "ok": km < range_km},
    ]


def refuse(job: dict, vehicle_id: str | None, rule_id: str, query: str, reason: str) -> dict:
    ident, quote = quoted(rule_id, query)
    vehicle = get_vehicle(vehicle_id) if vehicle_id else None
    return {
        "kind": "decision",
        "decision": "Refuse",
        "job": job,
        "vehicle": vehicle,
        "vehicle_id": vehicle_id,
        "rule": ident,
        "quote": quote,
        "reason": reason,
        "gates": gates(job, vehicle),
    }


def assign(job: dict, vehicle: dict) -> dict:
    ident, quote = quoted("DSP-1", "free")
    return {
        "kind": "decision",
        "decision": "Assign",
        "job": job,
        "vehicle": vehicle,
        "vehicle_id": vehicle.get("id"),
        "rule": ident,
        "quote": quote,
        "reason": (
            f"{vehicle.get('id')} is free, hours_ok, and "
            f"{job.get('km')} km is less than range {vehicle.get('range_km')} km."
        ),
        "gates": gates(job, vehicle),
    }


def decide_pair(job_id: str, vehicle_id: str, busy: set[str] | None = None) -> dict:
    job = get_job(job_id)
    if job is None:
        raise KeyError(f"Unknown job {job_id}")
    vehicle = get_vehicle(vehicle_id, busy)
    if vehicle is None:
        return refuse(job, vehicle_id, "DSP-4", "invent", "Vehicle is not in vehicles.json.")
    if vehicle.get("status") == "red":
        return refuse(
            job,
            vehicle_id,
            "DSP-3",
            "red",
            "Status red is out of service.",
        )
    if vehicle.get("status") != "free" or not vehicle.get("hours_ok"):
        return refuse(
            job,
            vehicle_id,
            "DSP-1",
            "free",
            "Vehicle is not free with hours_ok true.",
        )
    if not (int(job.get("km") or 0) < int(vehicle.get("range_km") or 0)):
        return refuse(
            job,
            vehicle_id,
            "DSP-2",
            "range",
            "Job distance is not less than vehicle range_km.",
        )
    return assign(job, vehicle)


def decide_job(job_id: str, busy: set[str] | None = None) -> dict:
    job = get_job(job_id)
    if job is None:
        raise KeyError(f"Unknown job {job_id}")
    refusals: list[dict] = []
    for row in load_vehicles():
        result = decide_pair(job_id, str(row.get("id") or ""), busy)
        if result["decision"] == "Assign":
            return result
        refusals.append(result)
    for wanted in ("DSP-1", "DSP-2", "DSP-3", "DSP-4"):
        for result in refusals:
            if result["rule"] == wanted:
                return result
    if refusals:
        return refusals[0]
    raise KeyError(f"No vehicle in vehicles.json for {job_id}")


def refuse_off_scope(question: str) -> dict:
    return {
        "kind": "refusal",
        "question": question,
        "decision": "Off desk",
        "rule": "",
        "quote": "",
        "message": OFF_DESK,
    }


def render(result: dict) -> str:
    if result.get("kind") == "refusal":
        return f"Decision: {result['decision']}\n{result['message']}"
    job = result.get("job") or {}
    vehicle_id = result.get("vehicle_id") or "none"
    return (
        f"{job.get('id')} {job.get('city')} {job.get('km')}km\n"
        f"Decision: {result['decision']} {vehicle_id}\n"
        f"{result['rule']}\n"
        f"Quoted from {result['rule']}\n"
        f"{result['quote']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dispatch desk from kit files")
    parser.add_argument("job_id", nargs="?", help="J-01 or J-02")
    parser.add_argument("vehicle_id", nargs="?", help="T-11, T-12, or T-14")
    parser.add_argument("--ask", help="Clerk question (off-scope is refused)")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Print the pass case and the T-14 refuse case",
    )
    args = parser.parse_args(argv)

    if args.ask and OFF_SCOPE.search(args.ask):
        print(render(refuse_off_scope(args.ask)))
        return 0
    if args.ask:
        print(render(refuse_off_scope(args.ask)))
        return 0

    if args.demo:
        blocks = [
            render(decide_pair("J-01", "T-11")),
            render(decide_pair("J-01", "T-14")),
        ]
        print("\n\n".join(blocks))
        return 0

    if args.job_id and args.vehicle_id:
        print(render(decide_pair(args.job_id, args.vehicle_id)))
        return 0
    if args.job_id:
        print(render(decide_job(args.job_id)))
        return 0

    blocks = [render(decide_job(str(job["id"]))) for job in load_jobs()]
    print("\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
