---
name: fix-issue
description: >
  Pick the next free open issue under .docs/issues/, implement it, and mark
  it done so later agents skip it. Use when the user wants to fix an issue,
  pick the next ticket, resolve ISS-NNN, or runs /fix-issue.
argument-hint: "[ISS-NNN]"
---

# Fix issue

Issue format lives in `.grok/skills/create-issue/SKILL.md`. This skill only
picks, implements, and closes. One issue per run.

## Pick

1. List `.docs/issues/`. Read every `ISS-*.md` frontmatter. Ignore
   `README.md` and other non-issue files.
2. **Free and unresolved** means `status: open` (missing `status` counts as
   `open`). Skip `done` and `in_progress`.
3. Choose the lowest `ISS-NNN`. If the user named an id, use that file
   instead: allowed when `open` or `in_progress` (unstick). Refuse `done`
   unless they explicitly ask to reopen.
4. If nothing is free, say so and stop. Do not invent an issue.

## Claim then fix

5. Set `status: in_progress` on that file **before** any source edit. That
   is the lock: another `/fix-issue` run must skip it.
6. The issue file is the spec. Implement Acceptance only. Honor Out of
   scope and Constraints. Also honor `AGENTS.md` / `Agents.md` (kit lock,
   no T-15, no DSP-5, `python` not `python3`).
7. Do not edit `instructions/`. Do not expand into a second issue.

## Close or release

8. Run every command in **Verify**. Tick an Acceptance box only when that
   check is true.
9. **Success:** set `status: done`, tick every Acceptance item, append
   **Resolution** (date, files changed, verify commands and results).
   `done` is the ignore signal for the next agent.
10. **Failure or blocked:** set `status: open` again so the ticket is free.
    Do not leave `in_progress`. Do not set `done`. Tell the user why.
11. Tell the user the id, path, what changed, and the new status. Do not
    commit unless they asked. Do not start another issue.

## Resolution block

```markdown
## Resolution

- date: YYYY-MM-DD
- files: path, path
- verify: `command` → pass | fail
```

## Rules

- Never pick `status: done`.
- Never mark `done` if any Acceptance item is unproven or any Verify
  command failed.
- Do not create issues (that is `/create-issue`).
