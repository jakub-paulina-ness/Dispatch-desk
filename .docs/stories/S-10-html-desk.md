# S-10 HTML desk (multiple sections)

| Field | Value |
|---|---|
| **Owner** | Marek |
| **Layer** | B — wow |
| **Status** | done |
| **Blocked on** | [S-00](S-00-contracts.md) only. Use fixtures until S-11/S-14. |
| **Unblocks** | S-14 serves this page on 8765 |

## Goal

As the desk designer, I want an **original** HTML page with several sections that shows the kit, the DSP decision, and later live driver telemetry.

Do **not** copy workshop HTML/CSS/JS.

## Files

- `src/web/index.html` (and optional `desk.css` / `desk.js` next to it)
- May start as static files; S-14 will serve them from `127.0.0.1:8765`

## Sections (all required)

1. **Kit strip** — names the four `instructions/` files (inspect on screen).
2. **Job queue** — J-01 Cluj 40 km, J-02 Oradea 160 km.
3. **Fleet** — T-11 free 180 km, T-12 busy 90 km, T-14 red / out of service.
4. **Decision board** — ASSIGN / SKIP / REFUSE + `dsp_ids` and quotes when present.
5. **Driver telemetry** — speed, junction stop, drive kW, SOC, remaining range (bind TelemetryEvent).
6. **Charge** — `charger_id`, `charger_power_kw` from locations (CS-2 150 kW after Oradea). Show CS-4 350 kW as unreachable.

## Data

- S-14 serves this page from `127.0.0.1:8765`. Live yard on 8770 is a separate board.
- Telemetry: poll `/api/telemetry` or a fixture array. Empty panel is OK on day one; do not block section 1–4 on Marian.
- Chargers: read `.docs/reference/locations.json` (or a copy served as `/api/locations`). Show `power_kw` on each pin/row.

## Acceptance

- [x] Six sections visible without a backend.
- [x] Decision board can render the six fixture events (2 jobs × 3 trucks).
- [x] T-14 styled as REFUSE, not ASSIGN.
- [x] Charger list shows power in kW.
- [x] No workshop assets. No invented T-15.

## Parallel

S-03 tests are your Layer A story — keep that green first if time is tight. This page is droppable; CLI still wins the lab.
