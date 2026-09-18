# Northbound · Dispatch desk

Grok Enablement Workshop, track 4.1. Assign jobs from the roster and the queue. Refuse vehicles that are out of service.

Work in this folder (`Dispatch-desk`). Kit files from the track page live under `instructions/`. Do not invent a rule file.

One working agent. Live demo, not slides. Kit files are the only source of rules.

## Run

```
python test_desk.py
python web/test_api.py
python web/server.py
```

Board: http://127.0.0.1:8770/

Backup if the page is down: `python desk.py --demo`

## Demo in 90 seconds

1. Track: assign from the roster, refuse anything red.
2. Pass: J-01 → Assign T-11, quote DSP-1, Confirm send.
3. Refuse: T-14 → Refuse, quote DSP-3.
4. Point at AGENTS.md, the skill, the hook, MCP `lookup_rule`.
5. Stop.

## Team

Roles, branches, and file ownership: [TEAM.md](TEAM.md)

## Kit (do not edit)

- `instructions/vehicles.json` — T-11 free, T-12 busy, T-14 red
- `instructions/jobs.json` — J-01 Cluj 40 km, J-02 Oradea 160 km
- `instructions/dispatch_rules.md` — DSP-1 … DSP-4
- `instructions/rules_mcp.py` — `lookup_rule`
