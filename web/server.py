#!/usr/bin/env python3
"""Local page for the dispatch desk. Uses desk.py. Does not change kit files."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import desk  # noqa: E402

DISPLAY_FILE = WEB / "display.json"
LOG_FILE = ROOT / "dispatch.log"

STATE: dict = {"busy": set(), "log": []}


def load_display() -> dict:
    return json.loads(DISPLAY_FILE.read_text(encoding="utf-8"))


def busy_set() -> set[str]:
    return set(STATE["busy"])


def overlay_vehicle(row: dict) -> dict:
    item = dict(row)
    if item.get("id") in STATE["busy"]:
        item["status"] = "busy"
        item["session"] = "sent"
    else:
        item["session"] = "roster"
    return item


def serialize_result(result: dict) -> dict:
    job = result.get("job") or {}
    vehicle = result.get("vehicle")
    return {
        "kind": result.get("kind") or "decision",
        "decision": result.get("decision"),
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


def board_payload(job_id: str | None = None, vehicle_id: str | None = None) -> dict:
    display = load_display()
    jobs = desk.load_jobs()
    vehicles = [overlay_vehicle(row) for row in desk.load_vehicles()]
    selected_job = job_id or (jobs[0]["id"] if jobs else None)
    selected_vehicle = vehicle_id
    if selected_job and selected_vehicle:
        result = desk.decide_pair(selected_job, selected_vehicle, busy_set())
    elif selected_job:
        result = desk.decide_job(selected_job, busy_set())
        selected_vehicle = result.get("vehicle_id")
    else:
        result = {
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
    return {
        "org": display.get("org"),
        "mark": display.get("mark"),
        "desk": display.get("desk"),
        "dispatcher": display.get("dispatcher"),
        "shift": display.get("shift"),
        "yard": display.get("yard"),
        "job_count": len(jobs),
        "jobs": jobs,
        "vehicles": vehicles,
        "selected_job": selected_job,
        "selected_vehicle": selected_vehicle,
        "recommendation": serialize_result(result),
        "log": list(STATE["log"]),
        "can_send": result.get("decision") == "Assign",
        "can_undo": any(row.get("decision") == "Assign" for row in STATE["log"]),
        "who_clicks": display.get("dispatcher"),
    }


def append_log(entry: dict) -> None:
    STATE["log"].insert(0, entry)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def confirm(job_id: str, vehicle_id: str) -> dict:
    result = desk.decide_pair(job_id, vehicle_id, busy_set())
    if result["decision"] != "Assign":
        return {"ok": False, "error": "That recommendation is a refuse. Nothing sent.", "board": board_payload(job_id, vehicle_id)}
    vid = str(result.get("vehicle_id") or "")
    STATE["busy"].add(vid)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "dispatcher": load_display().get("dispatcher"),
        "job_id": job_id,
        "vehicle_id": vid,
        "decision": "Assign",
        "rule": result["rule"],
        "quote": result["quote"],
    }
    append_log(entry)
    return {"ok": True, "sent": entry, "board": board_payload(job_id, None)}


def undo() -> dict:
    last = None
    for index, row in enumerate(STATE["log"]):
        if row.get("decision") == "Assign":
            last = STATE["log"].pop(index)
            break
    if last is None:
        return {"ok": False, "error": "Nothing to undo.", "board": board_payload()}
    STATE["busy"].discard(last.get("vehicle_id"))
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "dispatcher": load_display().get("dispatcher"),
        "job_id": last.get("job_id"),
        "vehicle_id": last.get("vehicle_id"),
        "decision": "Undo",
        "rule": last.get("rule"),
        "quote": "Dispatcher undid last send. Kit files unchanged.",
    }
    append_log(entry)
    return {"ok": True, "undone": last, "board": board_payload(last.get("job_id"), last.get("vehicle_id"))}


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
        result = desk.decide_pair(job_id, "T-14", busy_set())
        return {
            "ok": True,
            "kind": "decision",
            "label": result["decision"],
            "rule": result["rule"],
            "detail": result["quote"],
        }
    if "t-99" in lowered or "invent" in lowered:
        result = desk.decide_pair(job_id or "J-01", "T-99", busy_set())
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

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/board":
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
        if parsed.path == "/api/confirm":
            self._json(200, confirm(str(body.get("job_id") or ""), str(body.get("vehicle_id") or "")))
            return
        if parsed.path == "/api/undo":
            self._json(200, undo())
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
