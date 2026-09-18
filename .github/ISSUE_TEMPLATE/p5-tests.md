---
name: P5 Tests
about: T-14 stays refused. Quotes come from dispatch_rules.md
labels: p5-tests
---

## Goal

The refuse case cannot regress while others polish UI.

## Owns

`desk.py` `test_desk.py` `web/test_api.py`

## Done when

- [ ] T-14 → Refuse DSP-3 for J-01 and J-02
- [ ] J-01 → Assign T-11 DSP-1, quote is in dispatch_rules.md
- [ ] T-12 busy DSP-1, T-99 invent DSP-4
- [ ] Off-scope payout → Off desk, no rule id
- [ ] Hook tests: payout blocked, kit edit denied
- [ ] `python test_desk.py` and `python web/test_api.py` green on main
