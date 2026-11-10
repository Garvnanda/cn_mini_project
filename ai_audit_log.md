# AI Code Audit Log — NetArchitect (CIC-307)

Requirement: at least two **real** cases where AI suggested flawed networking code, with diagnosis and fix, validated by packet-flow analysis.
Rule: record only real incidents from this build. Never invent entries.

## Entry template

### Entry N — <short title>
- **Date / phase:**
- **AI tool & model:**
- **Prompt given:**
```
<exact prompt>
```
- **AI-generated code (buggy):**
```python
<exact code>
```
- **Symptom:** what went wrong, how noticed (test name / verifier output)
- **Packet-flow analysis:** `netarch trace ...` output before fix, showing the wrong hop / drop / leak
- **Root cause:** networking explanation (RFC / standard from docs/standards.md)
- **Fix:**
```python
<fixed code>
```
- **Packet-flow after fix:** trace output
- **Regression test:** `tests/...::test_name`

---

## Entries

### Entry 1 — Optical budget fails at the exact OM4 limit (float comparison)
- **Date / phase:** 2026-11-10, Phase 3
- **AI tool & model:** Claude Code (Claude Opus 5.5)
- **Prompt given:** "continue with building phase 2, 3 and 4" (task 3.4: optical power budget calc)
- **AI-generated code (buggy):**
```python
fiber = km * db_per_km
total = fiber + connectors * C.CONNECTOR_DB + splices * C.SPLICE_DB
allowed = C.CHANNEL_LOSS_DB[transceiver]
margin = allowed - total
...
return margin >= 0, total, r
```
- **Symptom:** `tests/test_media.py::test_auto_thresholds[400-...]` failed. A 400 m OM4 link, which is exactly at the 10GBASE-SR limit, was rejected with `PhysicalDistanceViolationError`.
- **Packet-flow analysis:** not applicable yet (L1 bug; the simulator arrives in Phase 11). Impact: a valid backbone link is refused, so the design generator would never produce the 400 m inter-building link and that building has no uplink. **[Owner: decide whether this entry counts for the rubric or keep it as a supporting entry.]**
- **Root cause:** `0.4 km × 3.5 dB/km + 2 × 0.75 dB` is `2.9000000000000004` in IEEE-754 floating point, so `2.9 − 2.9000000000000004 < 0` and the budget "failed" by 4e-16 dB.
- **Fix:**
```python
total = _r(fiber + connectors * C.CONNECTOR_DB + splices * C.SPLICE_DB)  # round to 0.01 dB
margin = _r(allowed - total)
```
- **Regression test:** `tests/test_media.py::test_auto_thresholds[400-OM4 multimode fiber-10GBASE-SR]`
