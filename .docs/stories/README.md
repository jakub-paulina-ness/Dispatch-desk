# Dispatch desk — story board

Read **[S-00 contracts](S-00-contracts.md)** first. That file is the freeze so five people can work at once.

Do not edit `instructions/` (kit). Do not invent T-15 or DSP-5. Runtime commands use `python`, not `python3`.

## How to parallelize

```text
Everyone reads S-00
        │
        ├── Jakub   S-01 AGENTS.md
        │           S-05 skill/hook/plugin/MCP/show_lab
        ├── Marek   S-03 tests (done on main; 18 T-* green)
        │           S-10 HTML (done on main; fixtures until S-14)
        ├── Peťo    S-02 engine               ← Marek tests against this stdout
        │           S-04 runbook + hook spec
        │           S-11 dispatcher (can emit fixture events before S-02 lands)
        └── Marian  S-12 driver (fixture ASSIGN events + locations.json)
                    S-14 thin server last (needs S-02 + S-10)
```

**S-13 locations** is done. Driver and HTML load `.docs/reference/locations.json`.

## Board

| ID | Story | Owner | Layer | Status | Blocked on |
|---|---|---|---|---|---|
| [S-00](S-00-contracts.md) | Shared contracts | all | — | **ready** | — |
| [S-01](S-01-agents-md.md) | `AGENTS.md` | Jakub | A graded | **done** | plan sign-off |
| [S-02](S-02-dispatch-engine.md) | `dispatch.py` engine | Peťo | A graded | **done** | plan sign-off (not S-01) |
| [S-03](S-03-dispatch-tests.md) | T-14 stays refused | Marek | A graded | **done** | contract; merge after S-02 |
| [S-04](S-04-demo-runbook.md) | Must-show runbook | Peťo | A graded | ready | plan sign-off |
| [S-05](S-05-grok-stack.md) | Skill + hook + plugin + MCP + show_lab | Jakub | A graded | **done** | S-00 (not S-04) |
| [S-10](S-10-html-desk.md) | HTML desk sections | Marek | B wow | **done** | S-00 only (mock data OK) |
| [S-11](S-11-dispatcher-agent.md) | Dispatcher agent | Peťo | B wow | **done** | S-00; wire engine when S-02 exists |
| [S-12](S-12-driver-agent.md) | Electric driver + charge | Marian | B wow | **done** | S-00 + S-13; fixture ASSIGN OK |
| [S-13](S-13-locations-data.md) | Locations + charger power | Jakub | B data | **done** | — |
| [S-14](S-14-thin-server.md) | Stdlib server | Marian | B stretch | ready | S-02 + S-10; cut if demo > 4 min |

Layer A is what the jury ticks. Layer B is the live desk. If time slips, cut S-14 then S-12 then S-10. Never cut S-01…S-05.

## Owner cheat sheet

| Person | Start now | Then | Last |
|---|---|---|---|
| Jakub | S-01 **and S-05** | quote sign-off on S-02 | spoken demo line + MCP/skill/hook |
| Ondrej | — (unassigned from S-02) | — | — |
| Marek | S-03 **and** S-10 **done** | hook HTML to real events | unittest in live demo |
| Peťo | **S-02**, S-04, then S-11 | hook deny rehearsal | CLI + open the demo |
| Marian | S-12 | S-14 if green | drive the laptop / UI |

## Mapping to architecture PRs

S-01 → PR-1 · S-02 → PR-2 · S-03 → PR-3 · S-04 → PR-4 · S-05 → PR-5 + PR-6 · S-14 → PR-8. Layer B stories have no architecture PR yet; keep them out of `instructions/` and out of the assignment algorithm.
