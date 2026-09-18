# Dispatch desk — rozdelenie práce (5 ľudí)

Track 4.1. Kit: `~/Downloads/grok/dispatch-desk`  
Spolu: Jakub architekt, Ondrej dev, Marek QA, Peťo QA, Marian (integrácia + live demo).

Jedna vec na stôl. Žiadny vymyslený rule file. Živý demo, nie slajdy.

## Kto čo vlastní

| Kto | Rola | Vlastní (hotové, keď…) | Odhad |
|---|---|---|---|
| **Jakub** | architekt | `/plan` schválený, `AGENTS.md`, rozhodovací poriadok DSP-1→4, sign-off že citáty idú z `lookup_rule` | stred |
| **Ondrej** | dev | `dispatch.py` — priradí J-01/J-02 na T-11, T-14 refuse + citát DSP-3 | stred |
| **Marian** | integrácia + demo | plugin (skill+hook+MCP), `grok mcp add`, live desk, `show_lab.sh`, beh dema pred porotou | **veľa** |
| **Marek** | QA automat | `test_dispatch.py` — T-14 stays refused, T-11 assigned, quote je riadok z `dispatch_rules.md` | stred |
| **Peťo** | QA acceptance | checklist must-show, manuálny beh, hook naozaj blokuje zmenu rules, runbook dema | stred |

Marian nie je „pomocník“. Bez neho nie je plugin, MCP na laptope, stránka/script naživo ani zoznam pre porotu.

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

**Jakub**
- `AGENTS.md` (krátke): inspect, len `dispatch_rules.md`, žiadne vymyslené vozidlo, refuse red.
- Draft skill text pre Mariana (kroky: inspect → lookup_rule → `python3 dispatch.py`).

**Ondrej**
- `dispatch.py`:
  - `python3 dispatch.py` — oba joby
  - `python3 dispatch.py J-01`
  - stdout: job, vehicle alebo refuse, rule id, quoted riadok
- Import `handle` z `rules_mcp.py` (lookup_rule). Žiadne hardcoded vety DSP-*.

**Marek** (môže písať testy hneď, assertuje správanie)
- `test_dispatch.py`
  - T-14 sa nikdy nepriradí (ani na J-01, ani na J-02)
  - J-01 a J-02 → T-11
  - quoted ⊆ `dispatch_rules.md`
  - T-12 sa nepriradí (busy)
- Beh: `python3 -m unittest test_dispatch -v`

**Peťo**
- Checklist must-show (inspect, AGENTS, plan, skill, hook, MCP, script, test).
- Špec hooku pre Mariana: PreToolUse deny na zápis `dispatch_rules.md` a `*_rules.md`.
- Runbook 3 minútového dema (čo kliknúť / spustiť, čo povedať).

**Marian** (hlavný balík)
1. `grok mcp add --scope project rules -- python3 rules_mcp.py` (trust áno).
2. Skill `.grok/skills/dispatch-desk/SKILL.md` (z Jakubovho draftu).
3. Hook `.grok/hooks/` podľa Peťovej špecifikácie.
4. Plugin `.grok/plugins/dispatch-desk/` = skill + hook + `.mcp.json`.
5. Live demo: `dispatch.py` naživo, alebo tenký `dispatch_server.py` (pôvodné UI, **nekopírovať** workshop HTML).
6. `show_lab.sh` — vypíše must-show cesty.
7. Integrácia: script Ondreja + testy Mareka prechádzajú na jednom stroji.
8. **Drive live demo** pred porotou (Peťo hovorí checklist, Marek ukáže test).

## Live demo (3–4 min) — kto čo robí

1. **Peťo** — `./show_lab.sh` / `grok inspect` (must-show).
2. **Ondrej** — `python3 dispatch.py` (J-01/J-02 → T-11, citát).
3. **Marek** — `python3 -m unittest test_dispatch -v` (T-14 refused).
4. **Marian** — MCP `lookup_rule` + plugin / prípadne UI.
5. **Jakub** — jedna veta: rozhodnutie je z `dispatch_rules.md`, nie z modelu.

## Done when (lab)

- Eligible vozidlo assigned + citát.
- T-14 refused.
- Zoznam must-show na laptope.

## Marian — tvoj backlog (ak ti znova dajú málo)

- [ ] MCP add + `grok mcp list` ukáže `rules`
- [ ] skill
- [ ] hook
- [ ] plugin pack
- [ ] show_lab.sh
- [ ] live UI alebo čistý beh scriptu na druhom okne
- [ ] dry-run dema s Peťom
- [ ] záloha: ak padne UI, demo ide z `python3 dispatch.py`
