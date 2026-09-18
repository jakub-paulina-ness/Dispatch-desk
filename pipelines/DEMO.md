# Dispatch desk — live demo runbook

Windows laptop. Interpreter is **`python`**, never `python3`.
Spoken `show_lab` command is **`python pipelines/show_lab.py` only** (no `.ps1` / `.sh`).
Peťo speaks the checklist. Marian drives. Others type their one command.

If UI dies: **continue on CLI**. Do not discuss. Say “fallback: `python dispatch.py`.”

---

## Stage 3 — laptop wiring (before the jury)

Do this once. Not a git commit. Do **not** type `grok mcp add` in the live slot if doctor is already green.

1. `python dispatch.py` — both jobs ASSIGN T-11, REFUSE T-14, quotes present.
2. `python -m unittest test_dispatch -v` — green; T-14 never ASSIGN.
3. `grok mcp doctor rules`
   - **Green** → do **not** `grok mcp add`. Show `grok mcp list` (`rules (project)`).
   - **Not green** (untrusted folder) → `grok --trust` or `/hooks-trust`, then doctor again.
   - Still failing Store stub → pin (laptop-local, commit only if the team agrees):

     ```text
     C:\Users\P3503318\AppData\Local\Programs\Python\Python313\python.exe
     ```

     in `.grok/config.toml` **and** the hook `command`. Not mid-demo.
4. Folder trust: `grok --trust` / `/hooks-trust`.
5. Plugin: `grok plugin enable dispatch-desk` (or Space in `/plugins`).
   Project skill + hook still show if the plugin is off.
6. Hook deny rehearsal: ask Grok to `search_replace` or `write` `instructions/dispatch_rules.md`. Expect deny. `Get-Content` of that file is allowed (hook does not parse `command`).

Existing `.grok/config.toml` **counts as MCP add done**. Jury evidence is `grok mcp list` + live `rules__lookup_rule` query `DSP-3`.

---

## Live clock (3–4 min)

| Time | Who | Type / say |
|---|---|---|
| 0:00 | Peťo | `python pipelines/show_lab.py` then `grok inspect` — eight must-show paths. List `instructions/` **before** claiming we wrote kit files. |
| 0:40 | Peťo | `python dispatch.py` — ASSIGN T-11, SKIP T-12, REFUSE T-14, quotes. |
| 1:20 | Marek | `python -m unittest test_dispatch -v` — T-14 stays refused. |
| 2:00 | Jakub | Grok: `rules__lookup_rule` query `DSP-3` (kit line). Point at plugin + hook. `/hooks` loaded. |
| 2:20 | Marian | Optional UI / driver. **Skip if dead.** |
| 2:40 | Jakub | “The decision is `dispatch_rules.md` through `lookup_rule`, not the model.” |
| 3:00 | Buffer | Re-run `python dispatch.py` if anyone blinks. If UI dead, skip it. |

Layer B (map / CS-2 150 kW) is **after Hotovo**, optional, **≤ 60 s**. Cut without guilt.

---

## Must-show — tick on the laptop

| ID | Show | Type this |
|---|---|---|
| **MS-1** inspect | Four kit files under `instructions/` | `python pipelines/show_lab.py` |
| **MS-2** AGENTS.md | Repo-root project instruction | `grok inspect` |
| **MS-3** plan | `.docs/specification/architecture.md` | open that file / `/plan` |
| **MS-4** skill | Project **and** plugin `SKILL.md` | paths from `show_lab`; `/skills` |
| **MS-5** hook | Project **and** plugin hooks; deny write | ask Grok to `write` `instructions/dispatch_rules.md` |
| **MS-6** MCP | `rules (project)` + live DSP-3 | `grok mcp list` then `rules__lookup_rule` query `DSP-3` |
| **MS-7** script | J-01 and J-02 → T-11 + quotes | `python dispatch.py` |
| **MS-8** test | T-14 never ASSIGN | `python -m unittest test_dispatch -v` |

Do **not** `grok mcp add` if doctor is green.

---

## Hotovo A / B / C

Evidence is **`python dispatch.py`** stdout (same command as MS-7 / MS-A/B).

| ID | Criterion | Look for |
|---|---|---|
| **MS-A** | Eligible assigned + quote from kit | `ASSIGN vehicle=T-11` and `RULE DSP-1:` / `RULE DSP-2:` lines ⊆ `instructions/dispatch_rules.md` |
| **MS-B** | T-14 refuse, cite DSP-3 | `REFUSE vehicle=T-14` and `RULE DSP-3:` equals `handle()` / `lookup_rule("DSP-3")` |
| **MS-C** | Live script; no invented rules | No slides. `git diff --ignore-cr-at-eol -- instructions/` empty. No DSP-5, no T-15. |

---

## Fallback

| Failure | What Marian says | What you type |
|---|---|---|
| HTML / server dies | “CLI is the demo.” | `python dispatch.py` |
| MCP untrusted | “Engine still cites via `handle()`.” Show `.grok/config.toml`. | still `python dispatch.py` |
| Plugin off | “Project skill and hook are on disk.” | `show_lab` paths `[4]` and `[5]` |
| Hook spawn hits Store `python` | Stop; pin `Python313\python.exe` **before** jury, not during. | — |

Rollback = last git revert, then `python dispatch.py`.

---

## Layer B (optional, after Hotovo, ≤ 60 s)

Only if Layer A is already ticked and the clock has a minute.

```text
python src/sim/driver.py J-02 --no-sleep
```

Look for `charger_id: CS-2` and `charger_power_kw: 150`. CS-4 is unreachable. Do not start a driver for T-14.

If `src/dispatch_server.py` is up: `http://127.0.0.1:8765` only. If it is not running, **do not start it in front of the jury**.

---

## Cut order if the dry-run exceeds 4 minutes

CLI + test + project MCP + AGENTS.md + skill + hook → plugin pack → UI / driver / server.

Never cut S-01…S-05. Cut S-14, then S-12, then S-10.
