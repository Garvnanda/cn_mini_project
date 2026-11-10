# Rubric self-check (CIC-307 NetArchitect, 100 points)

Each rubric row from the assignment PDF mapped to the code and the tests that prove it.
Test command: `cd backend && pytest` (Python) and `cd frontend && npm test` (UI).

## 1. Parameter engine & presets (15)
| Requirement | Where | Proof |
|---|---|---|
| 3 preset scenarios | `backend/presets/campus_lan.json`, `metro_man.json`, `global_wan.json` | `tests/test_presets.py::test_campus_spec / test_metro_spec / test_wan_spec` |
| Custom parameters validated (distance, density, resiliency) | `engine/models.py` (`DesignInput`, `parse_design_input`) | `tests/test_models.py` (32 cases) |
| Graceful boundary inputs and errors | typed errors in `engine/errors.py`; API returns 422 `{type, message, details}`; CLI exit codes 2-6 | `tests/test_presets.py::test_invalid_examples`, `tests/test_api.py::test_typed_errors_422`, `tests/test_cli.py::test_exit_codes` |
| Invalid examples | `backend/examples/invalid_copper_150m.json`, `invalid_exhausted.json`, `invalid_bad_vlan.json` | same tests |

## 2. Explainable decision engine (25)
| Requirement | Where | Proof |
|---|---|---|
| Justification for every media type / transceiver | `engine/media.py` + rules `L1.*` in `engine/rationale.py` (IEEE 802.3an/ae, TIA-568, optical budget, latency) | `tests/test_media.py`, `test_spec_example_wording` |
| Routing protocol justification | `engine/routing.py` + rules `ROUTE.*` (RFC 2328, 4271, 6996, 4301) | `tests/test_routing.py::test_select_protocol_boundaries` (49/50) |
| Subnetting math + RFC | `engine/vlsm.py` + rules `VLSM.*` (RFC 950, 1878, 3021, 4632) | `tests/test_vlsm.py` |
| Topology tier justification | `engine/topology.py` + `TOPO.*` | `tests/test_topology.py::test_tier_rule` |
| Every rule renders and cites a standard | `RULES` registry | `tests/test_rationale.py::test_every_rule_renders`, `test_every_rule_cites_a_standard` |
| Every design explains every domain | planner | `tests/test_presets.py::test_preset_every_domain_explained`, `tests/test_routing.py::test_every_decision_explained` |
| Visible to users | `design_report.md`, `cli.py explain`, web Decisions tab, TUI Decisions tab | `tests/test_export.py`, `tests/test_cli.py::test_explain_domain`, `frontend/src/App.test.tsx` |

## 3. Subnet engine & configs (25)
| Requirement | Where | Proof |
|---|---|---|
| Bitwise VLSM, zero overlap | `engine/bitmath.py`, `engine/vlsm.py` (integer bit ops; `ipaddress` only as oracle) | `tests/test_vlsm.py::test_property_no_overlap_inside_root` (Hypothesis, 500 cases), `test_oracle_matches_ipaddress` |
| Broadcast, gateways, utilization | `Subnet` fields | `tests/test_vlsm.py::test_basic_allocation_largest_first` |
| Copy-paste Cisco IOS: switches, routers, SVIs, ACLs | `templates/*.j2`, `engine/configgen.py`, `engine/acl.py` | golden files `tests/golden/*`, `tests/test_configs.py` |
| Only documented IOS syntax | `docs/ios_reference.md` | `tests/test_configs.py::test_only_documented_commands` |
| Configs actually work | own verifier: parse configs back, simulate forwarding | `tests/test_verifier.py::test_generated_designs_verify` (all 7 designs) |

## 4. Automated unit testing (15)
| Requirement | Proof |
|---|---|
| Distance violations | `tests/test_media.py::test_copper_101m_raises`, `test_beyond_er`, `test_multimode_preference`, `test_latency_budget_violation` |
| Address space exhaustion | `tests/test_vlsm.py::test_exhaustion`, `test_absurd_host_count_exhausts`, `tests/test_presets.py::test_invalid_examples` |
| Wildcard masks across edge-case subnets | `tests/test_bitmath.py::test_mask_and_wildcard_all_prefixes` (/0 to /32), `/31` and `/32` tests |
| Totals | 419 Python tests (1 live-Batfish test skipped), 4 Vitest UI tests |

## 5. AI code audit & defense (20)
| Requirement | Where |
|---|---|
| ≥ 2 real AI mistakes with prompt, buggy code, analysis, fix | `ai_audit_log.md` entries 1-3 |
| Validated with packet-flow analysis | entry 2 (AD-1 Null0 blackhole) and entry 3 (single-homed branch router): before/after hop-by-hop traces from `verify/simulator.py` |
| Regression tests | `tests/test_verifier.py::test_detects_ad1_null0_blackhole`, `tests/test_whatif.py::test_metro_branch_core_not_spof_after_fix`, `tests/test_media.py::test_auto_thresholds[400-...]` |

## Deliverables
| Deliverable | Status |
|---|---|
| Source repo with CLI / web interface, explainability engine, unit tests | done (`backend/cli.py`, `backend/api.py`, `backend/tui.py`, `frontend/`) |
| `ai_audit_log.md` | done (3 entries) |
| Exported configs for the 3 presets | `exports/campus_lan`, `exports/metro_man`, `exports/global_wan` |
| Loaded into Packet Tracer / GNS3 | **owner**: screenshots go in `docs/proof/` (not possible from this environment) |
