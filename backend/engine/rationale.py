"""Explainability core: every decision is rendered from a registered rule template.

No free-form justification strings elsewhere in the engine: call `explain(rule_id, **inputs)`.
"""

import json
from collections import defaultdict
from string import Formatter

from engine.errors import NetArchError
from engine.models import Rationale

__all__ = ["Rationale", "RationaleError", "RationaleLog", "RULES", "explain"]


class RationaleError(NetArchError):
    """Unknown rule id or missing template field."""


# rule_id -> (domain, standard_ref, threshold, template)
RULES: dict[str, tuple[str, str, str | None, str]] = {
    # ---- L1 media
    "L1.copper": (
        "L1", "IEEE 802.3an-2006", "copper ≤ 100 m",
        "Selected Cat6a copper (10GBASE-T) for {link} because the run ({distance_m} m) is within "
        "the 100 m 10GBASE-T channel limit of IEEE 802.3an.",
    ),
    "L1.mmf": (
        "L1", "IEEE 802.3ae (10GBASE-SR), TIA-492AAAD (OM4)", "OM4 ≤ 400 m",
        "Selected OM4 multimode fiber with 10GBASE-SR (850 nm) for {link} because {distance_m} m "
        "{reason}. At 850 nm, modal dispersion in multimode fiber caps 10G reach at 400 m on OM4.",
    ),
    "L1.smf_lr": (
        "L1", "IEEE 802.3ae (10GBASE-LR)", "LR ≤ 10 km",
        "Selected OS2 single-mode fiber with 10GBASE-LR (1310 nm) for {link} because {distance_m} m "
        "{reason}. Single-mode fiber has no modal dispersion; 10GBASE-LR reaches 10 km.",
    ),
    "L1.smf_er": (
        "L1", "IEEE 802.3ae (10GBASE-ER)", "ER ≤ 40 km",
        "Selected OS2 single-mode fiber with 10GBASE-ER (1550 nm) for {link} because {reason}. "
        "10GBASE-ER uses the lower-loss 1550 nm window and reaches 40 km.",
    ),
    "L1.budget": (
        "L1", "IEEE 802.3ae channel insertion loss; TIA-568 component loss", "loss ≤ allowed",
        "Optical budget for {link} ({transceiver}): fiber {fiber_loss_db} dB ({km} km × {db_per_km} dB/km) "
        "+ {connectors} connectors × {connector_db} dB + {splices} splices × {splice_db} dB = "
        "{total_loss_db} dB against {allowed_db} dB allowed, margin {margin_db} dB ({verdict}).",
    ),
    "L1.copper_violation": (
        "L1", "IEEE 802.3an-2006", "copper ≤ 100 m",
        "Copper was requested for {link}, but the run is {distance_m} m, beyond the 100 m 10GBASE-T "
        "limit (IEEE 802.3an). Past 100 m, signal attenuation and crosstalk exceed what the PHY can "
        "equalize, so the link would fail or flap. Use OM4 fiber (≤ 400 m) or OS2 fiber.",
    ),
    "L1.mmf_violation": (
        "L1", "IEEE 802.3ae (10GBASE-SR)", "OM4 ≤ 400 m",
        "Multimode fiber was requested for {link}, but the run is {distance_m} m, beyond the 400 m "
        "10GBASE-SR reach on OM4. Modal dispersion would close the eye at 10 Gb/s. Use OS2 single-mode fiber.",
    ),
    "L1.distance_exceeded": (
        "L1", "IEEE 802.3ae (10GBASE-ER)", "ER ≤ 40 km",
        "No standard 10G transceiver covers {link} at {distance_m} m: 10GBASE-ER tops out at 40 km. "
        "Use a carrier service (EVPL/MPLS) or amplified DWDM for this span.",
    ),
    "L1.budget_violation": (
        "L1", "IEEE 802.3ae channel insertion loss", "loss ≤ allowed",
        "Optical loss on {link} is {total_loss_db} dB, exceeding the {allowed_db} dB allowed even for "
        "10GBASE-ER. Reduce connectors/splices or use a carrier/DWDM service.",
    ),
    # ---- VLSM
    "VLSM.subnet": (
        "VLSM", "RFC 950, RFC 1878", "usable = 2^(32−p) − 2",
        "{name}: {hosts} hosts + 1 gateway need {needed} usable addresses; the smallest block is "
        "/{prefix} (2^{host_bits} − 2 = {usable} usable), giving {util}% utilization.",
    ),
    "VLSM.p2p": (
        "VLSM", "RFC 3021", "/31 for point-to-point",
        "{name}: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no "
        "network/broadcast addresses are wasted as a /30 would.",
    ),
    "VLSM.loopback": (
        "VLSM", "RFC 4632", "/32 host route",
        "{name}: loopback gets a /32, a single stable address used as the router ID.",
    ),
    "VLSM.efficiency": (
        "VLSM", "RFC 1878, RFC 4632", None,
        "Allocated {allocated} of {root_size} addresses in {root} ({root_util}% of the root used). "
        "{requested} addresses were actually needed, so packing efficiency is {eff}% "
        "({waste} addresses lost to power-of-two rounding). Blocks were allocated largest-first, "
        "so each block starts on its natural boundary and none overlap.",
    ),
    "VLSM.exhausted": (
        "VLSM", "RFC 4632", "Σ blocks ≤ root size",
        "Root {root} has {available} addresses but the requested subnets need {needed} "
        "(after rounding each to a power of two). Use a shorter root prefix (at least /{min_prefix}) "
        "or reduce host counts.",
    ),
    "VLSM.block": (
        "VLSM", "RFC 4632", None,
        "{name} gets the contiguous block {network}/{prefix} ({size} addresses) so all of its subnets "
        "can be summarized as one route.",
    ),
    "L1.provider": (
        "L1", "IEEE 802.3an-2006 (handoff)", None,
        "{link} uses a {transport} service: the inter-site physical layer belongs to the provider, "
        "so only the local handoff is designed (Cat6a 10GBASE-T to the demarc, assumed ≤ 100 m).",
    ),
    "L1.in_building": (
        "L1", "IEEE 802.3an-2006", "copper ≤ 100 m",
        "{count} in-building connection(s) (switch-to-switch and router-to-switch in the same building) "
        "are patch runs assumed ≤ 100 m, so Cat6a 10GBASE-T is used.",
    ),
    # ---- Topology
    "TOPO.collapsed_core": (
        "TOPO", "Cisco hierarchical campus design; Project rule", "buildings < 4",
        "{site}: collapsed-core design (core and distribution combined) because the site has "
        "{buildings} building(s), below the {threshold}-building point where a separate distribution "
        "layer pays off. Fewer devices and hops for {endpoints} endpoints.",
    ),
    "TOPO.three_tier": (
        "TOPO", "Cisco hierarchical campus design; Project rule", "buildings ≥ 4",
        "{site}: three-tier design (core / distribution / access) because the site has {buildings} "
        "buildings (≥ {threshold}). A distribution block per building contains failures and keeps the "
        "core purely layer 3.",
    ),
    "TOPO.access": (
        "TOPO", "Project rule", "48 ports per switch, 8 per stack",
        "{location}: {ports} access ports needed, so {members} × {per}-port switch(es) in {stacks} "
        "stack(s) (≤ {max_members} members per stack). {spare} spare port(s) are shut down.",
    ),
    "TOPO.poe": (
        "TOPO", "IEEE 802.3at", "30 W per PoE+ port",
        "{switch}: {poe_ports} PoE port(s) × {watts_per} W (802.3at Type 2) = {watts} W of PoE budget "
        "required from the switch power supplies.",
    ),
    "TOPO.redundant": (
        "TOPO", "Project rule (resiliency=high)", None,
        "{site}: resiliency is high, so {what} are paired and every access stack is dual-homed to "
        "both gateways. Any single device or uplink can fail without isolating users.",
    ),
    "TOPO.dual_homed": (
        "TOPO", "Project rule (resiliency=high)", None,
        "{link} is built as {n} circuits ({pairs}) so the site survives the loss of either router or circuit.",
    ),
    # ---- L2
    "L2.vlan_plan": (
        "L2", "IEEE 802.1Q", None,
        "{block}: VLANs {vlans} each carry one segment, giving each role its own broadcast domain.",
    ),
    "L2.native": (
        "L2", "IEEE 802.1Q", "native ≠ VLAN 1",
        "Native VLAN is the unused VLAN {native} on every trunk (not VLAN 1) and it is left out of the "
        "allowed lists. This blocks double-tagging VLAN hopping. Unused access ports are parked in it "
        "and shut down.",
    ),
    "L2.trunk_prune": (
        "L2", "IEEE 802.1Q", "allowed = VLANs present",
        "{device} trunk to {peer} allows only VLANs {vlans}, the VLANs that have ports behind it, "
        "instead of all 4094. This limits broadcast flooding and blast radius.",
    ),
    "L2.stp_root": (
        "L2", "IEEE 802.1w (Rapid PVST+)", None,
        "{block}: Rapid PVST+ root primary on {primary}{secondary}, so the root bridge is also the "
        "default gateway and frames never take a detour through an access switch.",
    ),
    "L2.edge_ports": (
        "L2", "IEEE 802.1w", None,
        "Access ports use PortFast (RSTP edge port, forwards immediately) and BPDU Guard "
        "(err-disables the port if a switch is plugged in), preventing accidental loops.",
    ),
    "L2.hsrp": (
        "L2", "RFC 2281 (HSRP)", None,
        "{block}: HSRPv2 gives each VLAN a virtual gateway (first usable address) shared by {gw1} "
        "(priority {p1}, active) and {gw2} (priority {p2}, standby). Each subnet reserves 2 extra "
        "addresses for the physical SVIs.",
    ),
    # ---- Routing
    "ROUTE.ospf_single": (
        "ROUTE", "RFC 2328; Assignment §3", "subnets < 50",
        "Single-area OSPF (area 0) because the design is one site with {n} subnets, below the "
        "{limit}-subnet threshold. One link-state database converges fast and needs no ABRs.",
    ),
    "ROUTE.ospf_large_flat": (
        "ROUTE", "RFC 2328; Assignment §3", "subnets < 50",
        "OSPF stays in area 0 although {n} subnets ≥ {limit}: the single site has no distribution "
        "layer to act as ABRs. With ≥ {min_b} buildings the design becomes three-tier and multi-area.",
    ),
    "ROUTE.ospf_multi_campus": (
        "ROUTE", "RFC 2328; Assignment §3", "subnets ≥ 50",
        "Multi-area OSPF because the campus has {n} subnets (≥ {limit}). Each building's distribution "
        "block is its own area with the distribution switches as ABRs, so LSA flooding stays local.",
    ),
    "ROUTE.ospf_multi_site": (
        "ROUTE", "RFC 2328; Assignment §3", "multi-site",
        "Multi-area OSPF because the design spans {sites} sites: {backbone} is the backbone (area 0) and "
        "every other site gets its own area, so flooding and SPF runs stay inside one site.",
    ),
    "ROUTE.area": (
        "ROUTE", "RFC 2328", None,
        "{unit} is OSPF area {area} with address block {block}.",
    ),
    "ROUTE.summary": (
        "ROUTE", "RFC 2328; RFC 4632", None,
        "ABR {abr} summarizes area {area} as {block} (1 route instead of {count}), which works because "
        "the area's subnets were allocated from one contiguous block.",
    ),
    "ROUTE.rid": (
        "ROUTE", "RFC 2328", None,
        "Router IDs come from Loopback0 /32 addresses. A loopback never goes down with a physical "
        "interface, so OSPF and BGP identities stay stable.",
    ),
    "ROUTE.ref_bw": (
        "ROUTE", "RFC 2328 (interface cost)", None,
        "OSPF reference bandwidth is {ref} Mbps. With the default {default} Mbps every link of 100 Mb/s "
        "or more gets cost 1, so 10G and 1G paths would look equal.",
    ),
    "ROUTE.ebgp": (
        "ROUTE", "RFC 4271; RFC 6996", None,
        "eBGP between {ent} (AS {ent_asn}) and {cloud} (AS {cloud_asn}) because the cloud VPC is a "
        "separate administrative domain. BGP keeps policy control at the boundary and OSPF is not "
        "extended into the provider. Both ASNs are private (RFC 6996).",
    ),
    "ROUTE.ipsec": (
        "ROUTE", "RFC 4301; RFC 5737", None,
        "{link} runs over the internet, so traffic between {a} and {b} is encrypted in a route-based "
        "IPsec tunnel (VTI, AES-256 / SHA-256, DH group 14). Underlay addresses come from {underlay} "
        "(RFC 5737 documentation range): replace them with the real public IPs.",
    ),
    # ---- ACL
    "ACL.policy": (
        "ACL", "Cisco IOS extended ACL (first match)", None,
        "{src} → {dst}: {action} {proto}{port} via {acl}, applied inbound on the {src} gateway so the "
        "decision is made at the first layer-3 hop.",
    ),
    "ACL.default": (
        "ACL", "Cisco IOS extended ACL (implicit deny)", None,
        "{acl} ends with 'permit ip any any' so traffic not covered by a policy is allowed; otherwise "
        "the IOS implicit deny would drop all other traffic from {src}.",
    ),
}


