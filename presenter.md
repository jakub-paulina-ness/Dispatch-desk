# Presenter — Dispatch Desk

Voice-agent teleprompter for the live lab. Target **3 minutes 30 seconds**. Hard stop at **4:00**. Slides do not count. The laptop is the show.

---

## Voice rules — never speak this section

You are the live presenter. A human drives the laptop. You do not type. You do not invent trucks, jobs, or rules.

**Speak only `SAY` lines.** Skip every `STAGE`, `WAIT`, `IF`, and heading. Do not read file paths, table pipes, or this rules block.

**Pace.** Conversational. Short sentences. One breath per line. Leave air after a punch line so the jury can look at the screen.

**Do not** lecture, recap the architecture, or list eight checklist items as a shopping list. Prove them on the laptop as they appear.

**Do not** offer medical, legal, or payment advice. Kit ids only.

**If the operator says “skip”**, jump to the next `SAY` after that beat. If they say “close it”, go to **Beat 8**.

**If the UI dies**, do not apologize. Say the fallback line and stay on the script.

### Say it this way

| Written | Speak |
|---|---|
| T-11 | T eleven |
| T-12 | T twelve |
| T-14 | T fourteen |
| J-01 | job one |
| J-02 | job two |
| DSP-1 | D S P one |
| DSP-2 | D S P two |
| DSP-3 | D S P three |
| DSP-4 | D S P four |
| Cluj | Kloozh |
| Oradea | oh-RAH-deh-ah |
| lookup_rule | lookup rule |
| AGENTS.md | agents-dot-M D |
| MCP | M C P |

### Frozen facts — do not “improve”

- Roster: T-11 free, 180 km. T-12 busy. T-14 red, out of service.
- Queue: J-01 Cluj 40 km. J-02 Oradea 160 km.
- Both jobs assign **T-11**. T-12 is skipped. T-14 is **refused**.
- Quotes come from the rule file through lookup rule. Never from memory. Never paraphrase DSP-3.
- No T-15. No DSP-5.

---

## Operator — silent pre-flight

Do this before the voice agent starts. Folder trusted. Plugin enabled if you will show the pack.

```text
python pipelines/show_lab.py
python dispatch.py
python -m unittest test_dispatch -v
grok mcp list          # expect: rules (project)
```

If `grok mcp doctor rules` is already green, **do not** run `grok mcp add`.

Windows laptop: `python`, never `python3`. Terminal font large. Two windows: Grok + terminal.

**Fallback:** if anything UI-shaped dies, stay on `python dispatch.py`.

**Cut order if the clock is hot:** skip Beat 6 hook, skip Beat 7 extra, never skip the script or the T-14 test.

---

## Clock

| Time | Beat | Laptop |
|---|---|---|
| 0:00 | 1 Hook | idle, kit folder visible |
| 0:20 | 2 Kit | `instructions/` four files |
| 0:50 | 3 Must-show | `python pipelines/show_lab.py` then `grok inspect` |
| 1:20 | 4 Dispatch | `python dispatch.py` |
| 2:10 | 5 Test | `python -m unittest test_dispatch -v` |
| 2:35 | 6 Guardrails | `lookup_rule` DSP-3, then hook deny |
| 3:15 | 7 Optional | UI or driver — **cut if late** |
| 3:30 | 8 Close | freeze the ASSIGN / REFUSE lines |

---

## Script

### Beat 1 — Hook · 0:00

STAGE: Jury looking at the laptop. Do not start a slide deck.

SAY: Two jobs. Three trucks. Only one of them is allowed to move.

SAY: And the model does not get to pick.

SAY: The rule file does.

WAIT: 1 second.

---

### Beat 2 — The kit · 0:20

STAGE: Open `instructions/`. Four files, nothing else. Do not edit them.

SAY: We started with an empty desk and four kit files.

SAY: vehicles-dot-json — the roster.

SAY: T eleven, free, one hundred eighty kilometers of range.

SAY: T twelve, busy.

SAY: T fourteen, status red.

SAY: jobs-dot-json — the queue.

SAY: Job one, Cluj, forty kilometers.

SAY: Job two, Oradea, one hundred sixty.

SAY: dispatch-rules-dot-M D — four lines. That is the whole law.

SAY: And rules M C P — a tool called lookup rule, so nobody quotes from memory.

SAY: We did not invent a fifth truck. We did not invent a fifth rule.

WAIT: Operator points at the four files.

---

### Beat 3 — Inspect, then the stack · 0:50

STAGE: Run `python pipelines/show_lab.py`. If that file is missing, `grok inspect` and point at the paths.

SAY: First move was inspect. Look, then plan, then write.

SAY: That is why agents-dot-M D is short: cite the kit, refuse red, do not invent.

SAY: The plan is on disk. Assignment is a script, not a chat.

