---
name: P4 Live ops
about: Who clicks, how to undo, what goes in the log
labels: p4-live
---

## Goal

A judge believes this could hang on a dispatch wall.

## Owns

`web/server.py` — UI copy goes to P2 as an issue, not a direct JS edit

## Done when

- [ ] Confirm is the only send. T-14 confirm does not send
- [ ] Undo last Assign restores T-11 to free. Kit files unchanged
- [ ] Log line: time, dispatcher, job, vehicle, decision, rule, quote
- [ ] One spoken sentence for the demo: who clicks, undo, log
- [ ] `python web/test_api.py` green
