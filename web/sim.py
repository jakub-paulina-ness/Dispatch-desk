#!/usr/bin/env python3
"""Session yard simulation. Kit files are never written."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOCATIONS_PATH = ROOT / ".docs" / "reference" / "locations.json"
CORRIDOR_KM = 160.0
KWH_PER_KM = 0.5

VIEW = (1000, 520)
YARD = (792.0, 292.0)
CLUJ = (760.0, 210.0)
CLUJ_DROP = (838.0, 148.0)
ORADEA = (92.0, 208.0)
ORADEA_DROP = (64.0, 168.0)
T14_POS = (318.0, 172.0)
T12_POS = (708.0, 168.0)
LOCATIONS: dict[str, Any] = {}
CHARGERS: list[dict] = []
CITIES: list[dict] = []

CORRIDOR = [
    (64.0, 168.0),
    (92.0, 208.0),
    (170.0, 198.0),
    (250.0, 182.0),
    (318.0, 172.0),
    (390.0, 178.0),
    (456.0, 198.0),
    (540.0, 214.0),
    (640.0, 236.0),
    (720.0, 258.0),
    (760.0, 210.0),
    (792.0, 292.0),
]

CLUJ_LOOP = [
    (792.0, 292.0),
    (820.0, 240.0),
    (838.0, 148.0),
    (780.0, 128.0),
    (720.0, 158.0),
    (708.0, 168.0),
    (740.0, 210.0),
    (792.0, 292.0),
]

LAND = [[(0, 90), (220, 50), (520, 36), (820, 58), (1000, 80), (1000, 520), (0, 520)]]
RIVER = [(20, 250), (180, 228), (360, 208), (560, 236), (760, 268), (1000, 300)]

CRUISE_KMH = 80.0
VAN_KMH = 140.0
CHARGE_KMH = 320.0
SERVICE_S = 18 * 60
DWELL_S = 90.0
SHIFT_START_S = 6 * 3600
SHIFT_LEN_S = 10 * 3600
SIM_PER_WALL_1X = 90.0
RETURN_KM = {"Cluj": 8.0, "Oradea": 160.0}
DEST = {"Cluj": CLUJ_DROP, "Oradea": ORADEA_DROP}


def _hypot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def path_len(points: list[tuple[float, float]]) -> float:
    return sum(_hypot(points[i - 1], points[i]) for i in range(1, len(points)))


PX_PER_KM = path_len(CORRIDOR) / 160.0


def km_of_path(points: list[tuple[float, float]]) -> float:
    return path_len(points) / PX_PER_KM if PX_PER_KM else 0.0


def point_along(points: list[tuple[float, float]], t: float) -> tuple[float, float]:
    if not points:
        return (0.0, 0.0)
    if len(points) == 1 or t <= 0:
        return points[0]
    if t >= 1:
        return points[-1]
    lengths = [_hypot(points[i - 1], points[i]) for i in range(1, len(points))]
    total = sum(lengths) or 1.0
    target = t * total
    acc = 0.0
    for i, length in enumerate(lengths):
        if acc + length >= target:
            u = 0.0 if length == 0 else (target - acc) / length
            a, b = points[i], points[i + 1]
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        acc += length
    return points[-1]


def point_at_km(km: float) -> tuple[float, float]:
    # Corridor is drawn Oradea (160 km) → garage (0 km). No lat/lon.
    t = 1.0 - (max(0.0, min(CORRIDOR_KM, float(km))) / CORRIDOR_KM)
    return point_along(CORRIDOR, t)


def charge_kmh(power_kw: float | None) -> float:
    if not power_kw:
        return CHARGE_KMH
    return float(power_kw) / KWH_PER_KM


def load_locations(path: Path | None = None) -> dict:
    return json.loads((path or LOCATIONS_PATH).read_text(encoding="utf-8"))


def _station_km(station: dict, city_km: dict) -> float:
    cluj_d = float(station["km_from"]["Cluj"])
    oradea_d = float(station["km_from"]["Oradea"])
    if cluj_d <= oradea_d:
        km = city_km["Cluj"] + cluj_d
        if km > city_km["Oradea"]:
            km = city_km["Cluj"] - cluj_d
        return km
    return city_km["Oradea"] - oradea_d


def apply_locations(path: Path | None = None) -> dict:
    """Pin cities/chargers from locations.json onto the corridor. Sim-only."""
    global LOCATIONS, CHARGERS, CITIES, YARD, CLUJ, ORADEA, CLUJ_DROP, ORADEA_DROP, DEST, RETURN_KM
    loc = load_locations(path)
    LOCATIONS = loc
    city_km = {row["id"]: float(row["km_from_garage"]) for row in loc["cities"]}
    garage = loc["garage"]
    YARD = point_at_km(float(garage.get("km_from_garage") or 0))
    CLUJ = point_at_km(city_km["Cluj"])
    ORADEA = point_at_km(city_km["Oradea"])
    CLUJ_DROP = (CLUJ[0] + 78.0, CLUJ[1] - 62.0)
    ORADEA_DROP = (ORADEA[0] - 28.0, ORADEA[1] - 40.0)
    DEST = {"Cluj": CLUJ_DROP, "Oradea": ORADEA_DROP}
    RETURN_KM = {"Cluj": 8.0, "Oradea": city_km["Oradea"]}
    CITIES = [
        {
            "id": "oradea",
            "name": "Oradea",
            "x": ORADEA[0],
            "y": ORADEA[1],
            "sub": f"J-02 · {int(city_km['Oradea'])} km",
            "km_from_garage": city_km["Oradea"],
        },
        {
            "id": "cluj",
            "name": "Cluj",
            "x": CLUJ[0],
            "y": CLUJ[1],
            "sub": f"J-01 · {int(city_km['Cluj'])} km",
            "km_from_garage": city_km["Cluj"],
        },
        {
            "id": "yard",
            "name": garage.get("name") or "Garage",
            "x": YARD[0],
            "y": YARD[1],
            "sub": f"{garage.get('id', 'G-0')} · {int(garage.get('power_kw') or 22)} kW",
            "km_from_garage": float(garage.get("km_from_garage") or 0),
        },
    ]
    chargers = [
        {
            "id": str(garage["id"]),
            "name": str(garage.get("name") or "Garage"),
            "x": YARD[0] + 32.0,
            "y": YARD[1] + 36.0,
            "place": "Garage",
            "power_kw": int(garage.get("power_kw") or 22),
            "km_from_garage": float(garage.get("km_from_garage") or 0),
            "reachable": True,
        }
    ]
    for station in loc.get("charging_stations") or []:
        km = _station_km(station, city_km)
        nearest = min(float(v) for v in station["km_from"].values())
        reachable = nearest <= CORRIDOR_KM
        if reachable and 0 <= km <= CORRIDOR_KM:
            x, y = point_at_km(km)
        else:
            x, y = 36.0, 64.0
            reachable = False
        nearer = "Cluj" if station["km_from"]["Cluj"] <= station["km_from"]["Oradea"] else "Oradea"
        chargers.append(
            {
                "id": str(station["id"]),
                "name": str(station["name"]),
                "x": x,
                "y": y,
                "place": nearer,
                "power_kw": int(station.get("power_kw") or 0),
                "km_from": dict(station["km_from"]),
                "km_from_garage": km,
                "reachable": reachable,
            }
        )
    CHARGERS = chargers
    return loc


def nearest_index(points: list[tuple[float, float]], p: tuple[float, float]) -> int:
    return min(range(len(points)), key=lambda i: _hypot(points[i], p))


def via(backbone: list[tuple[float, float]], start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
    if _hypot(start, end) < 48:
        return [start, end]
    i = nearest_index(backbone, start)
    j = nearest_index(backbone, end)
    mid = backbone[i : j + 1] if i <= j else list(reversed(backbone[j : i + 1]))
    path = [start]
    for q in mid:
        if _hypot(path[-1], q) > 2:
            path.append(q)
    if _hypot(path[-1], end) > 2:
        path.append(end)
    if len(path) < 2:
        path = [start, end]
    return path


def route(start: tuple[float, float], end: tuple[float, float], city: str | None = None) -> list[tuple[float, float]]:
    if city == "Cluj":
        return via(CLUJ_LOOP, start, end)
    return via(CORRIDOR, start, end)


def charger_by_id(charger_id: str | None) -> dict | None:
    for row in CHARGERS:
        if row["id"] == charger_id:
            return row
    return None


def charger_km(v: dict, row: dict, path: list[tuple[float, float]]) -> float:
    pixel = max(0.4, km_of_path(path))
    km_from = row.get("km_from") or {}
    here = place_name(v["x"], v["y"]).lower()
    for city, dist in km_from.items():
        if city.lower() in here:
            return max(0.4, float(dist))
    if ("yard" in here or "garage" in here) and row.get("km_from_garage") is not None:
        return max(0.4, abs(float(row["km_from_garage"])))
    return pixel


def nearest_charger(x: float, y: float) -> dict:
    here = (x, y)
    reachable = [row for row in CHARGERS if row.get("reachable", True)]
    pool = reachable or CHARGERS
    return min(pool, key=lambda row: _hypot(here, (row["x"], row["y"])))


def place_name(x: float, y: float) -> str:
    here = (x, y)
    spots = [
        (YARD, "Cluj yard"),
        (CLUJ_DROP, "Cluj drop-off"),
        (CLUJ, "Cluj"),
        (ORADEA_DROP, "Oradea drop-off"),
        (ORADEA, "Oradea"),
        (T14_POS, "Corridor west"),
    ]
    for row in CHARGERS:
        spots.append(((row["x"], row["y"]), row["name"]))
    spot, name = min(spots, key=lambda item: _hypot(here, item[0]))
    if _hypot(here, spot) < 36:
        return name
    if x < 280:
        return "West corridor"
    if x > 680:
        return "Cluj area"
    return "Corridor"


def clock_str(sim_s: float) -> str:
    total = int(SHIFT_START_S + sim_s)
    hours = (total // 3600) % 24
    mins = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def heading_of(prev: tuple[float, float], cur: tuple[float, float], fallback: float) -> float:
    if _hypot(prev, cur) < 0.4:
        return fallback
    return math.degrees(math.atan2(cur[1] - prev[1], cur[0] - prev[0]))


S: dict[str, Any] = {}

SPEEDS = (0, 0.5, 1, 4, 16)
DEFAULT_SPEED = 1.0


def as_speed(value: Any, fallback: float = DEFAULT_SPEED) -> float:
    try:
        speed = float(value)
    except (TypeError, ValueError):
        return fallback
    for allowed in SPEEDS:
        if abs(speed - allowed) < 1e-9:
            return float(allowed)
    return fallback


def reset(speed: float | None = None) -> None:
    keep = as_speed(speed, as_speed(S.get("speed"), DEFAULT_SPEED)) if speed is not None else as_speed(S.get("speed"), DEFAULT_SPEED)
    S.clear()
    S.update(
        {
            "sim_s": 0.0,
            "speed": keep,
            "last_wall": None,
            "vehicles": {
                "T-11": _unit("T-11", YARD, 180.0, oos=False, hours=True, activity="idle"),
                "T-12": _unit("T-12", T12_POS, 90.0, oos=False, hours=True, activity="en_route"),
                "T-14": _unit("T-14", T14_POS, 200.0, oos=True, hours=False, activity="stranded"),
            },
            "van": {
                "id": "crew",
                "active": False,
                "x": YARD[0],
                "y": YARD[1],
                "heading": -40.0,
                "queue": [],
                "target": None,
                "trail": [],
            },
            "jobs": {
                "J-01": {"state": "open", "vehicle_id": None},
                "J-02": {"state": "open", "vehicle_id": None},
            },
            "events": [],
            "undo": [],
        }
    )
    S["vehicles"]["T-11"]["schedule"] = [_sked("On shift · Cluj yard", "idle")]
    S["vehicles"]["T-12"]["schedule"] = [_sked("On run · Cluj (kit: busy)", "job")]
    S["vehicles"]["T-14"]["schedule"] = [_sked("Out of service · corridor", "red")]
    t12 = S["vehicles"]["T-12"]
    t12["queue"] = [
        {
            "kind": "drive",
            "path": via(CLUJ_LOOP, T12_POS, CLUJ_DROP),
            "km": 18.0,
            "done": 0.0,
            "label": "On run · Cluj",
        },
        {"kind": "dwell", "s": DWELL_S, "done_s": 0.0, "label": "Unload Cluj"},
        {
            "kind": "drive",
            "path": via(CLUJ_LOOP, CLUJ_DROP, YARD),
            "km": 12.0,
            "done": 0.0,
            "returning": True,
            "label": "Return to Cluj yard",
        },
    ]
    t12["heading"] = -20.0
    t12["work"] = _work_from(t12)
    emit("Shift open. T-11 at yard. T-12 already on a Cluj run. T-14 out of service.", "info")


def _unit(
    vid: str,
    pos: tuple[float, float],
    range_km: float,
    oos: bool,
    hours: bool,
    activity: str,
) -> dict:
    return {
        "id": vid,
        "x": pos[0],
        "y": pos[1],
        "heading": 0.0,
        "range_km": float(range_km),
        "range_full": float(range_km),
        "oos": oos,
        "hours_flag": hours,
        "activity": activity,
        "job_id": None,
        "queue": [],
        "trail": [list(pos)],
        "schedule": [],
        "work": {
            "title": "Waiting at Cluj yard" if vid == "T-11" else "Out of service",
            "detail": "",
            "progress": 0.0,
            "km_done": 0.0,
            "km_left": 0.0,
        },
    }


def _sked(label: str, kind: str) -> dict:
    return {"clock": clock_str(S.get("sim_s", 0.0)), "sim_s": S.get("sim_s", 0.0), "label": label, "kind": kind}


def add_sked(vid: str, label: str, kind: str) -> None:
    S["vehicles"][vid]["schedule"].append(_sked(label, kind))


def emit(text: str, tone: str = "info") -> None:
    S["events"].insert(0, {"clock": clock_str(S["sim_s"]), "text": text, "tone": tone})
    S["events"] = S["events"][:48]


def vehicle(vid: str) -> dict | None:
    return S["vehicles"].get(vid)


def van() -> dict:
    return S["van"]


def jobs() -> dict:
    return S["jobs"]


def shift_ok() -> bool:
    return S["sim_s"] < SHIFT_LEN_S


def hours_ok(v: dict) -> bool:
    # Kit/session flag only. Clock is atmospheric; a turbo demo must not fail DSP-1.
    return bool(v["hours_flag"])


def dsp_status(v: dict) -> str:
    if v["oos"] or v["range_km"] <= 0.5:
        return "red"
    if v["queue"] or v["activity"] in {"en_route", "dwelling", "returning", "charging", "servicing"}:
        return "busy"
    return "free"


def live(vid: str) -> dict | None:
    v = vehicle(vid)
    if v is None:
        return None
    return {
        "status": dsp_status(v),
        "hours_ok": hours_ok(v),
        "range_km": int(v["range_km"]),
    }


def fleet() -> dict[str, dict]:
    return {vid: live(vid) for vid in S["vehicles"] if live(vid)}


def busy_ids() -> set[str]:
    return {vid for vid, row in S["vehicles"].items() if dsp_status(row) == "busy"}


def activity_label(v: dict) -> str:
    act = v["activity"]
    task = v["queue"][0] if v["queue"] else None
    label = task["label"] if task else ""
    if v["oos"] and act != "servicing":
        return f"Out of service · {place_name(v['x'], v['y'])}"
    if act == "idle":
        return f"Waiting · {place_name(v['x'], v['y'])}"
    if act == "en_route":
        return label or "En route"
    if act == "returning":
        return label or "Returning to yard"
    if act == "dwelling":
        return label or "On site"
    if act == "charging":
        return f"Charging · {place_name(v['x'], v['y'])}"
    if act == "servicing":
        return "Yard service on site"
    if act == "stranded":
        return f"Stranded · {place_name(v['x'], v['y'])}"
    return label or act


def eta_free_s(v: dict) -> float:
    t = 0.0
    range_now = v["range_km"]
    for task in v["queue"]:
        kind = task["kind"]
        if kind == "drive":
            left = max(0.0, task["km"] - task["done"])
            t += left / (CRUISE_KMH / 3600.0)
        elif kind in {"dwell", "service"}:
            t += max(0.0, task["s"] - task.get("done_s", 0.0))
        elif kind == "charge":
            need = max(0.0, v["range_full"] - range_now)
            rate = charge_kmh(task.get("power_kw"))
            t += need / (rate / 3600.0) if rate else 0.0
            range_now = v["range_full"]
    return t


def _work_from(v: dict) -> dict:
    task = v["queue"][0] if v["queue"] else None
    if not task:
        return {
            "title": activity_label(v),
            "detail": "Range holds while idle.",
            "progress": 0.0,
            "km_done": 0.0,
            "km_left": 0.0,
        }
    if task["kind"] == "drive":
        prog = task["done"] / task["km"] if task["km"] else 1.0
        return {
            "title": task["label"],
            "detail": f"{task['done']:.0f} / {task['km']:.0f} km · range draining",
            "progress": prog,
            "km_done": task["done"],
            "km_left": max(0.0, task["km"] - task["done"]),
        }
    if task["kind"] in {"dwell", "service"}:
        prog = task.get("done_s", 0.0) / task["s"] if task["s"] else 1.0
        return {
            "title": task["label"],
            "detail": "Stopped. Range holds.",
            "progress": prog,
            "km_done": 0.0,
            "km_left": 0.0,
        }
    if task["kind"] == "charge":
        prog = v["range_km"] / v["range_full"] if v["range_full"] else 1.0
        return {
            "title": task["label"],
            "detail": f"Range {v['range_km']:.0f} / {v['range_full']:.0f} km",
            "progress": prog,
            "km_done": 0.0,
            "km_left": 0.0,
        }
    return {"title": task.get("label") or "", "detail": "", "progress": 0.0, "km_done": 0.0, "km_left": 0.0}


def trail_push(holder: dict, pos: tuple[float, float]) -> None:
    trail = holder["trail"]
    if not trail or _hypot((trail[-1][0], trail[-1][1]), pos) >= 6:
        trail.append([pos[0], pos[1]])
    holder["trail"] = trail[-48:]


def _finish_job_if_idle(v: dict) -> None:
    if v["job_id"] and not v["queue"]:
        jid = v["job_id"]
        job = S["jobs"].get(jid)
        if job:
            job["state"] = "done"
        emit(f"{v['id']} completed {jid}. Standing by · {place_name(v['x'], v['y'])}.", "assign")
        add_sked(v["id"], f"Completed {jid}", "idle")
        v["job_id"] = None
        v["activity"] = "idle"


def _drive_step(holder: dict, task: dict, dt: float, speed_kmh: float, drain: bool) -> None:
    left = max(0.0, task["km"] - task["done"])
    step = min(left, (speed_kmh / 3600.0) * dt)
    if drain:
        vrange = holder.get("range_km", 0.0)
        going_to_charge = any(item.get("kind") == "charge" for item in holder.get("queue") or [])
        if vrange <= 0.05 and not going_to_charge:
            holder["oos"] = True
            holder["activity"] = "stranded"
            holder["queue"] = []
            emit(f"{holder.get('id', 'Unit')} range depleted. Out of service.", "refuse")
            add_sked(holder["id"], "Range depleted · out of service", "red")
            return
        if not going_to_charge:
            step = min(step, vrange)
        holder["range_km"] = max(0.0, vrange - min(step, vrange))
    if step <= 0:
        return
    task["done"] += step
    t = 1.0 if task["km"] <= 0 else min(1.0, task["done"] / task["km"])
    prev = (holder["x"], holder["y"])
    nxt = point_along(task["path"], t)
    holder["x"], holder["y"] = nxt
    holder["heading"] = heading_of(prev, nxt, holder.get("heading", 0.0))
    trail_push(holder, nxt)
    if drain:
        holder["activity"] = "returning" if task.get("returning") else "en_route"
    if task["done"] >= task["km"] - 1e-6:
        holder["queue"].pop(0)


def _tick_vehicle(v: dict, dt: float) -> None:
    if not v["queue"]:
        if v["oos"]:
            v["activity"] = "stranded"
        else:
            v["activity"] = "idle"
        _finish_job_if_idle(v)
        v["work"] = _work_from(v)
        return
    task = v["queue"][0]
    kind = task["kind"]
    if kind == "drive":
        _drive_step(v, task, dt, CRUISE_KMH, drain=True)
    elif kind in {"dwell", "service"}:
        v["activity"] = "servicing" if kind == "service" else "dwelling"
        task["done_s"] = task.get("done_s", 0.0) + dt
        if task["done_s"] >= task["s"]:
            v["queue"].pop(0)
            if kind == "service":
                v["oos"] = False
                v["hours_flag"] = True
                v["range_km"] = v["range_full"]
                v["activity"] = "idle"
                emit(f"{v['id']} back in service. hours_ok true · range {int(v['range_km'])} km.", "assign")
                add_sked(v["id"], "Returned to service", "idle")
    elif kind == "charge":
        v["activity"] = "charging"
        rate = charge_kmh(task.get("power_kw"))
        v["range_km"] = min(v["range_full"], v["range_km"] + (rate / 3600.0) * dt)
        if v["range_km"] >= v["range_full"] - 0.05:
            v["range_km"] = v["range_full"]
            v["queue"].pop(0)
            emit(f"{v['id']} charge complete · {int(v['range_km'])} km.", "assign")
            add_sked(v["id"], "Charge complete", "charge")
    v["work"] = _work_from(v)


def _tick_van(dt: float) -> None:
    van_row = S["van"]
    if not van_row["active"]:
        return
    if not van_row["queue"]:
        target = van_row.get("target")
        unit = vehicle(target) if target else None
        if unit and unit["oos"] and (not unit["queue"] or unit["queue"][0]["kind"] != "service"):
            unit["queue"] = [{"kind": "service", "s": SERVICE_S, "done_s": 0.0, "label": "Yard service on site"}]
            add_sked(unit["id"], "Yard crew on site", "red")
            emit(f"Yard crew on site at {target}.", "info")
            van_row["queue"] = [
                {"kind": "dwell", "s": SERVICE_S, "done_s": 0.0, "label": "On site"},
                {
                    "kind": "drive",
                    "path": via(CORRIDOR, (van_row["x"], van_row["y"]), YARD),
                    "km": km_of_path(via(CORRIDOR, (van_row["x"], van_row["y"]), YARD)),
                    "done": 0.0,
                    "returning": True,
                    "label": "Crew return to yard",
                },
            ]
            return
        if van_row["queue"]:
            return
        van_row["active"] = False
        van_row["target"] = None
        van_row["x"], van_row["y"] = YARD
        emit("Yard crew back at Cluj yard.", "info")
        return
    task = van_row["queue"][0]
    if task["kind"] == "drive":
        _drive_step(van_row, task, dt, VAN_KMH, drain=False)
    elif task["kind"] == "dwell":
        task["done_s"] = task.get("done_s", 0.0) + dt
        if task["done_s"] >= task["s"]:
            van_row["queue"].pop(0)


def advance(dt: float) -> None:
    if dt <= 0:
        return
    # Step in slices so fast-forward still hits arrivals.
    left = dt
    while left > 0:
        slice_s = min(0.5, left)
        for v in S["vehicles"].values():
            _tick_vehicle(v, slice_s)
        _tick_van(slice_s)
        S["sim_s"] += slice_s
        left -= slice_s


def sync_wall(now: float) -> None:
    last = S.get("last_wall")
    S["last_wall"] = now
    if last is None:
        return
    speed = as_speed(S.get("speed"), 0)
    if speed <= 0:
        return
    wall = max(0.0, now - last)
    wall = min(wall, 0.25)
    dt = wall * speed * SIM_PER_WALL_1X
    advance(dt)


def set_speed(speed: float) -> None:
    S["speed"] = as_speed(speed, DEFAULT_SPEED)
    S["last_wall"] = None


def push_undo() -> None:
    S["undo"].append(
        {
            "vehicles": copy.deepcopy(S["vehicles"]),
            "van": copy.deepcopy(S["van"]),
            "jobs": copy.deepcopy(S["jobs"]),
        }
    )
    S["undo"] = S["undo"][-20:]


def undo() -> dict | None:
    if not S["undo"]:
        return None
    snap = S["undo"].pop()
    S["vehicles"] = snap["vehicles"]
    S["van"] = snap["van"]
    S["jobs"] = snap["jobs"]
    return snap


def can_undo() -> bool:
    return bool(S["undo"])


def return_km_for(city: str) -> float:
    return RETURN_KM.get(city, 8.0)


def warnings_for(job: dict | None, vid: str | None) -> list[str]:
    notes: list[str] = []
    if not job or not vid:
        return notes
    v = vehicle(vid)
    if v is None or dsp_status(v) != "free":
        return notes
    need = float(job.get("km") or 0)
    ret = return_km_for(str(job.get("city") or ""))
    remain = v["range_km"] - need
    if remain < ret:
        charger = nearest_charger(DEST.get(str(job.get("city") or ""), YARD)[0], DEST.get(str(job.get("city") or ""), YARD)[1])
        notes.append(
            f"{vid} would arrive with ~{max(0, int(remain))} km. "
            f"Return to yard needs {int(ret)} km. Plan {charger['id']} ({charger['power_kw']} kW)."
        )
    return notes


def ops(vid: str) -> dict:
    v = vehicle(vid)
    if v is None:
        return {
            "can_service": False,
            "can_charge": False,
            "can_return": False,
            "nearest_charger": None,
            "charge_advice": "",
        }
    st = dsp_status(v)
    freeish = st == "free" and not v["queue"]
    charger = nearest_charger(v["x"], v["y"])
    van_busy_for = S["van"]["active"] and S["van"].get("target") == vid
    advice = ""
    if st != "red" and v["range_km"] < max(40.0, 0.35 * v["range_full"]):
        advice = f"Range {int(v['range_km'])} km. Nearest charger: {charger['name']}."
    at_yard = _hypot((v["x"], v["y"]), YARD) < 28
    return_path = via(CORRIDOR, (v["x"], v["y"]), YARD)
    need_home = km_of_path(return_path)
    return {
        "can_service": st == "red" and v["activity"] != "servicing" and not van_busy_for,
        "can_charge": freeish and v["range_km"] < v["range_full"] - 1,
        "can_return": freeish and not at_yard and v["range_km"] > need_home + 1,
        "nearest_charger": charger,
        "charge_advice": advice,
        "return_km": round(need_home, 1),
        "at_yard": at_yard,
    }


def assign_job(vid: str, job: dict) -> dict:
    v = vehicle(vid)
    if v is None:
        return {"ok": False, "error": "Vehicle is not in vehicles.json."}
    if dsp_status(v) != "free":
        return {"ok": False, "error": "Vehicle is not free."}
    jid = job["id"]
    if S["jobs"].get(jid, {}).get("state") != "open":
        return {"ok": False, "error": "Job is not open."}
    dest = DEST[job["city"]]
    city = job["city"]
    start = (v["x"], v["y"])
    outbound = route(start, dest, city)
    ret_km = return_km_for(city)
    remain = v["range_km"] - float(job["km"])
    queue: list[dict] = [
        {
            "kind": "drive",
            "path": outbound,
            "km": float(job["km"]),
            "done": 0.0,
            "label": f"{jid} · {city}",
        },
        {"kind": "dwell", "s": DWELL_S, "done_s": 0.0, "label": f"Unload {city}"},
    ]
    if remain > ret_km + 2:
        queue.append(
            {
                "kind": "drive",
                "path": route(dest, YARD, city if city == "Cluj" else None),
                "km": ret_km,
                "done": 0.0,
                "returning": True,
                "label": "Return to Cluj yard",
            }
        )
    push_undo()
    v["job_id"] = jid
    v["queue"] = queue
    v["activity"] = "en_route"
    S["jobs"][jid] = {"state": "assigned", "vehicle_id": vid}
    add_sked(vid, f"Sent on {jid} · {city}", "job")
    emit(f"{vid} left {place_name(v['x'], v['y'])} · {jid} {city} {job['km']} km.", "assign")
    v["work"] = _work_from(v)
    return {"ok": True}


def call_service(vid: str) -> dict:
    v = vehicle(vid)
    if v is None:
        return {"ok": False, "error": "Vehicle is not in vehicles.json."}
    if dsp_status(v) != "red":
        return {"ok": False, "error": "Yard service is only for out-of-service vehicles."}
    if v["activity"] == "servicing":
        return {"ok": False, "error": "Yard crew is already on site."}
    if S["van"]["active"]:
        return {"ok": False, "error": "Yard crew is already out."}
    start = YARD
    dest = (v["x"], v["y"])
    path = via(CORRIDOR, start, dest)
    push_undo()
    S["van"] = {
        "id": "crew",
        "active": True,
        "x": start[0],
        "y": start[1],
        "heading": heading_of(start, dest, -40.0),
        "queue": [
            {
                "kind": "drive",
                "path": path,
                "km": max(1.0, km_of_path(path)),
                "done": 0.0,
                "label": f"Service {vid}",
            }
        ],
        "target": vid,
        "trail": [list(start)],
    }
    add_sked(vid, "Yard crew dispatched", "red")
    emit(f"Yard crew rolling from Cluj yard to {vid}. Not a roster vehicle.", "info")
    return {"ok": True}


def send_charge(vid: str, charger_id: str | None) -> dict:
    v = vehicle(vid)
    if v is None:
        return {"ok": False, "error": "Vehicle is not in vehicles.json."}
    if dsp_status(v) == "red":
        return {"ok": False, "error": "Out of service. Call yard service first."}
    if dsp_status(v) != "free":
        return {"ok": False, "error": "Vehicle is not free."}
    row = charger_by_id(charger_id) if charger_id else None
    if row is None:
        row = nearest_charger(v["x"], v["y"])
    if not row.get("reachable", True):
        return {"ok": False, "error": f"{row['id']} is out of range in locations.json."}
    dest = (row["x"], row["y"])
    path = via(CORRIDOR, (v["x"], v["y"]), dest)
    km = charger_km(v, row, path)
    if v["range_km"] + 0.5 < km:
        return {"ok": False, "error": "Range is less than the run to that charger."}
    push_undo()
    v["queue"] = [
        {"kind": "drive", "path": path, "km": km, "done": 0.0, "label": f"To {row['name']}"},
        {
            "kind": "charge",
            "label": f"Charging · {row['name']} {row.get('power_kw', 0)} kW",
            "power_kw": row.get("power_kw"),
        },
    ]
    v["activity"] = "en_route"
    add_sked(vid, f"Sent to {row['name']}", "charge")
    emit(f"{vid} sent to {row['name']}.", "info")
    v["work"] = _work_from(v)
    return {"ok": True, "charger": row}


def send_return(vid: str) -> dict:
    v = vehicle(vid)
    if v is None:
        return {"ok": False, "error": "Vehicle is not in vehicles.json."}
    if dsp_status(v) == "red":
        return {"ok": False, "error": "Out of service. Call yard service first."}
    if dsp_status(v) != "free":
        return {"ok": False, "error": "Vehicle is not free."}
    if _hypot((v["x"], v["y"]), YARD) < 28:
        return {"ok": False, "error": "Already at Cluj yard."}
    path = via(CORRIDOR, (v["x"], v["y"]), YARD)
    km = km_of_path(path)
    if v["range_km"] < km + 1:
        return {"ok": False, "error": "Range is less than the run to the yard. Send to a charger first."}
    push_undo()
    v["queue"] = [
        {
            "kind": "drive",
            "path": path,
            "km": km,
            "done": 0.0,
            "returning": True,
            "label": "Return to Cluj yard",
        }
    ]
    v["activity"] = "returning"
    add_sked(vid, "Return to Cluj yard", "job")
    emit(f"{vid} returning to Cluj yard · {km:.0f} km.", "info")
    v["work"] = _work_from(v)
    return {"ok": True}


def public_vehicle(vid: str) -> dict | None:
    v = vehicle(vid)
    if v is None:
        return None
    eta = eta_free_s(v)
    task = v["queue"][0] if v["queue"] else None
    driving = bool(task and task.get("kind") == "drive" and task.get("path"))
    path = list(task["path"]) if driving else []
    moving = v["activity"] not in {"idle", "dwelling", "charging", "servicing", "stranded"}
    return {
        "id": vid,
        "status": dsp_status(v),
        "hours_ok": hours_ok(v),
        "range_km": round(v["range_km"], 1),
        "range_full": v["range_full"],
        "activity": v["activity"],
        "activity_label": activity_label(v),
        "x": v["x"],
        "y": v["y"],
        "heading": v["heading"],
        "job_id": v["job_id"],
        "work": v["work"],
        "eta_free_s": eta,
        "eta_free_clock": clock_str(S["sim_s"] + eta) if eta > 0 else clock_str(S["sim_s"]),
        "trail": v["trail"],
        "schedule": list(reversed(v["schedule"][-12:])),
        "place": place_name(v["x"], v["y"]),
        "path": path,
        "oos": v["oos"],
        "session": "sent" if any(item["kind"] == "job" for item in v["schedule"]) else "roster",
        "ops": ops(vid),
        "speed_kmh": 0.0 if not moving or not driving else CRUISE_KMH,
        "path_km": float(task["km"]) if driving else 0.0,
        "path_done": float(task.get("done") or 0.0) if driving else 0.0,
    }


def map_payload(selected_vehicle: str | None = None) -> dict:
    units = [public_vehicle(vid) for vid in ("T-11", "T-12", "T-14")]
    van_row = S["van"]
    van_pub = None
    if van_row["active"]:
        task = van_row["queue"][0] if van_row["queue"] else None
        driving = bool(task and task.get("kind") == "drive" and task.get("path"))
        van_pub = {
            "id": "crew",
            "x": van_row["x"],
            "y": van_row["y"],
            "heading": van_row["heading"],
            "target": van_row.get("target"),
            "trail": van_row.get("trail") or [],
            "label": "Yard crew",
            "path": list(task["path"]) if driving else [],
            "path_km": float(task["km"]) if driving else 0.0,
            "path_done": float(task.get("done") or 0.0) if driving else 0.0,
            "speed_kmh": VAN_KMH if driving else 0.0,
        }
    selected = public_vehicle(selected_vehicle) if selected_vehicle else None
    return {
        "view": list(VIEW),
        "corridor": CORRIDOR,
        "loop": CLUJ_LOOP,
        "land": LAND,
        "river": RIVER,
        "cities": CITIES,
        "chargers": CHARGERS,
        "vehicles": units,
        "van": van_pub,
        "px_per_km": PX_PER_KM,
        "selected_path": selected["path"] if selected else [],
        "selected_id": selected_vehicle,
        "locations_source": str(LOCATIONS_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


def sim_payload() -> dict:
    left = max(0.0, SHIFT_LEN_S - S["sim_s"])
    return {
        "clock": clock_str(S["sim_s"]),
        "sim_s": S["sim_s"],
        "speed": S["speed"],
        "sim_per_wall_1x": SIM_PER_WALL_1X,
        "shift_left_min": int(left / 60),
        "hours_ok_shift": shift_ok(),
        "night": (SHIFT_START_S + S["sim_s"]) % 86400 >= 20 * 3600 or (SHIFT_START_S + S["sim_s"]) % 86400 < 6 * 3600,
    }


apply_locations()
reset()
