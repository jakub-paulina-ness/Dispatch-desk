# Plan: dispatch desk (track 4.1)

Status **2026-09-18:** Layer A (graded must-show) is on `main`. Layer B stories S-10…S-14 are on `main`. Live yard `desk.py` + `web/` on `http://127.0.0.1:8770/` is a second board (confirm / undo / map). Thin desk: `python src/dispatch_server.py` → `http://127.0.0.1:8765/`.

Design freeze: `.docs/specification/architecture.md` (some paths in that file are stale; this document wins on *what shipped*). Team: `TEAM.md`. Stories: `.docs/stories/README.md`.

Kit files stay as downloaded. Do not invent a rule file. Do not invent T-15 or DSP-5.

## Track in one sentence

Assign jobs from the roster and the queue; refuse any vehicle that is out of service. The model is the operator. The assigner is a deterministic script.

## What the kit contains

Canonical **assignment** files live under `instructions/` (engine, MCP, tests, AGENTS.md). `.docs/reference/` keeps the brief, screenshots, a copy of those four files, and sim-only `locations.json`.

| File | Role |
| --- | --- |
| `instructions/vehicles.json` | Roster: T-11 free 180 km, T-12 busy 90 km, T-14 red 200 km |
| `instructions/jobs.json` | Queue: J-01 Cluj 40 km, J-02 Oradea 160 km |
| `instructions/dispatch_rules.md` | DSP-1 … DSP-4 |
| `instructions/rules_mcp.py` | MCP `lookup_rule` / `list_rules` (`handle()`) |
| `.docs/reference/locations.json` | Driver / live-yard geography only. Not an eligibility input. |

## Frozen outcomes

Evaluate **DSP-3 → DSP-1 → DSP-2**. First-fit in `vehicles.json` order. Do not mutate the roster after J-01. Quotes come from `handle()` / `lookup_rule`, never from memory.

| Case | Outcome | Rule |
| --- | --- | --- |
| J-01 (Cluj 40 km) | **ASSIGN T-11** | DSP-1 (free + hours_ok). 40 < 180 also satisfies DSP-2. |
| J-02 (Oradea 160 km) | **ASSIGN T-11** | Same. 160 < 180. |
| Any job + **T-12** | **SKIP** | DSP-1. Busy, not free. (Live yard `desk.py` still prints this as Refuse — see Remaining.) |
| Any job + **T-14** | **REFUSE** | DSP-3. Status red is out of service. |
| Vehicle not in `vehicles.json` | **REFUSE** | DSP-4. Do not invent a vehicle. |
| Medical / legal / payment advice | **Off desk** | Turn down. Do not invent a rule id. |

Interpreter on this laptop: **`python`**, never `python3`.

## How we planned (two waves)

The repo had two planning systems. They were not kept in sync.

1. **Hackathon split (root `TEAM.md`, P1–P5).** One laptop, file ownership for `desk.py` + `web/` live board, confirm / undo / log. This is what landed first as `feature/dispatch-desk`.
2. **Named stories (`.docs/TEAM.md` + `.docs/stories/`).** Jakub / Marek / Peťo / Marian / Ondrej. Architecture + S-00…S-14. Layer A = graded CLI + Grok stack. Layer B = HTML desk, dispatcher, driver, locations, optional thin server.

Work after that was mixed: stories on their branches, live yard and extra skills **freestyle** on `main`. This file and `TEAM.md` are the single status view.

## What actually shipped

### Layer A — graded (must-show)

| # | Item | On disk |
| --- | --- | --- |
| 1 | inspect | `instructions/` four files; `python pipelines/show_lab.py` |
| 2 | AGENTS.md | repo-root `AGENTS.md` |
| 3 | plan | this file + `.docs/specification/architecture.md` |
| 4 | skill | `.grok/skills/dispatch-desk/SKILL.md` and plugin copy |
| 5 | hook | `.grok/hooks/protect_rules.py` (and `desk_guard.py`) + plugin copies |
| 6 | MCP `lookup_rule` | project `rules` in `.grok/config.toml` → `python instructions/rules_mcp.py`. Plugin has **no** `.mcp.json`. |
| 7 | script | `python dispatch.py` → `src/dispatch.py` (root file is a shim) |
| 8 | test | `python -m unittest test_dispatch -v` — T-14 never ASSIGN |

