#!/usr/bin/env python3
"""Dispatcher loop over the engine. Starts a driver only on ASSIGN."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
FIXTURE = ROOT / "pipelines" / "fixtures" / "dispatch_events.json"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dispatch import dispatch_job, load_jobs, load_vehicles, lookup_rule  # noqa: E402

KIND_ASSIGN = "ASSIGN"

# Recorded (vehicle_id, job_id) pairs. S-12 may consume these later.
STARTED: list[tuple[str, str]] = []


def reset_started() -> None:
    STARTED.clear()


def start_driver(vehicle_id: str, job_id: str) -> None:
    """Signal S-12. No-op if the driver module is not here yet."""
    STARTED.append((vehicle_id, job_id))
    sys.stderr.write(f"start_driver vehicle={vehicle_id} job={job_id}\n")
    try:
        from sim import driver as driver_mod
    except ImportError:
        return
    fn = getattr(driver_mod, "start_driver", None) or getattr(driver_mod, "play", None)
    if callable(fn):
        fn(vehicle_id, job_id)


def make_event(job: dict, vehicle: dict, kind: str, dsp_ids: list[str]) -> dict:
    quotes = {dsp_id: lookup_rule(dsp_id) for dsp_id in dsp_ids}
    return {
        "job_id": job.get("id"),
        "city": job.get("city"),
        "km": job.get("km"),
        "vehicle_id": vehicle.get("id"),
        "kind": kind,
        "dsp_ids": list(dsp_ids),
        "quotes": quotes,
    }


def collect_events(*, start: bool = True) -> list[dict]:
    """Six DispatchEvents, roster order, both jobs. Does not touch the roster."""
    jobs = load_jobs()
    vehicles = load_vehicles()
    events: list[dict] = []
    for job in jobs:
        for kind, vehicle, dsp_ids in dispatch_job(job, vehicles):
            events.append(make_event(job, vehicle, kind, dsp_ids))
            if start and kind == KIND_ASSIGN:
                start_driver(str(vehicle.get("id") or ""), str(job.get("id") or ""))
    return events


def write_fixture(events: list[dict], path: Path = FIXTURE) -> None:
    payload = {
        "note": "Fixture for S-10/S-11/S-12. Kept in sync with src/dispatcher.py + src/dispatch.py.",
        "events": events,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dispatcher agent")
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Emit events without calling start_driver",
    )
    parser.add_argument(
        "--write-fixture",
        action="store_true",
        help="Rewrite pipelines/fixtures/dispatch_events.json from the engine",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    reset_started()
    events = collect_events(start=not args.no_start)
    if args.write_fixture:
        write_fixture(events)
    json.dump({"events": events, "started_drivers": [list(p) for p in STARTED]}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
