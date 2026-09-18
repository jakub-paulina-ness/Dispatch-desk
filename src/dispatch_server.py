"""Thin stdlib desk. Same engine as python dispatch.py. If this dies: python dispatch.py."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
WEB = SRC / "web"
LOCATIONS_PATH = ROOT / ".docs" / "reference" / "locations.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dispatcher import collect_events, run  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

HELP = (
    "python src/dispatch_server.py\n"
    "python src/dispatch_server.py --no-drive\n"
    "python src/dispatch_server.py --help\n"
    "Binds 127.0.0.1:8765. Serves src/web and /api/dispatch|/api/locations|/api/telemetry.\n"
    "If this process dies, continue with: python dispatch.py\n"
)

STATE: dict = {"events": [], "telemetry": []}


def latest_telemetry(ticks: list[dict]) -> list[dict]:
    last: dict[str, dict] = {}
    order: list[str] = []
    for tick in ticks:
        key = str(tick.get("job_id") or "")
        if key not in last:
            order.append(key)
        last[key] = tick
    return [last[key] for key in order]


def load_desk(*, drive: bool = True) -> None:
    if drive:
        result = run(drive=True)
        STATE["events"] = result["events"]
        STATE["telemetry"] = result["telemetry"]
    else:
        STATE["events"] = collect_events()
        STATE["telemetry"] = []


def _safe_web_file(rel: str) -> Path | None:
    rel = unquote(rel).lstrip("/")
    if not rel or rel.endswith("/"):
        rel = (rel + "index.html") if rel else "index.html"
    candidate = (WEB / rel).resolve()
    web_root = WEB.resolve()
    if candidate != web_root and web_root not in candidate.parents:
        return None
    if not candidate.is_file():
        return None
    return candidate


class DeskHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("dispatch_server: " + (fmt % args) + "\n")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/dispatch":
            self._json({"events": STATE["events"]})
            return
        if path == "/api/locations":
            self._json(json.loads(LOCATIONS_PATH.read_text(encoding="utf-8")))
            return
        if path == "/api/telemetry":
            self._json({"events": latest_telemetry(STATE["telemetry"])})
            return
        if path == "/api/play":
            load_desk(drive=True)
            self._json(
                {
                    "events": STATE["events"],
                    "telemetry": latest_telemetry(STATE["telemetry"]),
                }
            )
            return
        target = _safe_web_file(path)
        if target is None:
            self._json({"error": "not found"}, code=404)
            return
        data = target.read_bytes()
        self._send(200, data, MIME.get(target.suffix.lower(), "application/octet-stream"))


def make_server(
    host: str = HOST,
    port: int = PORT,
    *,
    drive: bool = True,
) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("bind 127.0.0.1 only")
    load_desk(drive=drive)
    httpd = ThreadingHTTPServer((host, port), DeskHandler)
    httpd.allow_reuse_address = True
    return httpd


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("-h", "--help") for arg in argv):
        sys.stdout.write(HELP)
        return 0
    drive = "--no-drive" not in argv
    try:
        httpd = make_server(HOST, PORT, drive=drive)
    except OSError as exc:
        sys.stderr.write(f"{exc}\nfallback: python dispatch.py\n")
        return 1
    sys.stdout.write(f"http://{HOST}:{PORT}/  (fallback: python dispatch.py)\n")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("\nfallback: python dispatch.py\n")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
