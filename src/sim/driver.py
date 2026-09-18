"""Electric driver playback after ASSIGN. Not a dispatch rule. Not an assigner."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent.parent
LOCATIONS_PATH = ROOT / ".docs" / "reference" / "locations.json"
FIXTURE_PATH = ROOT / "pipelines" / "fixtures" / "dispatch_events.json"

VEHICLE_ID = "T-11"
BATTERY_KWH = 90.0
KWH_PER_KM = 0.5
SPEED_KMH = 70
DRIVE_POWER_KW = 35.0
JUNCTION_EVERY_KM = 10
MS_PER_KM = 50
JUNCTION_WALL_S = 0.25
CHARGE_TICK_KWH = 5.0
CHARGE_TICK_WALL_S = 0.4

TELEMETRY_KEYS = (
    "vehicle_id",
    "job_id",
    "status",
    "speed_kmh",
    "drive_power_kw",
    "soc_pct",
    "range_km",
    "km_from_garage",
    "charger_id",
    "charger_power_kw",
)


class Clock:
    def __init__(self, realtime: bool = False) -> None:
        self.realtime = realtime

    def km(self) -> None:
        if self.realtime:
            time.sleep(MS_PER_KM / 1000.0)

    def junction(self) -> None:
        if self.realtime:
            time.sleep(JUNCTION_WALL_S)

    def charge_tick(self) -> None:
        if self.realtime:
            time.sleep(CHARGE_TICK_WALL_S)


def load_locations(path: Path | None = None) -> dict:
    return json.loads((path or LOCATIONS_PATH).read_text(encoding="utf-8"))


def load_dispatch_events(path: Path | None = None) -> list[dict]:
    payload = json.loads((path or FIXTURE_PATH).read_text(encoding="utf-8"))
    return list(payload.get("events") or payload)


def range_km(energy_kwh: float) -> float:
    return round(max(0.0, energy_kwh) / KWH_PER_KM, 1)


def soc_pct(energy_kwh: float) -> float:
    return round(max(0.0, energy_kwh) / BATTERY_KWH * 100.0, 1)


def city_km_from_garage(locations: dict, city: str) -> int:
    for row in locations["cities"]:
        if row["id"] == city:
            return int(row["km_from_garage"])
    raise KeyError(city)


def nearest_charger(locations: dict, city: str, remaining_km: float) -> dict | None:
    reachable = [
        station
        for station in locations["charging_stations"]
        if station["km_from"][city] <= remaining_km
    ]
    if not reachable:
        return None
    return min(reachable, key=lambda station: station["km_from"][city])


def telemetry(
    *,
    job_id: str,
    status: str,
    energy_kwh: float,
    km_from_garage: float,
    moving: bool,
    charger_id: str | None = None,
    charger_power_kw: float | None = None,
) -> dict:
    return {
        "vehicle_id": VEHICLE_ID,
        "job_id": job_id,
        "status": status,
        "speed_kmh": SPEED_KMH if moving else 0,
        "drive_power_kw": DRIVE_POWER_KW if moving else 0,
        "soc_pct": soc_pct(energy_kwh),
        "range_km": range_km(energy_kwh),
        "km_from_garage": float(km_from_garage),
        "charger_id": charger_id,
        "charger_power_kw": charger_power_kw,
    }


def _drive_leg(
    *,
    job_id: str,
    status: str,
    energy: float,
    start_pos: float,
    distance_km: int,
    direction: int,
    clock: Clock,
    charger_id: str | None = None,
) -> Iterator[tuple[dict, float, float]]:
    pos = start_pos
    for step in range(1, distance_km + 1):
        energy = max(0.0, energy - KWH_PER_KM)
        pos = start_pos + direction * step
        yield (
            telemetry(
                job_id=job_id,
                status=status,
                energy_kwh=energy,
                km_from_garage=pos,
                moving=True,
                charger_id=charger_id,
            ),
            energy,
            pos,
        )
        clock.km()
        if step % JUNCTION_EVERY_KM == 0 and step != distance_km:
            yield (
                telemetry(
                    job_id=job_id,
                    status="junction_stop",
                    energy_kwh=energy,
                    km_from_garage=pos,
                    moving=False,
                    charger_id=charger_id,
                ),
                energy,
                pos,
            )
            clock.junction()


def play_job(
    event: dict,
    locations: dict | None = None,
    clock: Clock | None = None,
) -> Iterator[dict]:
    if event.get("kind") != "ASSIGN" or event.get("vehicle_id") != VEHICLE_ID:
        return
    locations = locations or load_locations()
    clock = clock or Clock(realtime=False)
    job_id = event["job_id"]
    city = event["city"]
    trip_km = int(event["km"])
    home_km = city_km_from_garage(locations, city)
    energy = BATTERY_KWH
    pos = 0.0

    for tick, energy, pos in _drive_leg(
        job_id=job_id,
        status="en_route",
        energy=energy,
        start_pos=0.0,
        distance_km=trip_km,
        direction=1,
        clock=clock,
    ):
        yield tick

    yield telemetry(
        job_id=job_id,
        status="delivered",
        energy_kwh=energy,
        km_from_garage=pos,
        moving=False,
    )

    if range_km(energy) >= home_km:
        for tick, energy, pos in _drive_leg(
            job_id=job_id,
            status="returning",
            energy=energy,
            start_pos=pos,
            distance_km=trip_km,
            direction=-1,
            clock=clock,
        ):
            yield tick
        return

    charger = nearest_charger(locations, city, range_km(energy))
    if charger is None:
        return
    divert_km = int(charger["km_from"][city])
    for tick, energy, pos in _drive_leg(
        job_id=job_id,
        status="divert_charge",
        energy=energy,
        start_pos=pos,
        distance_km=divert_km,
        direction=0,
        clock=clock,
        charger_id=charger["id"],
    ):
        yield tick

    need_kwh = home_km * KWH_PER_KM
    while energy + 1e-9 < need_kwh:
        energy = min(BATTERY_KWH, energy + min(CHARGE_TICK_KWH, need_kwh - energy))
        yield telemetry(
            job_id=job_id,
            status="charging",
            energy_kwh=energy,
            km_from_garage=pos,
            moving=False,
            charger_id=charger["id"],
            charger_power_kw=charger["power_kw"],
        )
        clock.charge_tick()

    for tick, energy, pos in _drive_leg(
        job_id=job_id,
        status="returning",
        energy=energy,
        start_pos=home_km,
        distance_km=trip_km,
        direction=-1,
        clock=clock,
    ):
        yield tick


def iter_telemetry(
    events: list[dict] | None = None,
    locations: dict | None = None,
    realtime: bool = False,
) -> Iterator[dict]:
    locations = locations or load_locations()
    clock = Clock(realtime=realtime)
    for event in events if events is not None else load_dispatch_events():
        yield from play_job(event, locations, clock)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(a in ("-h", "--help") for a in argv):
        sys.stdout.write(
            "python src/sim/driver.py [J-01|J-02] [--no-sleep]\n"
        )
        return 0
    realtime = "--no-sleep" not in argv
    job_id = next((a for a in argv if a.startswith("J-")), None)
    events = load_dispatch_events()
    if job_id:
        events = [event for event in events if event.get("job_id") == job_id]
    for tick in iter_telemetry(events, realtime=realtime):
        sys.stdout.write(json.dumps(tick) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
