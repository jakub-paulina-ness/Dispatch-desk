#!/usr/bin/env python3
"""Local page for the dispatch desk. Uses desk.py. Does not change kit files."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

import desk  # noqa: E402
import sim  # noqa: E402

DISPLAY_FILE = WEB / "display.json"
LOG_FILE = ROOT / "dispatch.log"

STATE: dict = {"log": []}


def reset() -> None:
    sim.reset()
    STATE["log"] = []


def load_display() -> dict:
    return json.loads(DISPLAY_FILE.read_text(encoding="utf-8"))


def busy_ids() -> set[str]:
    return sim.busy_ids()


def overlay_vehicle(row: dict) -> dict:
    live = sim.public_vehicle(str(row.get("id") or ""))
    item = dict(row)
    if live:
        item["status"] = live["status"]
        item["hours_ok"] = live["hours_ok"]
        item["range_km"] = live["range_km"]
        item["activity"] = live["activity"]
        item["activity_label"] = live["activity_label"]
        item["eta_free_s"] = live["eta_free_s"]
        item["eta_free_clock"] = live["eta_free_clock"]
        item["place"] = live["place"]
        item["work"] = live["work"]
        item["job_id"] = live["job_id"]
        item["session"] = live["session"]
        item["range_full"] = live["range_full"]
        item["ops"] = live["ops"]
    else:
        item["session"] = "roster"
    return item


def serialize_result(result: dict, phase: str = "open") -> dict:
    job = result.get("job") or {}
    vehicle = result.get("vehicle")
    return {
        "kind": result.get("kind") or "decision",
        "decision": result.get("decision"),
        "phase": phase,
        "rule": result.get("rule") or "",
        "quote": result.get("quote") or "",
        "reason": result.get("reason") or result.get("message") or "",
        "gates": result.get("gates") or [],
        "job_id": job.get("id"),
        "city": job.get("city"),
        "km": job.get("km"),
        "vehicle_id": result.get("vehicle_id"),
        "vehicle": overlay_vehicle(vehicle) if vehicle else None,
    }


def _kit_jobs() -> list[dict]:
    rows = []
    for job in desk.load_jobs():
        live = sim.jobs().get(job["id"], {"state": "open", "vehicle_id": None})
        item = dict(job)
        item["state"] = live.get("state") or "open"
        item["vehicle_id"] = live.get("vehicle_id")
        rows.append(item)
    return rows


def board_payload(job_id: str | None = None, vehicle_id: str | None = None) -> dict:
    display = load_display()
    jobs = _kit_jobs()
    vehicles = [overlay_vehicle(row) for row in desk.load_vehicles()]
    selected_job = job_id or (jobs[0]["id"] if jobs else None)
    selected_vehicle = vehicle_id
    phase = "open"
    job_row = next((row for row in jobs if row["id"] == selected_job), None)
    if selected_job and job_row and job_row["state"] in {"assigned", "done"}:
        phase = job_row["state"]
        assigned_to = job_row.get("vehicle_id")
        pair_id = selected_vehicle or assigned_to
        if pair_id:
            result = desk.decide_pair(selected_job, pair_id, None, sim.live(pair_id))
        else:
            result = desk.decide_job(selected_job, None, sim.fleet())
        packed = serialize_result(result, phase)
        packed["vehicle_id"] = assigned_to
        packed["decision"] = "Assign"
        ident, quote = desk.quoted("DSP-1", "free")
        packed["rule"] = ident
        packed["quote"] = quote
        if phase == "assigned":
            packed["reason"] = f"Already sent. {assigned_to} is on this job."
        else:
            packed["reason"] = f"Completed by {assigned_to}."
            packed["gates"] = [
                {"id": "on_roster", "label": "On vehicles.json", "ok": True},
                {"id": "not_red", "label": "Not out of service", "ok": True},
                {"id": "free", "label": "status free", "ok": True},
                {"id": "hours", "label": "hours_ok", "ok": True},
                {"id": "range", "label": "km < range_km", "ok": True},
            ]
        can_send = False
        selected_vehicle = selected_vehicle or assigned_to
    elif selected_job and selected_vehicle:
        result = desk.decide_pair(selected_job, selected_vehicle, None, sim.live(selected_vehicle))
        packed = serialize_result(result, phase)
        can_send = packed["decision"] == "Assign" and (job_row or {}).get("state") == "open"
    elif selected_job:
        result = desk.decide_job(selected_job, None, sim.fleet())
        packed = serialize_result(result, phase)
        selected_vehicle = result.get("vehicle_id")
        can_send = packed["decision"] == "Assign" and (job_row or {}).get("state") == "open"
    else:
        packed = serialize_result(
            {
                "kind": "decision",
                "decision": "Refuse",
                "rule": "",
                "quote": "",
                "reason": "No job in jobs.json.",
                "gates": [],
                "job": {},
                "vehicle_id": None,
                "vehicle": None,
            }
        )
        can_send = False
    detail = sim.public_vehicle(selected_vehicle) if selected_vehicle else None
    warnings = sim.warnings_for(job_row, packed.get("vehicle_id") if can_send else selected_vehicle)
    if detail and detail["ops"].get("charge_advice"):
        warnings.append(detail["ops"]["charge_advice"])
    open_jobs = sum(1 for row in jobs if row["state"] == "open")
    return {
        "org": display.get("org"),
        "mark": display.get("mark"),
        "desk": display.get("desk"),
        "dispatcher": display.get("dispatcher"),
        "shift": display.get("shift"),
        "yard": display.get("yard"),
        "job_count": open_jobs,
        "jobs": jobs,
        "vehicles": vehicles,
        "selected_job": selected_job,
        "selected_vehicle": selected_vehicle,
        "vehicle_detail": detail,
        "recommendation": packed,
        "warnings": warnings,
        "log": list(STATE["log"]),
        "events": sim.S["events"],
        "sim": sim.sim_payload(),
        "map": sim.map_payload(selected_vehicle),
        "can_send": can_send,
        "can_undo": sim.can_undo(),
        "who_clicks": display.get("dispatcher"),
    }


def append_log(entry: dict) -> None:
    STATE["log"].insert(0, entry)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _log(decision: str, job_id: str | None, vehicle_id: str | None, rule: str, quote: str) -> dict:
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "clock": sim.sim_payload()["clock"],
        "dispatcher": load_display().get("dispatcher"),
        "job_id": job_id,
        "vehicle_id": vehicle_id,
        "decision": decision,
        "rule": rule,
        "quote": quote,
    }
    append_log(entry)
    return entry


def confirm(job_id: str, vehicle_id: str) -> dict:
    result = desk.decide_pair(job_id, vehicle_id, None, sim.live(vehicle_id))
    if result["decision"] != "Assign":
        return {
            "ok": False,
            "error": "That recommendation is a refuse. Nothing sent.",
            "board": board_payload(job_id, vehicle_id),
        }
    job = desk.get_job(job_id)
    if job is None:
        return {"ok": False, "error": "Unknown job.", "board": board_payload(job_id, vehicle_id)}
    started = sim.assign_job(vehicle_id, job)
    if not started.get("ok"):
        return {"ok": False, "error": started.get("error") or "Not sent.", "board": board_payload(job_id, vehicle_id)}
    entry = _log("Assign", job_id, vehicle_id, result["rule"], result["quote"])
    return {"ok": True, "sent": entry, "board": board_payload(job_id, vehicle_id)}


def undo() -> dict:
    last = None
    for index, row in enumerate(STATE["log"]):
        if row.get("decision") in {"Assign", "Service", "Charge", "Return"}:
            last = STATE["log"].pop(index)
            break
    snap = sim.undo()
    if snap is None and last is None:
        return {"ok": False, "error": "Nothing to undo.", "board": board_payload()}
    if snap is None and last is not None:
        STATE["log"].insert(0, last)
        return {"ok": False, "error": "Nothing to undo.", "board": board_payload()}
    entry = _log(
        "Undo",
        (last or {}).get("job_id"),
        (last or {}).get("vehicle_id"),
        (last or {}).get("rule") or "",
        "Dispatcher undid last send. Kit files unchanged.",
    )
    return {
        "ok": True,
        "undone": last,
        "board": board_payload((last or {}).get("job_id"), (last or {}).get("vehicle_id")),
        "log_entry": entry,
    }


def call_service(vehicle_id: str) -> dict:
    if desk.get_vehicle(vehicle_id) is None:
        ident, quote = desk.quoted("DSP-4", "invent")
        return {
            "ok": False,
            "rule": ident,
            "error": quote,
            "board": board_payload(None, vehicle_id),
        }
    result = sim.call_service(vehicle_id)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error"), "board": board_payload(None, vehicle_id)}
    ident, quote = desk.quoted("DSP-3", "red")
    entry = _log("Service", None, vehicle_id, ident, quote)
    return {"ok": True, "sent": entry, "board": board_payload(None, vehicle_id)}


def send_charge(vehicle_id: str, charger_id: str | None) -> dict:
    if desk.get_vehicle(vehicle_id) is None:
        ident, quote = desk.quoted("DSP-4", "invent")
        return {"ok": False, "rule": ident, "error": quote, "board": board_payload(None, vehicle_id)}
    result = sim.send_charge(vehicle_id, charger_id)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error"), "board": board_payload(None, vehicle_id)}
    entry = _log("Charge", None, vehicle_id, "", f"Sent to {(result.get('charger') or {}).get('name')}.")
    return {"ok": True, "sent": entry, "board": board_payload(None, vehicle_id)}


def send_return(vehicle_id: str) -> dict:
    if desk.get_vehicle(vehicle_id) is None:
        ident, quote = desk.quoted("DSP-4", "invent")
        return {"ok": False, "rule": ident, "error": quote, "board": board_payload(None, vehicle_id)}
    result = sim.send_return(vehicle_id)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error"), "board": board_payload(None, vehicle_id)}
    entry = _log("Return", None, vehicle_id, "", "Return to Cluj yard.")
    return {"ok": True, "sent": entry, "board": board_payload(None, vehicle_id)}


def set_speed(speed: int) -> dict:
    sim.set_speed(int(speed))
    return {"ok": True, "board": board_payload()}


def ask_payload(question: str, job_id: str | None, vehicle_id: str | None) -> dict:
    question = (question or "").strip()
    if not question:
        return {"ok": False, "error": "Type a question for the desk."}
    if desk.OFF_SCOPE.search(question):
        refused = desk.refuse_off_scope(question)
        return {
            "ok": True,
            "kind": "off_desk",
            "label": "Off desk",
            "rule": "",
            "detail": refused["message"],
        }
    lowered = question.lower()
    if "t-14" in lowered or "t14" in lowered:
        job_id = job_id or "J-01"
        result = desk.decide_pair(job_id, "T-14", None, sim.live("T-14"))
        return {
            "ok": True,
            "kind": "decision",
            "label": result["decision"],
            "rule": result["rule"],
            "detail": result["quote"],
        }
    if "t-99" in lowered or "invent" in lowered:
        result = desk.decide_pair(job_id or "J-01", "T-99")
        return {
            "ok": True,
            "kind": "decision",
            "label": result["decision"],
            "rule": result["rule"],
            "detail": result["quote"],
        }
    return {
        "ok": True,
        "kind": "off_desk",
        "label": "Off desk",
        "rule": "",
        "detail": desk.OFF_DESK,
    }


MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


class DeskHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _sync(self) -> None:
        sim.sync_wall(time.monotonic())

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/board":
            self._sync()
            query = parse_qs(parsed.query)
            job_id = (query.get("job") or [None])[0]
            vehicle_id = (query.get("vehicle") or [None])[0]
            self._json(200, board_payload(job_id, vehicle_id))
            return
        if path == "/":
            path = "/index.html"
        rel = Path(path.lstrip("/"))
        if ".." in rel.parts:
            self._json(400, {"error": "bad path"})
            return
        target = (WEB / rel).resolve()
        if not str(target).startswith(str(WEB.resolve())) or not target.is_file():
            self._json(404, {"error": "not found"})
            return
        data = target.read_bytes()
        self._send(200, data, MIME.get(target.suffix, "application/octet-stream"))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = self._read_json()
        self._sync()
        if parsed.path == "/api/confirm":
            self._json(200, confirm(str(body.get("job_id") or ""), str(body.get("vehicle_id") or "")))
            return
        if parsed.path == "/api/undo":
            self._json(200, undo())
            return
        if parsed.path == "/api/service":
            self._json(200, call_service(str(body.get("vehicle_id") or "")))
            return
        if parsed.path == "/api/charge":
            self._json(
                200,
                send_charge(str(body.get("vehicle_id") or ""), body.get("charger_id")),
            )
            return
        if parsed.path == "/api/return":
            self._json(200, send_return(str(body.get("vehicle_id") or "")))
            return
        if parsed.path == "/api/speed":
            raw_speed = body.get("speed")
            self._json(200, set_speed(4 if raw_speed is None else int(raw_speed)))
            return
        if parsed.path == "/api/reset":
            reset()
            self._json(200, {"ok": True, "board": board_payload()})
            return
        if parsed.path == "/api/ask":
            self._json(
                200,
                ask_payload(
                    str(body.get("question") or ""),
                    body.get("job_id"),
                    body.get("vehicle_id"),
                ),
            )
            return
        self._json(404, {"error": "not found"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the dispatch desk page")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer((args.host, args.port), DeskHandler)
    print(f"Desk page: http://{args.host}:{args.port}/", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
