# S-12 Electric driver agent

| Field | Value |
|---|---|
| **Owner** | Marian |
| **Layer** | B — wow |
| **Status** | ready |
| **Blocked on** | [S-00](S-00-contracts.md) + [S-13](S-13-locations-data.md) (done). Fixture ASSIGN is enough; do not wait for S-11 process spawn. |
| **Unblocks** | S-10 telemetry panel; live “CS-2 150 kW” moment |

## Goal

As the driver agent, once dispatched I report speed, stop at junctions, draw electric power, watch range, and divert to the nearest **reachable** charger using station `power_kw`.

Assignment stays in Layer A. This story never assigns a truck.

## Files

- `src/sim/driver.py` — tick loop, emits TelemetryEvent
- Reads `.docs/reference/locations.json`
- Consumes ASSIGN (fixture or dispatcher)

## Behavior

Only `vehicle_id=T-11`. Ignore any call with T-12/T-14.

Per job playback, start at G-0, SOC 100%, range 180 km.

| Tick | What |
|---|---|
| Drive toward `city` | `status=en_route`, speed ~70 km/h, `drive_power_kw` > 0, range falls 0.5 kWh/km |
| Every 10 km | `junction_stop`, speed 0, drive power 0, ~12 s sim |
| On arrival | `delivered`. If `range_km >= km_from_garage`, `returning` to G-0 (J-01). |
| If `range_km < km_from_garage` | pick nearest charger with `km_from[city] <= remaining_range`. J-02 → **CS-2 at 20 km, 150 kW**. |
| At charger | `charging`, speed 0, `charger_id`, `charger_power_kw`. Add kWh at that power until range ≥ return distance. |
| Unreachable | CS-4 (350 kW) and CS-5 must not be chosen from Oradea leftover 20 km. |

Energy constants: [S-00](S-00-contracts.md) (90 kWh / 0.5 kWh per km).

Demo clock: compress so J-02 drive + CS-2 charge is visible in < 45 s.

## Acceptance

- [ ] J-01 playback: no charge required; may pass CS-1 without stopping.
- [ ] J-02 playback: leftover ~20 km → CS-2, `charger_power_kw == 150`.
- [ ] CS-4 (350 kW) never selected on kit jobs.
- [ ] TelemetryEvent stream matches S-00 schema.
- [ ] T-14 never emits telemetry.
- [ ] Does not import assignment rules; does not write kit files.

## Parallel

S-05 Grok stack is your Layer A story and comes first if the clock is tight. This sim is the 60-second wow, not the must-show.

## Out of scope

GPS map library. New DSP rule. Mutating `vehicles.json`.
