# Plan: dispatch desk (track 4.1)

Agreed before agent files were written. Kit files stay as downloaded from the track page: `vehicles.json`, `jobs.json`, `dispatch_rules.md`, `rules_mcp.py`. Do not invent a rule file.

## Track in one sentence

Assign jobs from the roster and the queue; refuse any vehicle that is out of service.

## What the kit contains

| File | Role |
| --- | --- |
| `vehicles.json` | Roster: T-11 free, T-12 busy, T-14 red |
| `jobs.json` | Queue: J-01 Cluj 40 km, J-02 Oradea 160 km |
| `dispatch_rules.md` | DSP-1 … DSP-4 |
| `rules_mcp.py` | MCP `lookup_rule` / `list_rules` |

## Decisions (from the rule file only)

| Case | Outcome | Rule |
| --- | --- | --- |
| J-01 (Cluj 40 km) | **Assign T-11** | DSP-1 (free + hours_ok). Distance 40 < 180 also satisfies DSP-2. |
| J-02 (Oradea 160 km) | **Assign T-11** | DSP-1. Distance 160 < 180 satisfies DSP-2. T-12 range 90 fails DSP-2; T-12 is also busy. |
| Any job + **T-14** | **Refuse** | DSP-3. Status red is out of service. |
| Any job + T-12 | **Refuse** | DSP-1. Status is busy, not free. |
| Vehicle not in `vehicles.json` | **Refuse** | DSP-4. Do not invent a vehicle. |
| Medical / legal / payment advice | **Off desk** | Turn down. Do not invent a rule id. |

## Build list (must show)

1. **inspect** — `grok inspect` on this folder before the demo.
2. **AGENTS.md** — quote `dispatch_rules.md` via `lookup_rule`; never invent rules; refuse T-14; off-scope questions get turned down.
3. **plan** — this file.
4. **skill** — how to open a job, call `lookup_rule`, assign or refuse.
5. **hook** — block off-scope advice; deny edits to kit files.
6. **MCP `lookup_rule`** — project server `rules` → `python3 rules_mcp.py`.
7. **plugin** — pack skill + hook + MCP under `.grok/plugins/dispatch-desk/`.
8. **script** — `desk.py`, rerunnable from the kit files.
9. **test** — T-14 stays refused (`python test_desk.py`).

## If this went live

- **Who must click before it sends:** the dispatcher. A recommendation is not a send. Confirm is the click.
- **How you undo a bad change:** Undo last send. Session overlay only; kit files are never rewritten.
- **What you write in a log:** time, dispatcher, job, vehicle, decision, rule id, quoted line (`dispatch.log`).

## Live demo order

1. Name the track in one sentence.
2. Pass: J-01 → Assign T-11, quote DSP-1, Confirm.
3. Refuse: T-14 → Refuse, quote DSP-3.
4. Point at AGENTS.md, the skill, the hook, and MCP `lookup_rule`.
5. Stop. Questions from judges only.

Backup if the page is down: `python desk.py --demo`