def _fields(template: str) -> set[str]:
    return {f for _, f, _, _ in Formatter().parse(template) if f}


def explain(rule_id: str, **inputs) -> Rationale:
    """Render one rule into a Rationale. Raises RationaleError on unknown rule or missing field."""
    if rule_id not in RULES:
        raise RationaleError(f"unknown rule id '{rule_id}'", rule_id=rule_id)
    domain, ref, threshold, template = RULES[rule_id]
    missing = _fields(template) - inputs.keys()
    if missing:
        raise RationaleError(
            f"rule '{rule_id}' missing field(s): {sorted(missing)}", rule_id=rule_id, missing=sorted(missing)
        )
    return Rationale(
        rule_id=rule_id, domain=domain, inputs=inputs, threshold=threshold,
        standard_ref=ref, text=template.format(**inputs),
    )


class RationaleLog:
    """Ordered collection of rationales for one design run."""

    def __init__(self) -> None:
        self.items: list[Rationale] = []

    def add(self, rule_id: str, **inputs) -> Rationale:
        r = explain(rule_id, **inputs)
        self.items.append(r)
        return r

    def extend(self, items: list[Rationale]) -> None:
        self.items.extend(items)

    def by_domain(self) -> dict[str, list[Rationale]]:
        out: dict[str, list[Rationale]] = defaultdict(list)
        for r in self.items:
            out[r.domain].append(r)
        return dict(out)

    def to_json(self) -> str:
        return json.dumps([r.model_dump() for r in self.items], indent=2, default=str)

    def to_markdown(self) -> str:
        lines = ["# Architectural Rationale"]
        for domain, items in self.by_domain().items():
            lines += ["", f"## {domain}"]
            lines += [f"- **[{r.rule_id}]** {r.text} _(ref: {r.standard_ref})_" for r in items]
        return "\n".join(lines) + "\n"
