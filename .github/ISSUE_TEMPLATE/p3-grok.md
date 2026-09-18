---
name: P3 Grok pack
about: inspect shows AGENTS.md, skill, hook, MCP, plugin
labels: p3-grok
---

## Goal

`grok inspect` lists every required artifact. You can point at them in 15 seconds.

## Owns

`AGENTS.md` `.grok/**`

## Done when

- [ ] inspect: project instructions, skill dispatch-desk, plugin dispatch-desk, MCP rules, hook
- [ ] Skill calls lookup_rule. T-14 → DSP-3. No invented rule id
- [ ] Hook blocks payout prompts and kit-file edits
- [ ] Talking path: AGENTS.md → SKILL.md → desk_guard.py → rules_mcp.py
- [ ] Demo uses inspect, not `grok plugin list`
