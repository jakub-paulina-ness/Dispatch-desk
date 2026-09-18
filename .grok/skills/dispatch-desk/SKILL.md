---
name: dispatch-desk
description: Assign jobs from the local roster and queue. Use when a dispatcher opens J-01 or J-02, asks to send T-11 / T-12 / T-14, or asks medical, legal, or payment advice. Slash command /dispatch-desk.
---

# Assign a job

1. If the user asks for a payout, a settlement, medical advice, a dose, or legal advice: refuse. Do not invent a rule id. Say the desk only assigns jobs from the roster. Stop.
2. Load `jobs.json` and `vehicles.json`. Do not guess a vehicle that is not in the roster.
3. Call MCP `lookup_rule` (server `rules`) with the gap (for example `free`, `range`, `red`, `invent`).
4. Decide only from the returned lines:
   - Status red → Refuse, quote DSP-3. T-14 stays refused.
   - Vehicle missing from `vehicles.json` → Refuse, quote DSP-4.
   - Not free or hours_ok false → Refuse, quote DSP-1.
   - Job km not less than range_km → Refuse, quote DSP-2.
   - Free, hours_ok, and km < range_km → Assign, quote DSP-1.
5. A recommendation is not a send. The dispatcher must confirm. Reply with Decision, vehicle id or Refuse, rule id, and the quoted rule line.
