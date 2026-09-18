# S-00 Shared contracts

| Field | Value |
|---|---|
| **Owner** | All (Jakub freeze) |
| **Status** | **done** |
| **Blocked on** | nothing |

This is the file you implement against. Do not wait for someone else's PR if your story says "S-00 only".

## Invariants

1. Kit under `instructions/` is immutable: `dispatch_rules.md`, `vehicles.json`, `jobs.json`, `rules_mcp.py`.
2. Only vehicles `T-11`, `T-12`, `T-14`. Only jobs `J-01`, `J-02`. Only rules DSP-1…DSP-4.
3. Quotes come from `handle()` / `lookup_rule`, never from model memory, never hardcoded DSP sentences in `src/dispatch.py`.
4. Do not mutate roster between jobs. Both jobs ASSIGN T-11.
5. Commands on this laptop: `python`, never `python3`.
6. Charging, speed, junctions, kW are **telemetry after ASSIGN**. They must not change who gets the job.

## Frozen outcomes (Layer A)

| Job | T-11 | T-12 | T-14 | Result |
|---|---|---|---|---|
| J-01 Cluj 40 km | ASSIGN | SKIP busy (DSP-1) | REFUSE red (DSP-3) | T-11 |
| J-02 Oradea 160 km | ASSIGN (160&lt;180) | SKIP busy (DSP-1) | REFUSE red (DSP-3) | T-11 |

Evaluation order: **DSP-3 → DSP-1 → DSP-2**. First-fit in `vehicles.json` order. Full stdout grammar: `.docs/specification/architecture.md` § API.

Engine importable names (Peťo, S-02): `load_vehicles`, `load_jobs`, `lookup_rule`, `evaluate_vehicle`, `dispatch_job`, `format_job_block`, `main`.

## DispatchEvent (S-11 → S-10 and S-12)

One object per vehicle per job, roster order. `quotes` values must equal `lookup_rule(id)` once the engine exists. Until then, Peťo may emit events **without** `quotes` and Marek shows `dsp_ids` only.

```json
{
  "job_id": "J-01",
  "city": "Cluj",
  "km": 40,
  "vehicle_id": "T-11",
  "kind": "ASSIGN",
  "dsp_ids": ["DSP-1", "DSP-2"],
  "quotes": {
    "DSP-1": "DSP-1. Assign only a vehicle with status free and hours_ok true.",
    "DSP-2": "DSP-2. Job distance must be less than vehicle range_km."
  }
}
```

`kind` is exactly `ASSIGN` | `SKIP` | `REFUSE`.

- Start a driver **only** when `kind == "ASSIGN"`.
- T-12 is always `SKIP`. T-14 is always `REFUSE`. Never a driver for them.

Until S-02 is merged, S-11 may serve `pipelines/fixtures/dispatch_events.json` with the six rows (2 jobs × 3 vehicles) matching the table above.

## TelemetryEvent (S-12 → S-10)

```json
{
  "vehicle_id": "T-11",
  "job_id": "J-02",
  "status": "en_route",
  "speed_kmh": 72,
  "drive_power_kw": 45,
  "soc_pct": 38.0,
  "range_km": 68.0,
  "km_from_garage": 90.0,
  "charger_id": null,
  "charger_power_kw": null
}
```

`status`: `en_route` | `junction_stop` | `divert_charge` | `charging` | `delivered` | `returning`.

When `charging`, `speed_kmh` is 0, `charger_id` is e.g. `CS-2`, `charger_power_kw` is that station's `power_kw`, `drive_power_kw` is 0.

## Locations (S-13, done)

Canonical file: `.docs/reference/locations.json` (not in `instructions/`).

- Distance table to Cluj / Oradea, plus garage at 0 km. **Not** a consistent GPS map — do not invent coordinates.
- Each station and the garage has `power_kw` (station max output).
- Nearest charger: `min(stations, key=km_from[city])` among `km_from[city] <= remaining_range`.

| id | km Cluj | km Oradea | power_kw | Demo role |
|---|---|---|---|---|
| G-0 | — | — | 22 | depot start / return |
| CS-1 | 20 | 40 | 50 | nearest after Cluj |
| CS-2 | 60 | 20 | 150 | nearest after Oradea (wow) |
| CS-3 | 100 | 47 | 50 | backup |
| CS-4 | 300 | 200 | 350 | unreachable trap |
| CS-5 | 350 | 74 | 22 | too far / slow |

## Energy model (S-12 only)

Not a DSP rule. Do not put this in `dispatch.py`.

| Constant | Value |
|---|---|
| T-11 battery | 90 kWh at 100% = 180 km |
| `KWH_PER_KM` | 0.5 |
| Start of each job playback | SOC 100% (jobs are independent; roster is not mutated) |
| Charge until | `range_km >= city.km_from_garage` (can return home) |
| Charge time hours | `kwh_needed / station.power_kw` |
| Junction | every 10 km, speed 0, `drive_power_kw` 0, ~12 s sim time |
| Clock | accelerated (suggest 1 km ≈ 50–80 ms) so Oradea fits in the demo |

Worked: J-02 160 km → leftover 20 km / 10 kWh. Garage is 160 km. Must charge. CS-2 is 20 km at 150 kW. Arrive empty, then `kwh_needed` for 160 km return = 80 kWh → **~32 min** wall at 1×; compress on the demo clock.

J-01 leftover 140 km. Return 40 km. No charge. CS-1 is optional only.

## What each story may mock

| Story | May mock | Must not mock |
|---|---|---|
| S-03 | nothing for T-14 / quotes once engine exists | kit files |
| S-10 | DispatchEvent + TelemetryEvent fixtures | DSP sentences (show ids until quotes arrive) |
| S-11 | `dispatch_job` results via fixture | starting a driver on SKIP/REFUSE |
| S-12 | incoming ASSIGN fixture | charging T-14; inventing CS-6 |

## Out of scope for everyone

Copied workshop HTML. LLM chooses the truck. Extra vehicles/rules. pip deps. Mutating `vehicles.json` status. `python3` in demo commands.