Also on `main`: `pipelines/DEMO.md`, `presenter.md`, plugin pack, `tests/test_protect_rules.py`.

### Layer B — stories

| Story | Status | What landed |
| --- | --- | --- |
| S-00 contracts | **done** | `.docs/stories/S-00-contracts.md` |
| S-10 HTML desk | **done** | `src/web/index.html` + `desk.css` / `desk.js` — served by S-14 |
| S-11 dispatcher | **done** | `src/dispatcher.py` — calls `dispatch_job`, starts a driver only on ASSIGN |
| S-12 driver | **done** | `src/sim/driver.py` — T-11 telemetry after ASSIGN; J-02 → CS-2 150 kW |
| S-13 locations | **done** | `.docs/reference/locations.json` |
| S-14 thin server | **done** | `src/dispatch_server.py` on `127.0.0.1:8765` — `/api/dispatch` from the engine |

### Freestyle (not on the original story board)

| Item | What landed |
| --- | --- |
| Live yard | `desk.py` + `web/server.py` + `web/sim.py` on `http://127.0.0.1:8770/`. Confirm, undo, `dispatch.log`, map, vehicle pages, session overlay (kit not rewritten). |
| Desk tests | `python test_desk.py`, `python web/test_api.py` |
| Presenter | `presenter.md` (voice script) |
| Extra skills | `.grok/skills/create-issue/`, `fix-issue/`, `run-app/` |
| Grok agents | `.grok/agents/dispatcher.md`, `driver.md` |
| ISS-001 | open — extra live jobs without touching the kit |

## If this went live

Already true on the live yard (session overlay only; kit files are never rewritten):

- **Who must click before it sends:** the dispatcher. A recommendation is not a send. Confirm is the click.
- **How you undo a bad change:** Undo last send.
- **What you write in a log:** time, dispatcher, job, vehicle, decision, rule id, quoted line (`dispatch.log`).

## Live demo

Graded path (3–4 min): `pipelines/DEMO.md` and `presenter.md`.

```text
python pipelines/show_lab.py
python dispatch.py
python -m unittest test_dispatch -v
```

Backup if any UI dies: `python dispatch.py` (or `python desk.py --demo`).

Optional wow: `python src/dispatch_server.py` → `http://127.0.0.1:8765/` (S-10 page + engine API), or `python web/server.py` → `http://127.0.0.1:8770/` (`/run-app` live yard).

## Remaining (what is still missing)

Nothing on this list blocks the Layer A lab tick. These are the real leftovers.

1. **Two UIs.** S-14 serves `src/web/` on **8765** from the engine. Live yard `web/` on **8770** is confirm/undo/map. Pick one for the jury; the other is leftover.
2. **Two assigners.** AGENTS.md says first-fit lives only in `dispatch_job`. Live yard `desk.py` reimplements DSP. Engine: T-12 is **SKIP**. Desk / `test_desk.py`: T-12 is **Refuse DSP-1**. Wire the 8770 board to `dispatch_job` or accept the split on purpose.
3. **Architecture kit path is stale.** The spec still says load assignment data from `.docs/reference/` and retarget MCP there. Code, tests (`T-LOAD-PATH`), MCP args, and AGENTS.md all use `instructions/`. Leave it unless someone wants a path migration. `locations.json` correctly stays in reference.
4. **T-LOC-NOT-ENGINE** was specified and never added to `tests/test_dispatch.py`. The engine does not read `locations.json`; the named test is missing.
5. **Hook split.** `protect_rules.py` denies `*_rules.md`. `protect_vehicles.py` denies `vehicles.json`. `desk_guard.py` also blocks `jobs.json`, `rules_mcp.py`, and off-scope prompts.
6. **ISS-001 is open** — extra live jobs without touching the kit.
7. **KD-8 never shipped.** Architecture still describes `.docs/reference/` as the assignment source. Implementation uses `instructions/`.

### Explicitly out of scope (do not treat as missing)

- T-15, DSP-5, a second rule file, workshop HTML, pip, Docker.
- Plugin `.mcp.json` (v1 decision: MCP stays project-scoped).
- Mutating T-11 to busy after J-01.
- `python3` as a documented runner on this laptop.
