# Dispatch desk — who owns what

Five people, one laptop, one story. Judges score **what they can see run**. Git is for sharing and merging, not five different versions on stage.

Work only in this folder. Kit under `instructions/` is immutable. Do not invent a rule file. Do not invent T-15 or DSP-5. Interpreter is `python`, never `python3`.

Repo: https://github.com/jakub-paulina-ness/Dispatch-desk

The old P1–P5 branch table (`p2-ui`, `p3-grok`, …) is retired. Named owners and stories replaced it. Status of the work: `PLAN.md`.

## People (what they actually shipped)

Git authors on `main` mapped to the names in architecture / stories.

| Person | Git | Role | Shipped on this repo |
| --- | --- | --- | --- |
| **Jakub** | `jakub-paulina-ness` | Architect + Grok project rules | `.docs/specification/architecture.md`, stories/S-13, MCP `rules` in `.grok/config.toml`, `AGENTS.md`, later live-yard map motion |
| **Marek** | `marek-pilarcik-ness` | QA auto + this laptop | S-03 `tests/test_dispatch.py`, S-10 `src/web/`, live yard (`desk.py`, `web/`, confirm/undo/map), merge captain, `create-issue` / `fix-issue` / `run-app` |
| **Marian** | `mlapko-ness` | Integration + a lot of Layer A | Kit + early TEAM split, S-05 skill/hook/plugin/`show_lab.py`, S-02 engine, S-11 dispatcher, S-12 driver, S-04 `pipelines/DEMO.md` |
| **Peťo** | `Peter Zagora` | Engine + dispatcher (parallel) | S-02 / S-11 commits (`src/dispatch.py`, `src/dispatcher.py`) |
| **Ondrej** | `Ondrej Matija` | Presenter | `presenter.md`. Unassigned from S-02. |

Stories named Jakub for S-05 and Peťo for S-02/S-04. On git, Marian landed those files; Peťo also pushed engine/dispatcher. Treat the **files** as done regardless of who typed them.

## Current file ownership

Edit **only your files** unless you ping the owner. Kit: nobody.

| Person | May edit | Must not edit |
| --- | --- | --- |
| **Jakub** | `AGENTS.md`, `.docs/specification/`, `.docs/reference/` (except the four assignment copies — those are kit-shaped, do not “improve”), `.grok/skills/dispatch-desk/`, `.grok/hooks/protect*`, `.grok/plugins/dispatch-desk/`, `.grok/config.toml`, `pipelines/show_lab.py` | `instructions/`, engine DSP sentences |
| **Marek** | `tests/`, `test_dispatch.py`, `src/web/`, `desk.py`, `test_desk.py`, `web/` (live yard), `.grok/skills/create-issue/`, `fix-issue/`, `run-app/` | `instructions/`, inventing T-15 cases |
| **Marian** | `src/sim/`, `src/dispatcher.py` (shared with Peťo), `pipelines/DEMO.md`, live demo laptop wiring | `instructions/`, a second assigner |
| **Peťo** | `src/dispatch.py`, root `dispatch.py` shim, `src/dispatcher.py` | `instructions/`, hardcoded DSP sentence bodies |
| **Ondrej** | `presenter.md` | product code unless agreed |

Shared docs: `PLAN.md`, this file, `.docs/stories/` — anyone updates status; do not rewrite acceptance after the fact without the owner.

## Stories vs what landed

| Planned | Owner on the board | Actual |
| --- | --- | --- |
| S-00 contracts | all | **done** |
| S-01 AGENTS.md | Jakub | **done** |
| S-02 engine | Peťo (board); Marian + Peťo (git) | **done** — loads `instructions/` |
| S-03 tests | Marek | **done** |
| S-04 runbook | Peťo (board); Marian (git) | **done** — `pipelines/DEMO.md` |
| S-05 Grok stack | Jakub (board); Marian (git) | **done** — skill + hook + plugin, MCP project-scoped |
| S-10 HTML | Marek | **done** — `src/web/`, served on 8765 |
| S-11 dispatcher | Peťo / Marian | **done** |
| S-12 driver | Marian | **done** |
| S-13 locations | Jakub | **done** |
| S-14 thin server | Marian | **done** — `src/dispatch_server.py` on 8765 |
| Live yard | (not a story) | **done** freestyle — Marek, later Jakub — 8770 |
| Presenter | (not a story) | **done** — Ondrej |
| ISS-001 | — | **open** — extra live jobs, no kit edits |

## Git

Shared remote is already set. Marek’s checkout is the demo laptop (`C:\Users\P3503707\Downloads\Dispatch-desk`). `main` must always be demoable. Small PRs, green tests, no force-push except the captain.

```text
python dispatch.py
python -m unittest test_dispatch -v
python test_desk.py
python web/test_api.py
```

Branches that existed for stories (`story/S-03-dispatch-tests`, `story/S-10-html-desk`, `feature/dispatch-desk`, `ondrej`) are historical. New work: short branch, PR into `main`.

## Live demo — who does what

Order from `pipelines/DEMO.md` (3–4 min). One person talks.

1. **Peťo / Marian** — `python pipelines/show_lab.py` then `python dispatch.py`
2. **Marek** — `python -m unittest test_dispatch -v`
3. **Jakub** — `rules__lookup_rule` query `DSP-3`; point at skill / hook / plugin
4. **Marian / Marek** — optional live yard `http://127.0.0.1:8770/` or `python src/sim/driver.py J-02 --no-sleep`
5. **Ondrej** — `presenter.md` if a voice agent is driving the script
6. Stop. Questions from judges only.

Backup: `python dispatch.py`. If the page is down, do not debug on stage.

## If we continue — leftover owners

From `PLAN.md` Remaining:

| Leftover | Suggested owner |
| --- | --- |
| Wire live yard to `dispatch_job` (one assigner; T-12 SKIP vs Refuse) | Marek (`desk.py` / `web/`) + Peťo (engine contract) |
| Pick 8765 (S-14) vs 8770 (live yard) for the jury | Marian / Marek |
| Architecture header / KD-8 vs `instructions/` | Jakub (docs only unless the team wants a path migration) |
| Add T-LOC-NOT-ENGINE to `tests/test_dispatch.py` | Marek |
| Document hook split (`protect_rules` / `protect_vehicles` / `desk_guard`) | Jakub |
| ISS-001 extra live jobs | whoever takes `/fix-issue` |

## Do not polish

- New vehicles, cities, or rule ids
- Medical, legal, or payment advice
- Slides as the demo
- A second laptop with different code
- Editing kit files because it would look nicer
- `python3` in runnable commands

## Definition of done for the table

- Pass and refuse run live from `main` (`python dispatch.py`)
- Inspect shows AGENTS.md, skill, hook, MCP
- Confirm / undo / log can be shown on the live yard, or skipped if the CLI is the demo
- Tests green
- One person talks. The others stay quiet until questions
