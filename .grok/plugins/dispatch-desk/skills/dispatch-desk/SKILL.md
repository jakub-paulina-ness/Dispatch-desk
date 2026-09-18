---
name: dispatch-desk
description: Assign kit jobs from instructions/jobs.json to instructions/vehicles.json using DSP-1..DSP-4. Use when dispatching fleet jobs, citing dispatch rules, running lookup_rule, or demonstrating the dispatch desk. Trigger phrases: dispatch, assign vehicle, T-14, lookup_rule.
---

# Dispatch desk

Kit under `instructions/` is immutable. Quotes come from `rules__lookup_rule`, never from memory. Interpreter is `python`, not `python3`. Do not invent T-15 or DSP-5. Do not copy workshop HTML.

## Steps

1. `list_dir` / read the four kit files under `instructions/`: `dispatch_rules.md`, `vehicles.json`, `jobs.json`, `rules_mcp.py`. Write nothing yet.
2. Call `rules__lookup_rule` with query `DSP-1`, then `DSP-2`, then `DSP-3`. Do not recite rules from memory.
3. Run `python dispatch.py` (both jobs) or `python dispatch.py J-01` for one job.
4. Run `python -m unittest test_dispatch -v`.
5. Never edit `dispatch_rules.md`, `*_rules.md`, kit JSON, or `rules_mcp.py`.
6. Never invent a vehicle. Only T-11, T-12, T-14.

T-14 is always refuse; the DSP-3 line must be the `lookup_rule` hit. Both jobs assign T-11.

## Demo laptop

MCP is project-scoped in `.grok/config.toml`. If `grok mcp doctor rules` is green, do not `grok mcp add` — show `grok mcp list` (`rules (project)`).

Plugin packs skill + hook only (no `.mcp.json`). Enable: `grok plugin enable dispatch-desk` or Space in `/plugins`, after folder trust (`grok --trust` / `/hooks-trust`). Project `.grok/skills/` and `.grok/hooks/` still show if the plugin is off.
