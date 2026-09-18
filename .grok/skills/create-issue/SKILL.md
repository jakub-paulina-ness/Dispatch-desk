---
name: create-issue
description: >
  File a new repo issue as markdown under .docs/issues/ with enough detail
  for a later fixer agent to implement it. Use when the user wants to create
  an issue, file a bug, open a ticket, write a .docs/issues note, or runs
  /create-issue. Do not implement the fix.
argument-hint: "<title or bug description>"
---

# Create issue

Write one markdown file under `.docs/issues/`. That file is the handoff for
a later fixer skill. Do not implement the fix. Do not create a GitHub
issue. Do not edit `.docs/stories/` or `instructions/`.

## Issue file

Path: `.docs/issues/ISS-NNN-slug.md`

- `NNN` is the next unused integer, zero-padded to 3 digits
- `slug` is the title in lowercase hyphenated ASCII, max 40 characters

```markdown
---
id: ISS-001
title: Short imperative title
status: open
priority: high | medium | low
type: bug | feature | chore
created: YYYY-MM-DD
area: engine | web | tests | docs | skill | other
files:
  - path/relative/to/repo
---

# ISS-001 Short imperative title

## Handoff

Implement this issue from this file. Do not expand scope. Set `status: done`
only after every acceptance item is true.

## Problem

What is wrong or missing. Cite paths and symbols you actually read.

## Expected

Correct behavior after the fix.

## Actual

What happens now. Include command output or a file excerpt when you have it.

## Repro

1. `python ...`

## Files

- `path` — why the fixer must touch or read it

## Acceptance

- [ ] Observable check the fixer can prove (command, file state, or UI)

## Constraints

- Hard rules from `AGENTS.md` / `Agents.md` that apply to this change

## Out of scope

- Nearby work that must not land in this ticket

## Verify

- Commands to run after the fix (`python -m unittest ...`)
```

`status` on create is always `open`. `/fix-issue` sets `in_progress` while
working, then `done` when Acceptance is met. This skill does not.

Default `priority` to `medium` when the user does not say. Pick `type` from
the request: broken behavior is `bug`, new behavior is `feature`, otherwise
`chore`.

## Steps

1. If the user did not describe a problem, ask once what to file, then stop
   until they answer.
2. Inspect the repo. Read the named files. Run a cheap repro command when it
   clarifies Expected / Actual. Fill those sections from the tree, not from
   memory.
3. List `.docs/issues/`. Parse `ISS-(\d+)` from filenames and from `id:`
   frontmatter. Next id is max+1. If the folder is missing or empty, use
   `ISS-001`.
4. If an **open** issue already covers the same change, show that path and
   do not write a duplicate.
5. Write the new file with the template above. Every section is required.
   Write `none` only when a section truly does not apply.
6. Put in **Constraints** the repo hard rules that apply to this change
   (kit lock, no invented vehicles or rules, `python` not `python3`,
   stdlib-only engine). Read them from `AGENTS.md` / `Agents.md`; do not
   invent extra rules.
7. Tell the user the path, the id, and a 2–4 line summary. Stop.

## Rules

- One problem per file. Split independent bugs into separate ids.
- Quotes, line numbers, and command output must come from files or a
  command you ran. If a fact is unverified, say so in the issue.
- Write the issue in English unless the user asked for another language.
- Do not edit source to confirm a theory. Do not start the fix.
- Do not commit unless the user asked to commit the issue file.
