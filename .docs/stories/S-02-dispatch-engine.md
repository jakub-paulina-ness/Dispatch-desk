# S-02 Dispatch engine

| Field | Value |
|---|---|
| **Owner** | Peťo |
| **Layer** | A — graded (must-show 7) |
| **Status** | ready |
| **Blocked on** | Architecture sign-off / [S-00](S-00-contracts.md). **Not** blocked on S-01, S-03, or UI. |
| **Unblocks** | S-03 merge, S-11 real `dispatch_job`, S-14 |

## Goal

As the dispatch developer, I want a deterministic script that assigns J-01 and J-02 to T-11 and refuses T-14 with DSP-3 quoted from `handle()`.

S-11 is a separate story (event loop + start driver) on top of this file. Do not put DSP-1…4 into `src/dispatcher.py`.

## Files

- `src/dispatch.py` — engine + `main()`
- `dispatch.py` — 5-line shim (`sys.path` → `src`, `from dispatch import main`)

## Contract

Architecture § API and [S-00](S-00-contracts.md). Stdout:

```
=== JOB J-01 Cluj 40 km ===
ASSIGN vehicle=T-11
  RULE DSP-1: …
  RULE DSP-2: …
SKIP vehicle=T-12
  RULE DSP-1: …
REFUSE vehicle=T-14
  RULE DSP-3: …
```

Same block for J-02. `python dispatch.py` and `python dispatch.py J-01`. Unknown id → exit 2.

- Load kit from `instructions/` only.
- `from rules_mcp import handle` (kit module next to `dispatch_rules.md`).
- DSP-3 then DSP-1 then DSP-2. First-fit only inside `dispatch_job`.
- No roster mutation. No hardcoded DSP sentence bodies. No `locations.json`. No driver sim.

## Acceptance

- [ ] `python dispatch.py` → both jobs ASSIGN T-11, SKIP T-12, REFUSE T-14.
- [ ] DSP-3 quote equals `lookup_rule("DSP-3")`.
- [ ] `python dispatch.py J-01` prints J-01 only.
- [ ] Source of `src/dispatch.py` does not contain `out of service`, `hours_ok true`, or `less than vehicle range` as literals (including comments).

## Out of scope

HTML. Charging. Tests (Marek). Skill/hook. HTTP server. S-11 event loop (`src/dispatcher.py`) — that is still a separate story.
