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

### Entry 2 — eBGP Null0 anchor static blackholes every remote OSPF area
- **Date / phase:** 2026-11-10, written in Phase 7, caught in Phase 12 by the built-in verifier
- **AI tool & model:** Claude Code (Claude Opus 5.5)
- **Prompt given:** "continue with phase 5, 6, 7 and 8" (task 7.5: BGP ASN plan, neighbor list). The AI chose to advertise each OSPF area block to the cloud with `network ... mask ...` and to anchor it with a Null0 static.
- **AI-generated code (buggy):** `backend/engine/routing.py`
```python
for k, b in sorted(blocks.items(), key=lambda kv: str(kv[0])):
    if isinstance(k, int):
        ent.bgp.networks.append((b.network, b.mask))
        ent.static_routes.append(StaticRoute(network=b.network, mask=b.mask, next_hop="Null0"))
```
  rendered on DELHI-R1 (global_wan preset) as:
```
ip route 10.100.8.0 255.255.252.0 Null0
ip route 10.100.12.0 255.255.252.0 Null0
ip route 10.100.16.0 255.255.252.0 Null0
```
- **Symptom:** `verify(design("global_wan"))` failed `reachability_and_policy`: every flow from Delhi (and every branch-to-branch flow, which transits Delhi) to another site was dropped. All Phase 5-8 unit tests had passed because they checked config text, not forwarding.
- **Packet-flow analysis (before fix):** `sim.trace("10.100.3.254", <Mumbai-IoT host>)`
```
host 10.100.3.254 -> VLAN 10 : forward to default gateway 10.100.0.1 on DELHI-CORE1
DELHI-CORE1 Vlan10 -> TenGigabitEthernet1/0/3 : forward route 10.100.8.0/22 [ospf 110/20] via 10.100.4.6
DELHI-R1 TenGigabitEthernet0/0/0 : drop discard route 10.100.8.0/22 [static 1/0] via Null0
outcome: dropped | DELHI-R1 discards via 10.100.8.0/22 [static 1/0] via Null0
```
- **Root cause:** the Mumbai ABR advertises its area as the inter-area summary 10.100.8.0/22 (OSPF, AD 110). DELHI-R1 also has a static 10.100.8.0/22 → Null0 with the default AD 1. Same prefix length, so longest-prefix match ties and the lower administrative distance wins: the discard route is installed and the OSPF summary is never used. The static was only needed so BGP `network` finds an exact route in the RIB (RFC 4271 origination; Cisco AD table in docs/standards.md).
- **Fix:** make the anchor a floating static (AD 254), so it is installed only when OSPF has no route for that block (D-021).
```python
ent.static_routes.append(StaticRoute(network=b.network, mask=b.mask, next_hop="Null0",
                                     distance=C.FLOATING_STATIC_AD))  # 254
```
  rendered as `ip route 10.100.8.0 255.255.252.0 Null0 254`.
- **Packet-flow after fix:**
```
host 10.100.3.254 -> VLAN 10 : forward to default gateway 10.100.0.1 on DELHI-CORE1
DELHI-CORE1 Vlan10 -> TenGigabitEthernet1/0/3 : forward route 10.100.8.0/22 [ospf 110/20] via 10.100.4.6
DELHI-R1 TenGigabitEthernet0/0/0 -> TenGigabitEthernet0/0/1 : forward route 10.100.8.0/22 [ospf 110/10] via 10.100.4.9
MUMBAI-R1 TenGigabitEthernet0/0/1 -> TenGigabitEthernet0/0/0 : forward route 10.100.8.0/23 [ospf 110/10] via 10.100.10.1
MUMBAI-CORE1 TenGigabitEthernet1/0/3 -> Vlan20 : deliver connected 10.100.8.0/23 [connected 0/0] via connected; delivered to host
outcome: delivered
```
- **Regression tests:** `tests/test_verifier.py::test_detects_ad1_null0_blackhole`, `tests/test_simulator.py::test_null0_discard_and_floating_static`
