# Dispatch desk

Live fleet dispatch for Grok Enablement Track 4.1. Assign kit jobs to kit vehicles using DSP-1…DSP-4, cite the rule file, refuse T-14. Grok is the **operator**. The assignment algorithm is a **deterministic script**, not the model.

Durable plan: `.docs/specification/architecture.md`. Stories: `.docs/stories/README.md`.

## Inspect first

Before writing files, list and read the four kit files under `instructions/`:

- `dispatch_rules.md` — only rule book (DSP-1…DSP-4)
- `vehicles.json` — T-11, T-12, T-14
- `jobs.json` — J-01 Cluj 40 km, J-02 Oradea 160 km
- `rules_mcp.py` — `list_rules` / `lookup_rule` (`handle()`)

## Hard rules

1. Kit under `instructions/` is **immutable**. Do not edit those four files. A PreToolUse hook denies writes to `dispatch_rules.md` and `*_rules.md`.
2. Do not invent vehicles (no T-15) or rules (no DSP-5, no second rule file).
3. Quotes come from `lookup_rule` / `handle()`, never from memory, never hardcoded DSP sentence bodies in `src/dispatch.py`. On a miss, fail — do not dump the rule file.
4. Status `red` → **REFUSE**, cite DSP-3. T-14 is never assigned.
5. Eligible = `free` and `hours_ok is True` (DSP-1) and `job.km < range_km` (DSP-2, strict `<`). Evaluate **DSP-3 → DSP-1 → DSP-2**. First-fit in `vehicles.json` order.
6. Do not mutate roster after J-01. Both jobs ASSIGN T-11. T-12 is always SKIP (busy).
7. Interpreter is `python`, never `python3` (Store stub on this laptop).
8. Do not copy workshop HTML/CSS/JS.
9. A recommendation is not a send. The dispatcher must confirm. Undo last send if the click was wrong. Do not give medical, legal, or payment advice.

## Commands

```text
python dispatch.py
python dispatch.py J-01
python -m unittest test_dispatch -v
python pipelines/show_lab.py
python test_desk.py
python web/test_api.py
python web/server.py
```

Engine: `src/dispatch.py` (root `dispatch.py` is a shim). Kit path: `instructions/`, not `.docs/reference/`.

Live yard (Layer B): `desk.py` + `web/` on http://127.0.0.1:8770/ — session overlay only; kit files are never rewritten. Charging, yard service, and map motion are telemetry after ASSIGN, not new DSP rules.

MCP: project `rules` in `.grok/config.toml`. If `grok mcp doctor rules` is green, do not re-add — show `grok mcp list`.

## Outcomes (frozen)

| Job | Result |
|---|---|
| J-01 Cluj 40 km | ASSIGN T-11 (DSP-1, DSP-2); SKIP T-12; REFUSE T-14 (DSP-3) |
| J-02 Oradea 160 km | same |

## Standards

- **Stdlib only** for the engine and optional `dispatch_server.py`. No pip, no Docker, no extra DSP markdown.
- **One assigner:** first-fit lives only in `dispatch_job`. Do not reimplement DSP in HTML, `src/dispatcher.py`, or a driver agent.
- **Sim vs assignment:** charging, speed, junctions, kW are telemetry **after** ASSIGN. `.docs/reference/locations.json` is sim-only — never an eligibility input.
- **Python:** 3.13 via `python`. UTF-8. `hours_ok is True` (identity). Import engine as `dispatch` after inserting `src/` on `sys.path` — never `import src.dispatch`.
- **Tests:** `unittest`, no kit edits, no T-15 cases. Quotes on stdout must be a subset of `instructions/dispatch_rules.md`.
- **UI:** original, thin, `127.0.0.1` only. If it dies, demo continues on the CLI.
- **Comments:** short and factual. Do not paste DSP sentence bodies into engine comments (tests grep for that).
- **Git:** do not commit `instructions/__pycache__/`. Do not “fix” kit line endings.
