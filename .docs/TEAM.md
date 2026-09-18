# Dispatch desk — rozdelenie práce (5 ľudí)

Track 4.1. Kit: `~/Downloads/grok/dispatch-desk`  
Spolu: Jakub architekt, Ondrej dev, Marek QA, Peťo QA, Marian (integrácia + live demo).

Jedna vec na stôl. Žiadny vymyslený rule file. Živý demo, nie slajdy.

## Kto čo vlastní

| Kto | Rola | Vlastní (hotové, keď…) | Odhad |
|---|---|---|---|
| **Jakub** | architekt + Grok stack | `/plan`, `AGENTS.md`, S-05 skill/hook/plugin/MCP/`show_lab.py`, sign-off že citáty idú z `lookup_rule` | **veľa** |
| **Ondrej** | — | Unassigned from S-02 | — |
| **Marian** | integrácia + demo | S-12 driver, S-14 thin server, live desk, beh dema pred porotou | stred |
| **Marek** | QA automat | `test_dispatch.py` — T-14 stays refused, T-11 assigned, quote je riadok z `dispatch_rules.md` | stred |
| **Peťo** | engine + QA acceptance | S-02 `dispatch.py`; checklist must-show, hook spec, runbook dema; S-11 event loop | **veľa** |

## Parallel stories

Work items: `.docs/stories/README.md`.  
Read `.docs/stories/S-00-contracts.md` before coding so Marek / Peťo / Marian / Ondrej / Jakub are not blocked on each other.

Locations for the driver sim (not kit, not a DSP rule): `.docs/reference/locations.json`.

## Čo nerobiť

- Needitovať `dispatch_rules.md`, `vehicles.json`, `jobs.json`, `rules_mcp.py`.
- Nevymýšľať auto T-15 ani pravidlo DSP-5.
- Nezačať písať AGENTS.md / script **pred** Jakubovým `/plan`.
- Nesliať to do priečinka reverse-engineering.

## Poradie (aby sa neblokovali)

### 0. Všetci spolu — 10 min
Inspect priečinka. Prečítať 4 kit súbory. Nikto nepíše kód.

### 1. Jakub — 15 min
`/plan` v Grok Build v `dispatch-desk`. Tím schváli. Až potom súbory.

Plán musí povedať:
- T-11 je jediné eligible (free + hours_ok + range).
- T-14 vždy refuse, citát DSP-3.
- Quote cez MCP `lookup_rule`, nie z hlavy.

### 2. Paralelne po pláne

**Jakub (S-01 + S-05)**
- `AGENTS.md` (krátke): inspect, len `dispatch_rules.md`, žiadne vymyslené vozidlo, refuse red.
- S-05 Grok stack: skill, protect-rules hook (project + plugin), MCP doctor/`lookup_rule`, `python pipelines/show_lab.py`. Plugin **bez** `.mcp.json`.

**Peťo (S-02 engine)**
- `dispatch.py`:
  - `python dispatch.py` — oba joby
  - `python dispatch.py J-01`
  - stdout: job, vehicle alebo refuse, rule id, quoted riadok
- Import `handle` z `rules_mcp.py` (lookup_rule). Žiadne hardcoded vety DSP-*.

**Marek** (môže písať testy hneď, assertuje správanie)
- `test_dispatch.py`
  - T-14 sa nikdy nepriradí (ani na J-01, ani na J-02)
  - J-01 a J-02 → T-11
  - quoted ⊆ `dispatch_rules.md`
  - T-12 sa nepriradí (busy)
- Beh: `python3 -m unittest test_dispatch -v`

**Peťo (S-04 + S-11, after S-02)**
- Checklist must-show (inspect, AGENTS, plan, skill, hook, MCP, script, test).
- Špec hooku pre Jakuba (S-05): PreToolUse deny na zápis `dispatch_rules.md` a `*_rules.md`.
- Runbook 3 minútového dema (čo kliknúť / spustiť, čo povedať).
- S-11: event loop on top of `dispatch_job` (not a second engine).

**Marian** (S-12 driver + S-14 server + demo)
1. S-12 electric driver (telemetry, CS-2 charge). Not assignment.
2. Optional `dispatch_server.py` / live desk (pôvodné UI, **nekopírovať** workshop HTML).
3. Integrácia: script Peťa + testy Mareka + Jakubov Grok stack na jednom stroji.
4. **Drive live demo** pred porotou (Peťo hovorí checklist, Marek ukáže test, Jakub ukáže skill/hook/MCP).

## Live demo (3–4 min) — kto čo robí

1. **Peťo** — `python pipelines/show_lab.py` / `grok inspect` (must-show).
2. **Peťo** — `python dispatch.py` (J-01/J-02 → T-11, citát).
3. **Marek** — `python3 -m unittest test_dispatch -v` (T-14 refused).
4. **Jakub** — MCP `lookup_rule` + skill/hook/plugin.
5. **Marian** — UI / driver, ak beží; inak CLI.
6. **Jakub** — jedna veta: rozhodnutie je z `dispatch_rules.md`, nie z modelu.

## Done when (lab)

- Eligible vozidlo assigned + citát.
- T-14 refused.
- Zoznam must-show na laptope.

## Jakub — S-05 backlog

- [ ] skill (project + plugin)
- [ ] hook (project + plugin)
- [ ] plugin pack (skill + hook, no `.mcp.json`)
- [ ] `grok mcp list` ukáže `rules` (config už existuje — nepridávať znova ak doctor je green)
- [ ] `python pipelines/show_lab.py`

## Marian — demo / wow

- [ ] S-12 driver
- [ ] live UI alebo čistý beh scriptu na druhom okne
- [ ] dry-run dema s Peťom
- [ ] záloha: ak padne UI, demo ide z `python dispatch.py`
