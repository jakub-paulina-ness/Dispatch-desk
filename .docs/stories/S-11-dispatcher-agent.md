# S-11 Dispatcher agent

| Field | Value |
|---|---|
| **Owner** | Peťo |
| **Layer** | B — wow |
| **Status** | ready |
| **Blocked on** | [S-00](S-00-contracts.md). Real engine when S-02 exists; fixtures are enough to unblock S-10/S-12. |
| **Unblocks** | S-10 live board, S-12 ASSIGN stream |

## Goal

As the dispatcher, I want an agent loop that follows DSP-1…DSP-4 and **starts a driver only for ASSIGN**.

This is orchestration on top of Ondrej's engine, not a second assignment algorithm.

## Files

- `src/dispatcher.py` — load kit outcomes, emit DispatchEvent list, spawn/signal driver on ASSIGN
- `pipelines/fixtures/dispatch_events.json` — already seeded; keep it in sync with the engine

## Behavior

```text
events = []
for job in jobs:
    for outcome in dispatch_job(job, vehicles):   # or fixture
        events.append(DispatchEvent)
        if outcome.kind == "ASSIGN":
            start_driver(vehicle_id, job_id)      # S-12 process or in-proc
        # SKIP / REFUSE → no driver
```

- Call `src/dispatch.py` functions; do not reimplement DSP in this file.
- Until S-02 merges, emit the fixture as-is so Marek and Marian are not blocked.
- When engine exists, fill `quotes` from `lookup_rule` / `dispatch.lookup_rule`.
- Independent jobs: do not set T-11 to busy after J-01.

## Acceptance

- [ ] Six events, roster order, both jobs.
- [ ] `start_driver` invoked twice (J-01/T-11, J-02/T-11) and never for T-12 or T-14.
- [ ] Event `kind`/`dsp_ids` match S-00 table.
- [ ] No read of `locations.json` for eligibility.

## Parallel

S-04 runbook is your Layer A story. Dispatcher can be a thin loop; do not block the checklist on process spawning.

## Out of scope

LLM-in-the-loop assignment. Charging decisions. HTML.
