# S-05 Grok stack (skill, hook, plugin, MCP, show_lab)

| Field | Value |
|---|---|
| **Owner** | Jakub |
| **Layer** | A — graded (must-show 4, 5, 6 + show_lab) |
| **Status** | done |
| **Blocked on** | [S-00](S-00-contracts.md) and architecture hook/skill contract. **Not** blocked on S-04. MCP config already exists. |
| **Unblocks** | Must-show on the laptop; S-12 can proceed in parallel |

## Goal

As Grok-stack owner, I want skill + protect-rules hook shipped twice (project + plugin), live `rules__lookup_rule`, and `python pipelines/show_lab.py` printing the eight paths.

## Files

- `.grok/skills/dispatch-desk/SKILL.md`
- `.grok/hooks/protect-rules.json` + `protect_rules.py`
- `.grok/plugins/dispatch-desk/` (`plugin.json`, same skill, same hook) — **no** `.mcp.json` in v1
- `pipelines/show_lab.py`
- Optional T-HOOK-FIXTURE with Marek

Do not regress `.grok/config.toml`: `command = "python"`, `args = ["instructions/rules_mcp.py"]`.

## Acceptance

- [ ] Skill YAML frontmatter `name` + `description`; steps: inspect kit → `lookup_rule` → `python dispatch.py` → unittest; never edit kit; never invent vehicles.
- [ ] Hook matcher includes `write`. Command uses `${GROK_WORKSPACE_ROOT}` / `${GROK_PLUGIN_ROOT}`. Basename deny on `dispatch_rules.md` / `*_rules.md`. Deny JSON on exception (do not fail-open).
- [ ] `grok mcp list` shows `rules (project)`. Live `lookup_rule` query `DSP-3` returns the kit line.
- [ ] If doctor is already green, do **not** `grok mcp add` in the demo.
- [ ] `python pipelines/show_lab.py` prints MS-1…8 paths even if some files are still missing.
- [ ] Plugin enable path documented; project skill+hook still show if plugin is off.

## Parallel

S-01 `AGENTS.md` is your other Layer A story. This stack is already on `main`. S-12/S-14 stay Marian’s.

## Out of scope

Rewriting `dispatch.py`. Copied workshop HTML. Plugin `.mcp.json`.
