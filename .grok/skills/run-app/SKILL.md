---
name: run-app
description: >
  Start the Northbound dispatch desk live yard in the browser.
  Use when the user says "run the app", "start the app", "start the desk",
  "start the server", "open the board", or runs /run-app.
---

# Run the dispatch desk

Source of truth for how to start: repo-root `README.md` (Run section). Interpreter is `python`, never `python3`. Do not edit `instructions/`.

## Start

1. From the repo root, if `http://127.0.0.1:8770/` already returns HTTP 200, do not start a second server. Tell the user the board is up.
2. Otherwise start in the background (cwd = repo root):

```text
python web/server.py
```

Binds `127.0.0.1:8770`. Print line looks like `Desk page: http://127.0.0.1:8770/`.
3. Poll `GET http://127.0.0.1:8770/` until 200 (a few seconds). Then open that URL in the default browser (`Start-Process` on Windows).
4. If the page does not come up, run the CLI fallback and say so:

```text
python desk.py --demo
```

## What this is

Live yard UI (`web/server.py` + `desk.py` + `web/sim.py`). Session overlay only; kit files are never rewritten.

Backup CLI is `python desk.py --demo`. Assignment rules stay DSP-1…DSP-4 via `desk.py` / `lookup_rule` — do not re-decide T-11 vs T-14 in the browser.

## Do not

- `python3`
- A second process on 8770
- `src/web/` as the demo server (that is the older six-section page)
- Copy workshop HTML
