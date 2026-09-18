# S-01 AGENTS.md

| Field | Value |
|---|---|
| **Owner** | Jakub |
| **Layer** | A — graded (must-show 2) |
| **Status** | **done** |
| **Blocked on** | Team sign-off of `.docs/specification/architecture.md` |
| **Unblocks** | Live `grok inspect`; not a blocker for S-02 |

## Goal

As the architect, I want a short repo-root `AGENTS.md` so Grok inspects the kit first and never invents vehicles or rules.

## Files

- `AGENTS.md` (create)

## Acceptance

- [x] Repo root `AGENTS.md` exists.
- [x] Says: inspect `instructions/` before writing; kit is immutable; only DSP-1…DSP-4; no T-15; red → refuse and cite DSP-3 via `lookup_rule`; quotes are exact `handle()` lines; interpreter is `python` not `python3`; engine is `src/dispatch.py`; do not copy workshop HTML.
- [x] `grok inspect` lists it as a project instruction (folder must be trusted).
- [x] Short enough to show on a laptop in 15 seconds.

## Out of scope

Skill/hook/plugin (that is S-05, also yours). Engine.