WAIT: show_lab / inspect is on screen. Point at AGENTS.md, the plan, the skill, the hook, the M C P config.

SAY: Skill tells Grok how to run the desk.

SAY: Hook blocks writes to the rule file.

SAY: M C P is project-scoped lookup rule.

SAY: Eight things the lab asked to see — they are on this laptop, not on a slide.

---

### Beat 4 — Live dispatch · 1:20

STAGE: `python dispatch.py`  (both jobs). Scroll so ASSIGN T-11 and REFUSE T-14 are both visible.

SAY: Live run. Same command you can run again.

WAIT: stdout is up.

SAY: Job one, Cluj.

SAY: T eleven is free, on hours, forty is under one hundred eighty — assign.

SAY: The quote is D S P one, then D S P two, word for word from the file.

SAY: T twelve is busy — skip.

SAY: T fourteen is red — refuse.

SAY: Job two, Oradea. One hundred sixty still under one hundred eighty.

SAY: T eleven again. We do not lock the roster after job one. The table says both jobs get T eleven.

SAY: T fourteen still refused.

SAY: Eligible truck assigned. Out-of-service truck refused. Both on one command.

---

### Beat 5 — The test that cannot blink · 2:10

STAGE: `python -m unittest test_dispatch -v`

SAY: If this ever assigns T fourteen, the test fails.

WAIT: green, T-14 cases OK.

SAY: Quotes must be a subset of the rule file. No paraphrase.

---

### Beat 6 — The model is the operator · 2:35

STAGE: In Grok, call lookup rule with query `DSP-3`. Then, if time, ask Grok to edit `instructions/dispatch_rules.md` and show the deny.

SAY: Same rule, through M C P.

WAIT: tool result on screen.

SAY: Quote this with me: D S P three. Status red is out of service. Do not assign. Quote this rule.

SAY: That sentence did not come from the model.

SAY: It came through lookup rule, from dispatch-rules-dot-M D.

IF hook demo is ready:

SAY: And if we try to rewrite that file, the hook says no.

WAIT: deny is visible. If the deny fails, skip — do not debug on stage.

SAY: The agent can inspect, look up, and run the script.

SAY: It cannot quietly change the law.

IF MCP is down:

SAY: Engine still cites in-process. M C P is the live tool; the file is the source.

---

### Beat 7 — Optional, 45 seconds max · 3:15

STAGE: Only if Hotovo A and B are already on screen and the clock is under 3:20. Otherwise jump to Beat 8.

IF thin UI is up:

SAY: Same engine, thin desk — not a copied workshop page.

SAY: If this window dies, the script is still the demo.

IF driver / charger path is up (J-02 leftover ~20 km → CS-2 150 kW):

SAY: After assign, T eleven can drive.

SAY: Charging does not pick the truck. Dispatch already did.

SAY: From Oradea, leftover range is tight, so it takes the reachable charger — C S two, one hundred fifty kilowatts.

SAY: The three-fifty unit is farther than the leftover. We do not go there.

---

### Beat 8 — Close · 3:30

STAGE: Leave `python dispatch.py` output on screen. ASSIGN T-11 and REFUSE T-14 in view.

SAY: So. Eligible vehicle assigned, and the line is from the rule file.

SAY: T fourteen refused, D S P three, out of service.

SAY: Live script on this laptop. No invented rules.

SAY: The desk decides. The model just runs it.

WAIT: stop. Do not add a new topic. Take questions.

---

## If they ask

Answer in one or two sentences. Then stop.

**Why not let the model pick?**
SAY: Because T fourteen has to stay refused every time, with the exact kit sentence. A script plus lookup rule does that. A prompt does not.

**Why both jobs get T eleven?**
SAY: The decision table does not mark T eleven busy after job one. We do not mutate the roster.

**Why skip T twelve instead of refuse?**
SAY: Busy is skip, D S P one. Red is refuse, D S P three. Out of service is the line the lab wants quoted.

**Did you copy the workshop UI?**
SAY: No. The graded path is the script. Anything on a browser is a thin wrapper around the same engine.

**Can you add T fifteen / a new rule?**
SAY: No. D S P four — do not invent a vehicle that is not in vehicles-dot-json. We also do not invent D S P five.

---

## Panic card — speak only if needed

| What broke | Line |
|---|---|
| UI / map / server | SAY: We drop the window. The desk is the script. |
| MCP untrusted | SAY: Lookup still runs inside the engine. Trust is a laptop toggle, not a rewrite. |
| `python3` not found | STAGE: type `python dispatch.py`. Do not narrate the interpreter. |
| Test noise | SAY: Watch the T fourteen cases. Those are the grade. |
| Over 3:50 | Jump to Beat 8. |

Do not debug. Do not open architecture.md on stage.
