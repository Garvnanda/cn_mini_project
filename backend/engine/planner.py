"""Orchestrator: input -> media -> topology -> L2 -> routing/addressing -> ACLs -> DesignResult."""

from typing import Any

from engine.acl import build_acls
from engine.l2 import apply_l2
from engine.media import CAT6A, select_media
from engine.models import DesignInput, DesignResult, MediaDecision, Transport, parse_design_input
from engine.rationale import RationaleLog, explain
from engine.routing import plan_routing
from engine.topology import build_topology


def design(data: dict[str, Any] | DesignInput) -> DesignResult:
    inp = data if isinstance(data, DesignInput) else parse_design_input(data)
    log = RationaleLog()

    media: list[MediaDecision] = []
    for ln in inp.links:
        if ln.transport == Transport.FIBER:
            m = select_media(ln)
        else:
            m = MediaDecision(link=ln.key, distance_m=ln.distance_m, media=f"{ln.transport.value} handoff ({CAT6A})",
                              transceiver="10GBASE-T",
                              rationale=[explain("L1.provider", link=ln.key, transport=ln.transport.value)])
        media.append(m)
        log.extend(m.rationale)

    topo = build_topology(inp, log)
    apply_l2(topo, inp, log)
    routing, subnets = plan_routing(inp, topo, log)
    devices = list(topo.devices.values())
    build_acls(inp, devices, subnets, log)

    by_link = {m.link: m for m in media}
    in_building = 0
    for c in topo.cables:
        if c.link:
            c.media, c.transceiver = by_link[c.link].media, by_link[c.link].transceiver
        else:
            c.media, c.transceiver = CAT6A, "10GBASE-T"
            in_building += 1
        for host, ifname in ((c.a, c.a_if), (c.b, c.b_if)):
            i = topo.devices[host].iface(ifname)
            i.media, i.transceiver = c.media, c.transceiver
            i.description += f" [{c.transceiver}]"
    if in_building:
        log.add("L1.in_building", count=in_building)

    return DesignResult(input=inp, media=media, subnets=subnets, routing=routing, devices=devices,
                        cables=topo.cables, tiers=topo.tiers, rationale=log.items)
