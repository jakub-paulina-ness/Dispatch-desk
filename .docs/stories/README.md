# Dispatch desk — story board

Read **[S-00 contracts](S-00-contracts.md)** first. Status of the whole project: [`PLAN.md`](../../PLAN.md). Who owns files: [`TEAM.md`](../../TEAM.md).

Do not edit `instructions/` (kit). Do not invent T-15 or DSP-5. Runtime commands use `python`, not `python3`.

Layer A is what the jury ticks and is **done**. Layer B stories S-10…S-14 are **done**. Live yard on port 8770 is extra (confirm / undo / map).

## Board

| ID | Story | Owner | Layer | Status | Blocked on |
|---|---|---|---|---|---|
| [S-00](S-00-contracts.md) | Shared contracts | all | — | **done** | — |
| [S-01](S-01-agents-md.md) | `AGENTS.md` | Jakub | A graded | **done** | — |
| [S-02](S-02-dispatch-engine.md) | `dispatch.py` engine | Peťo | A graded | **done** | — |
| [S-03](S-03-dispatch-tests.md) | T-14 stays refused | Marek | A graded | **done** | — |
| [S-04](S-04-demo-runbook.md) | Must-show runbook | Peťo / Marian | A graded | **done** | — |
| [S-05](S-05-grok-stack.md) | Skill + hook + plugin + MCP + show_lab | Jakub / Marian | A graded | **done** | — |
| [S-10](S-10-html-desk.md) | HTML desk sections | Marek | B wow | **done** | — |
| [S-11](S-11-dispatcher-agent.md) | Dispatcher agent | Peťo / Marian | B wow | **done** | — |
| [S-12](S-12-driver-agent.md) | Electric driver + charge | Marian | B wow | **done** | — |
| [S-13](S-13-locations-data.md) | Locations + charger power | Jakub | B data | **done** | — |
| [S-14](S-14-thin-server.md) | Stdlib server on 8765 | Marian | B stretch | **done** | — |

## Also shipped (not originally on this board)

| Item | Owner | Status | Where |
|---|---|---|---|
| Live yard | Marek (+ Jakub map) | **done** | `desk.py`, `web/` on `http://127.0.0.1:8770/` |
| Presenter script | Ondrej | **done** | `presenter.md` |
| Issue skills | Marek | **done** | `.grok/skills/create-issue/`, `fix-issue/` — ISS-001 is **open** |
| Run-app skill | Marek | **done** | `.grok/skills/run-app/` |

## Owner cheat sheet (now)

| Person | Done | If we continue |
|---|---|---|
| Jakub | S-01, architecture, MCP, S-13, AGENTS.md | Docs: architecture header vs `instructions/`; hook split |
| Marek | S-03, S-10, live yard, extra skills | One assigner on `desk.py`; keep or retire `src/web/`; T-LOC-NOT-ENGINE test |
| Peťo | S-02, S-11 (git) | Engine contract if the board starts calling `dispatch_job` |
| Marian | S-05, S-02, S-04, S-11, S-12, S-14 (git) | Drive demo; 8765 thin desk or 8770 live yard |
| Ondrej | `presenter.md` | Voice script only |

## Mapping to architecture PRs

S-01 → PR-1 · S-02 → PR-2 · S-03 → PR-3 · S-04 → PR-4 · S-05 → PR-5 + PR-6 · S-14 → PR-8 (**done**). Live yard has no architecture PR. Keep Layer B out of `instructions/` and out of the assignment algorithm.
