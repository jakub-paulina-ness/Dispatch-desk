# S-04 Must-show runbook

| Field | Value |
|---|---|
| **Owner** | Peťo |
| **Layer** | A — graded |
| **Status** | done |
| **Blocked on** | Architecture / [S-00](S-00-contracts.md). Hook **implementation** is Jakub (S-05); you spec it (already in architecture). |
| **Unblocks** | Dry-run clock; live demo speaking order |

## Goal

As acceptance QA, I want a 3–4 minute spoken checklist so the laptop shows inspect, AGENTS.md, plan, skill, hook, MCP, script, and test.

## Files

- `pipelines/DEMO.md`

## Acceptance

- [x] Checklist MS-1…MS-8 and Hotovo A/B/C with the exact command to type.
- [x] Spoken timestamps (architecture demo table is the default).
- [x] Windows only: `python pipelines/show_lab.py`, `python dispatch.py`, `python -m unittest test_dispatch -v`. Never `python3`.
- [x] Stage 3 laptop wiring: `grok mcp doctor rules` — if green, do **not** re-add; show `grok mcp list`. Folder trust. Plugin enable. Hook deny rehearsal (`search_replace` / `write` on `instructions/dispatch_rules.md`).
- [x] Fallback line: if UI dies, continue on CLI.
- [x] Layer B (map / charger) is **after** Hotovo, optional, ≤ 60 s.

## Parallel

S-11 dispatcher is your second story. Runbook can be written without any engine.

## Out of scope

Implementing `protect_rules.py` (S-05, Jakub). Driving the desk/UI in the jury slot (Marian).
