# Dispatch desk requirements

Source: https://grok-enablement-workshop.grok.me/modules/hackathon/fleet  
Module 4.1 — Grok Enablement Workshop (hackathon track)

## Brief

Build a dispatch desk. Inputs are a vehicle roster and a job queue. For each job, assign a vehicle that is free, within range, and inside operating hours. If no vehicle qualifies, refuse the assignment and cite the dispatch rules. Do not invent vehicles or rules.

Use only the files on this track. Do not invent a rule file.

## Kit files

| File | Role |
|---|---|
| `vehicles.json` | roster |
| `jobs.json` | queue |
| `dispatch_rules.md` | rules |
| `rules_mcp.py` | reads the rules file |

MCP setup (so Grok can read the rule file):

```
grok mcp add --scope project rules -- python3 rules_mcp.py
```

If Grok asks to trust the folder, say yes.

## Must show

- inspect: look at the folder before writing files
- AGENTS.md: short rules file for Grok Build
- plan: agree a plan before it writes files
- a skill: short how-to file Grok Build reads
- a hook: check that runs before Grok Build does something
- MCP lookup_rule: tool that reads the rule file
- a script you can run again
- a test: T-14 stays refused

You may pack skill + hook + MCP into one plugin.

## Done when

- An eligible vehicle is assigned and the rule is cited.
- Vehicle T-14 is refused.
- You can show the list above on the laptop.

End with a live demo. Slides do not count. No real customer data. No medical, legal, or payment advice.
