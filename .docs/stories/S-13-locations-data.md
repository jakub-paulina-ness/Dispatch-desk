# S-13 Locations + charger power

| Field | Value |
|---|---|
| **Owner** | Jakub |
| **Layer** | B — data |
| **Status** | **done** |
| **Blocked on** | — |
| **Unblocks** | S-10 charge section, S-12 driver |

## Goal

As the team, we want a loadable locations file (not a `.txt` note) so HTML and the driver can share garage, cities, chargers, and **station power**.

## Files

- `.docs/reference/locations.json` — canonical
- `.docs/reference/locations.json.txt` — **removed** (replaced by JSON)

Not in `instructions/`. Not a dispatch rule.

## Schema

- `garage`: `id`, `name`, `km_from_garage` (0), `power_kw` (22 depot AC)
- `cities`: Cluj 40, Oradea 160 (matches `jobs.json` distances)
- `charging_stations[]`: `id`, `name`, `km_from.{Cluj,Oradea}`, `power_kw`

## Frozen power

| id | power_kw | Why |
|---|---|---|
| G-0 | 22 | depot overnight |
| CS-1 | 50 | urban DC, nearest Cluj |
| CS-2 | 150 | fast DC, nearest Oradea — demo charge finishes on the compressed clock |
| CS-3 | 50 | backup |
| CS-4 | 350 | ultra-fast **trap** (300 / 200 km) |
| CS-5 | 22 | remote AC |

This is a distance-to-city table, not a consistent map. Do not invent lat/lon.

## Acceptance

- [x] Valid JSON
- [x] Five stations + garage, each with `power_kw`
- [x] `.txt` gone
- [x] Kit untouched

## Out of scope

Engine changes. New DSP-5 “must charge to assign”.
