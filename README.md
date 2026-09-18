# Northbound · Dispatch desk

Grok Enablement Workshop, track 4.1. Assign jobs from the roster and the queue. Refuse vehicles that are out of service.

Work in this folder (`Dispatch-desk`). Kit files from the track page live under `instructions/`. Do not invent a rule file.

One working agent. Live demo, not slides. Kit files are the only source of rules.

Status of the work (what shipped, what is left): [PLAN.md](PLAN.md). Roles: [TEAM.md](TEAM.md). Design spec: [.docs/specification/architecture.md](.docs/specification/architecture.md). Stories: [.docs/stories/README.md](.docs/stories/README.md).

## Run

Graded path (must-show):

```
python pipelines/show_lab.py
python dispatch.py
python -m unittest test_dispatch -v
```

Thin desk (S-14, optional): `python src/dispatch_server.py` → http://127.0.0.1:8765/

Live yard (optional):

```
python web/server.py
```

Board: http://127.0.0.1:8770/

Also: `python test_desk.py`, `python web/test_api.py`.

Backup if the page is down: `python dispatch.py` or `python desk.py --demo`.

## Demo in 90 seconds

1. Track: assign from the roster, refuse anything red.
2. Pass: `python dispatch.py` — J-01 and J-02 → ASSIGN T-11, SKIP T-12, REFUSE T-14.
3. Test: `python -m unittest test_dispatch -v`.
4. Point at AGENTS.md, the skill, the hook, MCP `lookup_rule`.
5. Optional: Confirm send on the live yard. Stop.

Spoken script: [presenter.md](presenter.md). Clock: [pipelines/DEMO.md](pipelines/DEMO.md).

## Kit (do not edit)

- `instructions/vehicles.json` — T-11 free, T-12 busy, T-14 red
- `instructions/jobs.json` — J-01 Cluj 40 km, J-02 Oradea 160 km
- `instructions/dispatch_rules.md` — DSP-1 … DSP-4
- `instructions/rules_mcp.py` — `lookup_rule`
