# Five people, one laptop, one story

Judges score **what they can see run**. Slides do not count. The live demo is on **one laptop**. Git is for sharing and merging, not for five different versions on stage.

Work only in `C:\Users\P3503707\Downloads\Dispatch-desk`. This folder has the track kit and the shared git remote. Do not invent a rule file. Do not edit kit files.

Repo: https://github.com/jakub-paulina-ness/Dispatch-desk

## GitHub

Shared remote is already set. P1 pushes `main`. Everyone else clones that URL.

If a teammate still needs write access: repo Settings → Collaborators, or:

```
gh repo add-collaborator USER --repo jakub-paulina-ness/Dispatch-desk --permission push
```

## Offline share (Teams / USB)

From this laptop:

```
git bundle create ..\hackathon-dispatch-desk.bundle main
```

Everyone else:

```
git clone hackathon-dispatch-desk.bundle hackathon-dispatch-desk
cd hackathon-dispatch-desk
```

The bundle is a snapshot. Prefer the GitHub remote.

## How to join

1. Send your GitHub username to the captain (P1).
2. Wait for the invite, then:

```
git clone https://github.com/jakub-paulina-ness/Dispatch-desk.git
cd Dispatch-desk
git checkout -b pN-your-role
python test_desk.py
python web/server.py
```

3. Edit **only your files**. Another person's file = issue or ping the owner.
4. Open a PR into `main`. P1 merges. `main` must always be a working demo.

## Branches

| Branch | Who | Purpose |
| --- | --- | --- |
| `main` | P1 merges | Always demoable. Nobody force-pushes except P1. |
| `p2-ui` | P2 | Look, Assign vs Refuse readable from across the table |
| `p3-grok` | P3 | AGENTS.md, skill, hook, plugin, MCP |
| `p4-live` | P4 | Confirm, undo, log, "if this went live" |
| `p5-tests` | P5 | desk.py, tests, off-scope, quotes |

Rule: small PRs, one change, green tests. Kit files are not edited.

## File ownership

If two people edit the same file, we lose to a merge conflict, not to the demo.

| Person | May edit | Must not edit |
| --- | --- | --- |
| **P1 Demo captain** | `README.md`, `TEAM.md`, merges to `main` | Product code without agreement |
| **P2 UI** | `web/index.html`, `web/styles.css`, `web/app.js`, `web/display.json` | `desk.py`, kit, `.grok/` |
| **P3 Grok pack** | `AGENTS.md`, `.grok/**` | `web/`, `desk.py`, kit |
| **P4 Live ops** | `web/server.py` | `web/app.js` (send P2 the exact copy/API), kit |
| **P5 Rules + tests** | `desk.py`, `test_desk.py`, `web/test_api.py` | UI, kit, `.grok/` |

Kit (nobody): `dispatch_rules.md`, `vehicles.json`, `jobs.json`, `rules_mcp.py`.

If P4 needs a UI change (bigger Confirm, a log row), file an issue for P2: what to add, the exact text, when the button is disabled. P2 draws it. P4 owns the API.

---

## P1 — Demo captain / laptop

**Goal:** 90 seconds, one story, nothing missing on stage.

Git user: Marek (`marek-pilarcik-ness`). This is the demo laptop.

### You do

- Invite people to the repo.
- Merge PRs into `main`. After every merge: `python test_desk.py` and `python web/test_api.py`.
- Demo setup: browser on `http://127.0.0.1:8770/`, `grok inspect` next to it, this folder open.
- Freeze **15 minutes before the demo**. No more merges.

### Script (memorize it)

1. "Dispatch desk. We assign a job from the roster. A red vehicle is refused."
2. Click **J-01** → Assign T-11, quote DSP-1 → **Confirm send**.
3. Click **T-14** → Refuse, quote DSP-3.
4. Point at `AGENTS.md`, the skill, the hook, MCP `lookup_rule` (`grok inspect`).
5. Stop. Wait for questions.

"If this went live": the dispatcher A. Pop must Confirm before it sends. Undo last send. The log is `dispatch.log`.

Backup: `python desk.py --demo`

### Done when

- One laptop, one tab with the board, one with inspect, one with AGENTS.md.
- You can say it in 90 seconds with no slides.
- You can answer: who clicks, how to undo, what goes in the log.

---

## P2 — UI / Assign vs Refuse from three meters

**Goal:** a judge across the table sees Assign vs Refuse immediately.

### You do

