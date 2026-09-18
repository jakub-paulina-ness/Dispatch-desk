# S-03 Automated tests

| Field | Value |
|---|---|
| **Owner** | Marek |
| **Layer** | A — graded (must-show 8) |
| **Status** | ready |
| **Blocked on** | [S-00](S-00-contracts.md) to **write** tests. **Merge** after S-02. |
| **Unblocks** | Live demo unittest; confidence for Layer B |

## Goal

As QA, I want `python -m unittest test_dispatch -v` to fail if T-14 is ever assigned, if T-12 is assigned, or if quotes are not kit lines.

## Files

- `tests/__init__.py` (empty)
- `tests/test_dispatch.py`
- `test_dispatch.py` shim: `from tests.test_dispatch import *`

Import engine with `sys.path.insert(src)` then `import dispatch` (same as root shim).

## Acceptance (from architecture test strategy)

- [ ] T-J01-T11 / T-J02-T11 — both jobs ASSIGN T-11
- [ ] T-14-J01 / T-14-J02 — never ASSIGN T-14; has REFUSE T-14
- [ ] T-12-NEVER — never ASSIGN T-12
- [ ] T-QUOTE-SUBSET / T-QUOTE-HANDLE / T-QUOTE-DSP3 / T-QUOTE-ASSIGN
- [ ] T-QUOTE-SRC — engine source has no DSP sentence bodies
- [ ] T-LOAD-PATH — kit is `instructions/`, not `.docs/reference/`
- [ ] T-NO-INVENT / T-ORDER / T-INDEPENDENT
- [ ] T-CLI-ALL / T-CLI-ONE / T-CLI-HELP / T-CLI-BAD
- [ ] Command: `python -m unittest test_dispatch -v`
- [ ] Tests do **not** load `locations.json` or assert charging

## Parallel with S-10

Write this file first. HTML (S-10) is a second story; do not block tests on CSS.

## Out of scope

Browser tests. Hook fixture may land with S-05 (T-HOOK-FIXTURE), not required to close S-03.
