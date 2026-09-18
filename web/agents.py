"""Live-yard dispatcher + driver. Engine decides; Grok speaks the tickets."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
_src = str(SRC)
if _src in sys.path:
    sys.path.remove(_src)
sys.path.insert(0, _src)

import desk  # noqa: E402
import dispatcher  # noqa: E402
import grok_llm  # noqa: E402
import sim  # noqa: E402

PLUGIN = "dispatch-desk"
DISPATCHER_SRC = ".grok/agents/dispatcher.md"
DRIVER_SRC = ".grok/agents/driver.md"

DISPATCHER_SYSTEM = """You are the Northbound fleet dispatcher, a live Grok agent on the yard radio.
You do not drive. You do not invent vehicles (no T-15) or rules (no DSP-5).
The Python engine already ran dispatch_job on the live overlay (DSP-3 then DSP-1 then DSP-2).
Follow the engine readout for kind. Copy quoted lines exactly from lookup_rule in the snapshot.
Never ASSIGN a red vehicle. T-14 is Refuse while status is red.
Human Confirm on the board is the send. You issue the ticket and a short radio line.
Reply JSON only:
{"kind":"ASSIGN|SKIP|REFUSE","decision":"Assign|Refuse","job_id":"","vehicle_id":"","rule":"","quoted":"","say":"one radio line, <= 160 chars"}
"""

DRIVER_SYSTEM = """You are the Northbound driver agent, a live Grok agent.
You do not dispatch. You do not pick a vehicle. You do not invent T-15.
If the dispatcher ticket is not Assign, or the unit is red, Decline.
If Assign and the unit is on the roster, Accept immediately.
Status comes from the live unit (idle until Confirm sends, then en_route/charging/returning).
Chargers are from locations.json, not DSP rules. After Oradea leftover ~20 km use CS-2 150 kW. Never CS-4.
Keep the ticket quoted line. Reply JSON only:
{"action":"Accept|Decline","status":"idle|en_route|delivered|returning|charging|stranded","city":"","say":"one radio line, <= 160 chars","charger_id":null,"charger_power_kw":null}
"""

_lock = threading.Lock()
_cache: dict[str, dict] = {}
_inflight: set[str] = set()

ACTIVITY_STATUS = {
    "en_route": "en_route",
    "dwelling": "delivered",
    "returning": "returning",
    "charging": "charging",
    "stranded": "stranded",
    "servicing": "idle",
    "idle": "idle",
}


def live_vehicles() -> list[dict]:
    rows = []
    for row in desk.load_vehicles():
        item = dict(row)
        overlay = sim.live(str(item.get("id") or ""))
        if overlay:
            item["status"] = overlay["status"]
            item["hours_ok"] = overlay["hours_ok"]
            item["range_km"] = overlay["range_km"]
        rows.append(item)
    return rows


def events() -> list[dict]:
    vehicles = live_vehicles()
    live_jobs = sim.jobs()
    rows: list[dict] = []
    for job in desk.load_jobs():
        state = live_jobs.get(job["id"]) or {}
        assigned_to = state.get("vehicle_id") if state.get("state") in {"assigned", "done"} else None
        for kind, vehicle, dsp_ids in dispatcher.dispatch_job(job, vehicles):
            if assigned_to:
                if vehicle["id"] == assigned_to:
                    kind, dsp_ids = "ASSIGN", ["DSP-1", "DSP-2"]
                elif kind == "ASSIGN":
                    kind, dsp_ids = "SKIP", ["DSP-1"]
            rows.append(dispatcher.make_event(job, vehicle, kind, dsp_ids))
    return rows


def find_event(
    job_id: str | None,
    vehicle_id: str | None,
    rows: list[dict] | None = None,
) -> dict | None:
    rows = events() if rows is None else rows
    if job_id and vehicle_id:
        for row in rows:
            if row["job_id"] == job_id and row["vehicle_id"] == vehicle_id:
                return row
        return None
    if job_id:
        for row in rows:
            if row["job_id"] == job_id and row["kind"] == "ASSIGN":
                return row
        for row in rows:
            if row["job_id"] == job_id:
                return row
    return None


def dispatcher_ticket(event: dict) -> dict:
    kind = str(event.get("kind") or "")
    dsp_ids = list(event.get("dsp_ids") or [])
    quotes = dict(event.get("quotes") or {})
    quoted = "\n".join(quotes[dsp] for dsp in dsp_ids if quotes.get(dsp))
    return {
        "job_id": event.get("job_id"),
        "vehicle_id": event.get("vehicle_id"),
        "city": event.get("city"),
        "km": event.get("km"),
        "kind": kind,
        "decision": "Assign" if kind == "ASSIGN" else "Refuse",
        "rule": ", ".join(dsp_ids),
        "dsp_ids": dsp_ids,
        "quotes": quotes,
        "quoted": quoted,
        "env": "live-yard",
    }


def _charger_from_live(ticket: dict, live: dict | None) -> tuple[str | None, float | None]:
    if not live:
        return None, None
    ops = live.get("ops") or {}
    nearest = ops.get("nearest_charger") or {}
    if live.get("activity") == "charging":
        cid = nearest.get("id")
        if cid == "CS-4":
            return None, None
        return cid, nearest.get("power_kw")
    job_km = float(ticket.get("km") or 0)
    range_km = float(live.get("range_km") or 0)
    city = str(ticket.get("city") or "")
    remain = range_km - job_km
    if remain < sim.return_km_for(city):
        cid = nearest.get("id")
        if cid == "CS-4":
            return None, None
        return cid, nearest.get("power_kw")
    return None, None


def driver_reply(ticket: dict | None, live: dict | None = None, job_state: str | None = None) -> dict | None:
    if not ticket:
        return None
    vid = str(ticket.get("vehicle_id") or "")
    roster = {row["id"] for row in desk.load_vehicles()}
    live = live if live is not None else (sim.public_vehicle(vid) if vid else None)
    red = bool(live and live.get("status") == "red")
    assign = ticket.get("decision") == "Assign" and vid in roster and not red
    if assign:
        if job_state in {"assigned", "done"} and live:
            status = ACTIVITY_STATUS.get(str(live.get("activity") or ""), "en_route")
        elif live:
            status = ACTIVITY_STATUS.get(str(live.get("activity") or ""), "idle")
            if job_state == "open" or not job_state:
                status = "idle"
        else:
            status = "idle"
        charger_id, charger_kw = _charger_from_live(ticket, live)
        return {
            "vehicle_id": vid,
            "job_id": ticket.get("job_id"),
            "action": "Accept",
            "status": status,
            "city": ticket.get("city") or "-",
            "rule": ticket.get("rule") or "",
            "quoted": ticket.get("quoted") or "",
            "charger_id": charger_id,
            "charger_power_kw": charger_kw,
            "range_km": None if not live else live.get("range_km"),
            "activity": None if not live else live.get("activity"),
            "env": "live-yard",
        }
    return {
        "vehicle_id": vid or "-",
        "job_id": ticket.get("job_id"),
        "action": "Decline",
        "status": "idle",
        "city": "-",
        "rule": ticket.get("rule") or "",
        "quoted": ticket.get("quoted") or "",
        "charger_id": None,
        "charger_power_kw": None,
        "range_km": None if not live else live.get("range_km"),
        "activity": None if not live else live.get("activity"),
        "env": "live-yard",
    }


def _fingerprint(job_id: str | None, vehicle_id: str | None, ticket: dict | None, reply: dict | None) -> str:
    fleet = []
    for row in live_vehicles():
        fleet.append((row.get("id"), row.get("status"), row.get("range_km"), row.get("hours_ok")))
    jobs = []
    for jid, state in sorted((sim.jobs() or {}).items()):
        jobs.append((jid, state.get("state"), state.get("vehicle_id")))
    return json.dumps(
        {
            "job": job_id,
            "vehicle": vehicle_id,
            "kind": None if not ticket else ticket.get("kind"),
            "action": None if not reply else reply.get("action"),
            "status": None if not reply else reply.get("status"),
            "fleet": fleet,
            "jobs": jobs,
        },
        separators=(",", ":"),
    )


def _snapshot(ticket: dict | None, reply: dict | None, live: dict | None) -> dict:
    return {
        "engine_ticket": ticket,
        "engine_driver": reply,
        "live_unit": {
            "id": None if not live else live.get("id"),
            "status": None if not live else live.get("status"),
            "activity": None if not live else live.get("activity"),
            "range_km": None if not live else live.get("range_km"),
            "place": None if not live else live.get("place"),
            "job_id": None if not live else live.get("job_id"),
        },
        "fleet": live_vehicles(),
        "jobs": sim.jobs(),
        "lookup_quotes": None if not ticket else ticket.get("quotes"),
    }


def _apply_dispatcher(engine: dict, grok: dict) -> dict:
    out = dict(engine)
    kind = str(grok.get("kind") or engine.get("kind") or "")
    if engine.get("kind") == "REFUSE":
        kind = "REFUSE"
    if engine.get("vehicle_id") == "T-14" and kind == "ASSIGN":
        kind = "REFUSE"
    out["kind"] = engine.get("kind") or kind
    out["decision"] = "Assign" if out["kind"] == "ASSIGN" else "Refuse"
    out["say"] = str(grok.get("say") or "").strip()
    quoted = str(grok.get("quoted") or "").strip()
    if quoted and engine.get("quoted") and quoted in engine["quoted"]:
        out["quoted"] = quoted
    out["source"] = "grok"
    out["model"] = grok_llm.MODEL
    return out


def _apply_driver(engine: dict, grok: dict) -> dict:
    out = dict(engine)
    action = str(grok.get("action") or engine.get("action") or "Decline")
    if engine.get("action") == "Decline":
        action = "Decline"
    out["action"] = action
    out["say"] = str(grok.get("say") or "").strip()
    if grok.get("charger_id") and grok.get("charger_id") != "CS-4":
        out["charger_id"] = grok.get("charger_id")
        out["charger_power_kw"] = grok.get("charger_power_kw")
    out["source"] = "grok"
    out["model"] = grok_llm.MODEL
    return out


def _run_grok(key: str, ticket: dict | None, reply: dict | None, live: dict | None) -> None:
    status = {"status": "error", "error": "unknown", "model": grok_llm.MODEL}
    try:
        snap = json.dumps(_snapshot(ticket, reply, live), ensure_ascii=True)
        drv_snap = json.dumps(
            {
                "ticket": ticket,
                "engine_driver": reply,
                "live_unit": None
                if not live
                else {
                    "id": live.get("id"),
                    "status": live.get("status"),
                    "activity": live.get("activity"),
                    "range_km": live.get("range_km"),
                    "place": live.get("place"),
                },
            },
            ensure_ascii=True,
        )
        box: dict[str, str] = {}

        def _disp() -> None:
            box["disp"] = grok_llm.chat(
                [
                    {"role": "system", "content": DISPATCHER_SYSTEM},
                    {"role": "user", "content": snap},
                ]
            )

        def _drv() -> None:
            box["drv"] = grok_llm.chat(
                [
                    {"role": "system", "content": DRIVER_SYSTEM},
                    {"role": "user", "content": drv_snap},
                ]
            )

        td = threading.Thread(target=_disp, daemon=True)
        tr = threading.Thread(target=_drv, daemon=True)
        td.start()
        tr.start()
        td.join()
        tr.join()
        disp_raw = box["disp"]
        drv_raw = box["drv"]
        status = {
            "status": "ready",
            "error": "",
            "model": grok_llm.MODEL,
            "dispatcher": grok_llm.parse_json(disp_raw),
            "driver": grok_llm.parse_json(drv_raw),
        }
    except Exception as exc:  # noqa: BLE001 — radio fallback is engine tickets
        status = {"status": "error", "error": str(exc)[:240], "model": grok_llm.MODEL}
    with _lock:
        _cache[key] = status
        _inflight.discard(key)


def _kick(key: str, ticket: dict | None, reply: dict | None, live: dict | None) -> dict:
    with _lock:
        hit = _cache.get(key)
        if hit:
            return hit
        if key in _inflight:
            return {"status": "calling", "error": "", "model": grok_llm.MODEL}
        if not grok_llm.api_key():
            miss = {"status": "off", "error": "XAI_API_KEY is not set", "model": grok_llm.MODEL}
            _cache[key] = miss
            return miss
        _inflight.add(key)
        threading.Thread(
            target=_run_grok,
            args=(key, ticket, reply, live),
            daemon=True,
            name="grok-desk-agents",
        ).start()
        return {"status": "calling", "error": "", "model": grok_llm.MODEL}


def payload(
    job_id: str | None,
    vehicle_id: str | None,
    started: list[dict] | None = None,
) -> dict:
    rows = events()
    event = find_event(job_id, vehicle_id, rows)
    ticket = dispatcher_ticket(event) if event else None
    vid = (ticket or {}).get("vehicle_id")
    live = sim.public_vehicle(str(vid)) if vid else None
    job_state = (sim.jobs().get(job_id) or {}).get("state") if job_id else None
    reply = driver_reply(ticket, live=live, job_state=job_state)
    key = _fingerprint(job_id, vehicle_id, ticket, reply)
    llm = _kick(key, ticket, reply, live)
    if llm.get("status") == "ready":
        if ticket and isinstance(llm.get("dispatcher"), dict):
            ticket = _apply_dispatcher(ticket, llm["dispatcher"])
        if reply and isinstance(llm.get("driver"), dict):
            reply = _apply_driver(reply, llm["driver"])
        note = f"{grok_llm.LABEL} on the radio. Engine still runs dispatch_job. Driver only rolls on ASSIGN."
    elif llm.get("status") == "calling":
        note = f"{grok_llm.LABEL} is on the air…"
    elif llm.get("status") == "off":
        note = "Grok key missing. Engine tickets only."
    else:
        note = f"Grok radio down. Engine tickets only. {llm.get('error') or ''}".strip()
    return {
        "plugin": PLUGIN,
        "sources": {"dispatcher": DISPATCHER_SRC, "driver": DRIVER_SRC},
        "env": "live-yard",
        "model": grok_llm.MODEL,
        "model_label": grok_llm.LABEL,
        "llm": {"status": llm.get("status"), "error": llm.get("error") or ""},
        "events": rows,
        "dispatcher": ticket,
        "driver": reply,
        "started": list(started or []),
        "note": note,
    }