- Color, type, layout. Dark ops board. Not Alder Health parchment.
- T-14 must read as out of service at a glance.
- Confirm is the largest button on the page. Disabled when the decision is Refuse.
- After Confirm, T-11 looks busy with no confusion.
- Mobile 375px and desktop 1280px. The demo is a laptop; the layout must not break.
- No new cities, vehicles, or rule text. Kit fields plus chrome only.

### Polish list

1. Decision card: Assign green, Refuse red, type about 28px+.
2. Roster: T-14 red badge "Out of service", T-12 amber "Busy", T-11 green "Free".
3. "Quoted from DSP-x" must be readable, not grey on grey.
4. Ask the desk placeholder stays *What should we pay the driver?* — that is the off-scope demo.
5. Nothing that looks like a slide (no hero "Welcome to our solution").

### Done when

- Three-meter test: someone behind you can say Assign or Refuse without reading a paragraph.
- `python web/test_api.py` still passes (you do not change the API).

---

## P3 — Grok Build pack

**Goal:** `grok inspect` lists everything judges asked for, and you can point at it in 15 seconds.

### You do

- `AGENTS.md` — short, hard rules. No essay.
- Skill `.grok/skills/dispatch-desk/SKILL.md` — 5 steps, `lookup_rule`, T-14 = DSP-3.
- Hook `.grok/hooks/desk_guard.py` — block off-scope advice; deny kit-file edits.
- Plugin `.grok/plugins/dispatch-desk/` — skill + hook + MCP in one pack.
- `.grok/config.toml` — `rules` MCP + plugin enabled.

### Polish list

1. Run `grok inspect` after every change. It must show: project instructions, skill `dispatch-desk`, plugin `dispatch-desk`, MCP `rules`, hook.
2. `grok plugin list` may falsely say "none". Show **inspect**, not plugin list.
3. The skill must not invent a rule id. Off-scope = no fake DSP.
4. Prepared line: "The hook blocks a payout prompt and an edit to `dispatch_rules.md`."
5. If there is time: in a Grok session call `lookup_rule` with query `red` → DSP-3.

### Done when

- Inspect checklist is complete.
- You can click AGENTS.md → SKILL.md → desk_guard.py → rules_mcp.py without searching.

---

## P4 — If this went live

**Goal:** a judge believes this could hang on a dispatch wall.

Judging row: *who must click before it sends, how you undo a bad change, what you would write in a log.*

### You do

- `web/server.py`: Confirm, Undo, busy overlay, `dispatch.log`.
- The API does not change what a decision means. `desk.py` decides.
- Copy for P2 (issue, not a direct JS edit): "Dispatcher A. Pop must click before it sends."

### Polish list

1. Confirm without Assign → nothing is sent (T-14 confirm must fail).
2. Undo returns T-11 to free. Kit files stay the same.
3. Log line: time, dispatcher, job, vehicle, decision, rule id, quoted line.
4. `dispatch.log` is gitignored. The server owns the format.
5. No payout, no amount, no "we will pay".

### Done when

- You can say it in one sentence on stage when P1 turns to you.
- `python web/test_api.py` — confirm / undo / T-14 tests green.

---

## P5 — Rules + tests

**Goal:** T-14 stays refused while others polish the UI. No invented rule.

### You do

- `desk.py` — assign and refuse from the kit only.
- `test_desk.py` — lock the demo cases.
- `web/test_api.py` — the UI layer still quotes the same rules.

### Polish list

1. `test_t14_stays_refused` is sacred. It must not fail.
2. J-01 → Assign T-11, DSP-1, quote is a substring of `dispatch_rules.md`.
3. T-12 → Refuse DSP-1. T-99 → Refuse DSP-4.
4. Off-scope ("What should we pay the driver?") → Off desk, `rule == ""`.
5. Hook test: payout prompt returncode 2; edit `dispatch_rules.md` denied.
6. After every PR from someone else: run both test suites before P1 merges.

### Done when

- `python test_desk.py` and `python web/test_api.py` green on clean `main`.
- On a judge question you can open `dispatch_rules.md` and show the line that just ran on screen.

---

## Do not polish

- New vehicles, cities, or rule ids.
- Medical, legal, or payment advice.
- Slides.
- A second laptop "just in case" with different code.
- Editing kit files because it would look nicer.

## Definition of done for the table

- Pass and refuse run live from `main`.
- Inspect shows AGENTS.md, skill, hook, MCP.
- Confirm / undo / log can be shown in one sentence.
- Tests green.
- One person talks. The other four stay quiet until questions.
