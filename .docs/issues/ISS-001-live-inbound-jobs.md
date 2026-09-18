---
id: ISS-001
title: Feed extra live jobs without touching the kit
status: open
priority: medium
type: feature
created: 2026-09-18
area: web
files:
  - .docs/reference/live_jobs.json
  - src/dispatcher.py
  - src/dispatch_server.py
  - src/web/index.html
  - tests/test_dispatch_server.py
---

# ISS-001 Feed extra live jobs without touching the kit

## Handoff

Implement this issue from this file. Do not expand scope. Set `status: done`
only after every acceptance item is true.

## Problem

Layer A kit queue is two tickets only:

```json
[
  {"id": "J-01", "city": "Cluj", "km": 40},
  {"id": "J-02", "city": "Oradea", "km": 160}
]
```

`src/dispatch.py` `load_jobs()` always reads `instructions/jobs.json`.
`src/dispatcher.py` `collect_events()` uses that list. `src/dispatch_server.py`
`GET /api/dispatch` therefore never grows past J-01/J-02.

The live desk looks static after the first assign. Extra jobs must **not** go
into `instructions/jobs.json` (kit lock, DSP-4 universe for Layer A, T-LOAD-PATH).

## Expected

Layer B inbound pack at `.docs/reference/live_jobs.json` (not kit):

| id | city | km | Why it is interesting | Expected outcomes |
|---|---|---|---|---|
| J-03 | Cluj | 40 | Second short hop | ASSIGN T-11, SKIP T-12 DSP-1, REFUSE T-14 DSP-3 |
| J-04 | Oradea | 180 | DSP-2 miss: `180 < 180` is false | SKIP T-11 DSP-2, SKIP T-12 DSP-1, REFUSE T-14 DSP-3, **no ASSIGN** |
| J-05 | Oradea | 160 | Repeat highway + CS-2 charge if driver runs | ASSIGN T-11, SKIP T-12, REFUSE T-14 |

`python src/dispatch_server.py --live` (or equivalent flag already in HELP):

1. Serve kit events first (J-01, J-02) so Layer A is unchanged on `/api/dispatch` at t=0.
2. Every ~6–8 s append the next live job, run existing `dispatch_job(job, vehicles)` (same engine, same quotes via `lookup_rule`).
3. Do not mutate roster. Do not invent T-15 / DSP-5 / new cities.
4. HTML job queue shows the extra tickets as they arrive.

`python dispatch.py` still prints **only** J-01 and J-02.

Cities stay Cluj / Oradea from `.docs/reference/locations.json`. No new map points in this ticket.

## Actual

`python dispatch.py` prints two `=== JOB` blocks and two `ASSIGN vehicle=T-11`.
Server `STATE["events"]` is filled once in `load_desk()` from kit jobs only.
There is no `live_jobs.json`. No `--live` flag in `src/dispatch_server.py` HELP.

## Repro

1. `python dispatch.py` — two jobs.
2. `python src/dispatch_server.py --no-drive` then `GET http://127.0.0.1:8765/api/dispatch` — six events, job_id in {J-01, J-02} only.
3. Open `http://127.0.0.1:8765/` — job queue lists J-01 and J-02 only.

## Files

- `.docs/reference/live_jobs.json` — inbound pack (create)
- `src/dispatcher.py` — optional `jobs=` already exists; wire a loader for the live pack, do not copy DSP
- `src/dispatch_server.py` — `--live` timer that appends dispatch events
- `src/web/index.html` / `desk.js` — render extra job tickets from `/api/dispatch` (do not hardcode J-03 in HTML if the API already lists them)
- `tests/test_dispatch_server.py` — live pack + J-04 has no ASSIGN; kit CLI tests stay green
- `instructions/jobs.json` — **do not edit**

## Acceptance

- [ ] `instructions/jobs.json` unchanged (still J-01, J-02 only)
- [ ] `python dispatch.py` still two JOB blocks, both ASSIGN T-11
- [ ] `.docs/reference/live_jobs.json` contains J-03, J-04, J-05 as in Expected
- [ ] `python src/dispatch_server.py --live` eventually includes those job_ids on `GET /api/dispatch`
- [ ] J-04 events include SKIP T-11 with DSP-2, REFUSE T-14 with DSP-3, and **no** ASSIGN
- [ ] J-03 and J-05 ASSIGN T-11 with quotes from `lookup_rule`
- [ ] `python -m unittest test_dispatch -v` still green
- [ ] No T-15, no DSP-5, no new city names

## Constraints

- Kit under `instructions/` is immutable.
- Do not invent vehicles (no T-15) or rules (no DSP-5).
- Quotes from `lookup_rule` / `handle()`, never hardcoded DSP sentences in `src/dispatch.py`.
- Eligible = free + `hours_ok is True` (DSP-1) and `job.km < range_km` (DSP-2). Order DSP-3 → DSP-1 → DSP-2.
- Do not mutate roster after J-01 for Layer A. Live extras use the same frozen roster.
- Interpreter is `python`, never `python3`.
- Do not copy workshop HTML/CSS/JS.

## Out of scope

- Occupancy (T-11 busy after ASSIGN) — would change C-5; separate ticket
- New cities / extra chargers in `locations.json`
- Editing `instructions/jobs.json` or `src/dispatch.py` `evaluate_vehicle`
- Auth, `0.0.0.0`, replacing CLI as must-show 7

## Verify

```text
python dispatch.py
python -m unittest test_dispatch -v
python -m unittest tests.test_dispatch_server -v
python src/dispatch_server.py --live --no-drive
```

Then `GET /api/dispatch` after ~25 s must list J-03, J-04, J-05.
