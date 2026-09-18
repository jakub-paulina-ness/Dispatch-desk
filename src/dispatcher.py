"""Orchestrate kit outcomes. Assignment stays in dispatch.py. Driver only on ASSIGN."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dispatch import dispatch_job, load_jobs, load_vehicles, lookup_rule  # noqa: E402

HELP = (
    "python src/dispatcher.py\n"
    "python src/dispatcher.py --events-only\n"
    "python src/dispatcher.py --telemetry\n"
    "python src/dispatcher.py --help\n"
)


def make_event(job: dict, vehicle: dict, kind: str, dsp_ids: list[str]) -> dict:
    return {
        "job_id": job["id"],
        "city": job["city"],
        "km": job["km"],
        "vehicle_id": vehicle["id"],
        "kind": kind,
        "dsp_ids": list(dsp_ids),
        "quotes": {dsp: lookup_rule(dsp) for dsp in dsp_ids},
    }


def collect_events(
    jobs: list[dict] | None = None,
    vehicles: list[dict] | None = None,
) -> list[dict]:
    jobs = jobs if jobs is not None else load_jobs()
    vehicles = vehicles if vehicles is not None else load_vehicles()
    events: list[dict] = []
    for job in jobs:
        for kind, vehicle, dsp_ids in dispatch_job(job, vehicles):
            events.append(make_event(job, vehicle, kind, dsp_ids))
    return events


def start_driver(event: dict, play=None) -> list[dict]:
    if event.get("kind") != "ASSIGN":
        return []
    if play is None:
        from sim.driver import play_job

        play = play_job
    return list(play(event))


def run(
    *,
    jobs: list[dict] | None = None,
    vehicles: list[dict] | None = None,
    drive: bool = True,
    play=None,
) -> dict:
    events = collect_events(jobs=jobs, vehicles=vehicles)
    started: list[dict] = []
    telemetry: list[dict] = []
    for event in events:
        if event["kind"] != "ASSIGN":
            continue
        started.append(
            {"vehicle_id": event["vehicle_id"], "job_id": event["job_id"]}
        )
        if drive:
            telemetry.extend(start_driver(event, play=play))
    return {
        "events": events,
        "drivers_started": started,
        "telemetry": telemetry,
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("-h", "--help") for arg in argv):
        sys.stdout.write(HELP)
        return 0
    events_only = "--events-only" in argv
    want_telemetry = "--telemetry" in argv
    result = run(drive=not events_only)
    payload = {
        "events": result["events"],
        "drivers_started": result["drivers_started"],
    }
    if want_telemetry:
        payload["telemetry"] = result["telemetry"]
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
