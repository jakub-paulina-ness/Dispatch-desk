# S-14 Thin HTTP server (stretch)

| Field | Value |
|---|---|
| **Owner** | Marian |
| **Layer** | B — stretch |
| **Status** | ready |
| **Blocked on** | S-02 engine + S-10 HTML. Cut without guilt if dry-run > 4 minutes. |
| **Unblocks** | One-URL live desk |

## Goal

As demo driver, I want `python src/dispatch_server.py` on `127.0.0.1:8765` serving Marek's page and JSON from the **same** engine as the CLI.

## Files

- `src/dispatch_server.py` — stdlib `http.server` only
- Serves S-10 static files
- `GET /api/dispatch` → DispatchEvent list (quotes from `handle()`)
- `GET /api/locations` → contents of `.docs/reference/locations.json`
- `GET /api/telemetry` → latest TelemetryEvent list (empty array if sim not running)

JSON shapes: [S-00](S-00-contracts.md). Define response wrappers in this story if needed, e.g. `{"events":[...]}`.

## Acceptance

- [ ] Bind `127.0.0.1` only, port 8765.
- [ ] `/api/dispatch` matches CLI outcomes (T-11 ASSIGN, T-14 REFUSE).
- [ ] No workshop HTML. No pip.
- [ ] If the process dies, demo continues with `python dispatch.py` (S-04 fallback).

## Out of scope

Auth. 0.0.0.0. Replacing the CLI as must-show 7.
