"""Phase 7: protocol selection, OSPF areas, hierarchical addressing, summaries, eBGP, IPsec."""

from collections import defaultdict

from engine import bitmath as B
from engine import constants as C
from engine.errors import TopologyError
from engine.models import (
    BgpConfig, DesignInput, Interface, OspfConfig, RoutingDecision, StaticRoute, Subnet,
)
from engine.rationale import RationaleLog
from engine.topology import Topology
from engine.vlsm import AllocRequest, allocate

UnitKey = int | str  # OSPF area number, or "cloud:<site>"


def select_protocol(n_subnets: int, multi_site: bool, three_tier: bool) -> str:
    """Assignment §3 rule: single AS with < 50 subnets -> area 0; multi-site -> multi-area."""
    if multi_site:
        return "ospf_multi_site"
    if n_subnets < C.OSPF_SINGLE_AREA_MAX_SUBNETS:
        return "ospf_single"
    return "ospf_multi_campus" if three_tier else "ospf_large_flat"


PROTOCOL_LABEL = {
    "ospf_single": "OSPF single-area",
    "ospf_large_flat": "OSPF single-area",
    "ospf_multi_campus": "OSPF multi-area",
    "ospf_multi_site": "OSPF multi-area",
}


def plan_routing(inp: DesignInput, t: Topology, log: RationaleLog) -> tuple[RoutingDecision, list[Subnet]]:
    start = len(log.items)
    devs = t.devices
    for d in devs.values():
        if d.l3:
            d.interfaces.insert(0, Interface(name="Loopback0", mode="loopback", description="Router ID"))

    routed = [c for c in t.cables if c.kind == "routed"]
    n_subnets = len(inp.segments) + len(routed) + len(t.tunnels) + sum(d.l3 for d in devs.values())
    three_tier = any(v == "three_tier" for v in t.tiers.values())
    proto = select_protocol(n_subnets, t.multi_site, three_tier)

    # ---- areas
    site_area: dict[str, int] = {}
    if proto == "ospf_multi_site":
        others = [s.name for s in inp.sites if s.name != t.backbone and s.kind.value != "cloud"]
        site_area = {t.backbone: 0} | {s: i for i, s in enumerate(others, start=1)}
        n_sites = len(inp.sites)
        log.add("ROUTE.ospf_multi_site", sites=n_sites, backbone=t.backbone)
        _check_backbone_adjacency(t, others)
    elif proto == "ospf_multi_campus":
        log.add("ROUTE.ospf_multi_campus", n=n_subnets, limit=C.OSPF_SINGLE_AREA_MAX_SUBNETS)
    elif proto == "ospf_single":
        log.add("ROUTE.ospf_single", n=n_subnets, limit=C.OSPF_SINGLE_AREA_MAX_SUBNETS)
    else:
        log.add("ROUTE.ospf_large_flat", n=n_subnets, limit=C.OSPF_SINGLE_AREA_MAX_SUBNETS,
                min_b=C.THREE_TIER_MIN_BUILDINGS)

    block_area = {b.name: i for i, b in enumerate(t.blocks, start=1)}

    def unit_of(host: str) -> UnitKey:
        d = devs[host]
        if d.role == "cloud":
            return f"cloud:{d.site}"
        if proto == "ospf_multi_site":
            return site_area[d.site]
        if proto == "ospf_multi_campus" and d.role == "distribution":
            return block_area[next(b.name for b in t.blocks if host in b.gateways)]
        return 0

    def unit_name(k: UnitKey) -> str:
        if isinstance(k, str):
            return f"Cloud {k.split(':', 1)[1]}"
        if proto == "ospf_multi_site":
            return f"Area {k} ({next(s for s, a in site_area.items() if a == k)})"
        if proto == "ospf_multi_campus" and k:
            return f"Area {k} ({next(b for b, a in block_area.items() if a == k)})"
        return f"Area {k}"

    # ---- address requests per unit
    reqs: dict[UnitKey, list[AllocRequest]] = defaultdict(list)
    gws_of: dict[str, list[tuple[str, Interface]]] = defaultdict(list)
    for d in devs.values():
        for i in d.interfaces:
            if i.segment:
                gws_of[i.segment].append((d.hostname, i))
    for seg in inp.segments:
        gws = gws_of[seg.name]
        extra = 2 if len(gws) == 2 else 0  # HSRP: two physical SVI addresses
        reqs[unit_of(gws[0][0])].append(AllocRequest(seg.name, seg.hosts + extra, "lan", seg.vlan))
    for d in devs.values():
        if d.l3:
            reqs[unit_of(d.hostname)].append(AllocRequest(f"{d.hostname} Loopback0", kind="loopback"))
    p2p_name: dict[int, str] = {}
    for idx, c in enumerate(routed):
        ua, ub = unit_of(c.a), unit_of(c.b)
        name = f"{c.a}--{c.b}"
        if name in p2p_name.values():
            name = f"{name}#{idx}"
        p2p_name[idx] = name
        reqs[ua if ua == ub else 0].append(AllocRequest(name, kind="p2p"))
    for tn in t.tunnels:
        reqs[0].append(AllocRequest(f"{tn.a} {tn.a_if}--{tn.b} {tn.b_if}", kind="p2p"))

    # ---- allocate (hierarchically when there is more than one unit)
    subnets: list[Subnet] = []
    blocks: dict[UnitKey, Subnet] = {}
    unit_by_subnet: dict[str, UnitKey] = {}
    if len(reqs) == 1:
        (k, rs), = reqs.items()
        subs, rat = allocate(inp.root_prefix, rs)
        log.extend(rat)
        for s in subs:
            s.unit, unit_by_subnet[s.name] = unit_name(k), k
        subnets += subs
    else:
        keys = sorted(reqs, key=str)
        sizes = {k: 1 << (sum(1 << (32 - r.prefix) for r in reqs[k]) - 1).bit_length() for k in keys}
        bsubs, rat = allocate(inp.root_prefix, [AllocRequest(unit_name(k), sizes[k], "block") for k in keys])
        log.extend(rat)
        by_name = {s.name: s for s in bsubs}
        for k in keys:
            blocks[k] = by_name[unit_name(k)]
            subs, rat = allocate(f"{blocks[k].network}/{blocks[k].prefix}", reqs[k])
            log.extend(rat)
            for s in subs:
                s.unit, unit_by_subnet[s.name] = unit_name(k), k
            subnets += subs
    if t.tunnels:
        subs, rat = allocate(C.INTERNET_UNDERLAY, [AllocRequest(f"{tn.a}--{tn.b} underlay", kind="p2p")
                                                   for tn in t.tunnels])
        log.extend(rat)
        for s in subs:
            s.unit = "internet underlay"
        subnets += subs
    sub = {s.name: s for s in subnets}

    # ---- assign addresses
    for seg in inp.segments:
        s, gws = sub[seg.name], gws_of[seg.name]
        first = B.ip_to_int(s.first_usable)
        for n, (_, i) in enumerate(gws):
            i.mask = s.mask
            if len(gws) == 2:
                i.ip, i.hsrp_vip = B.int_to_ip(first + 1 + n), s.gateway
            else:
                i.ip = s.gateway
    for d in devs.values():
        if d.l3:
            lo = d.iface("Loopback0")
            lo.ip, lo.mask = sub[f"{d.hostname} Loopback0"].first_usable, "255.255.255.255"
    for idx, c in enumerate(routed):
        _p2p(devs, c.a, c.a_if, c.b, c.b_if, sub[p2p_name[idx]])
    for tn in t.tunnels:
        _p2p(devs, tn.a, tn.a_if, tn.b, tn.b_if, sub[f"{tn.a} {tn.a_if}--{tn.b} {tn.b_if}"])
        u = sub[f"{tn.a}--{tn.b} underlay"]
        _p2p(devs, tn.a, tn.underlay.a_if, tn.b, tn.underlay.b_if, u)
        devs[tn.a].iface(tn.a_if).tunnel_destination = u.last_usable
        devs[tn.b].iface(tn.b_if).tunnel_destination = u.first_usable
        devs[tn.a].ipsec_peers.append(u.last_usable)
        devs[tn.b].ipsec_peers.append(u.first_usable)
        log.add("ROUTE.ipsec", link=tn.link, a=tn.a, b=tn.b, underlay=C.INTERNET_UNDERLAY)

    # ---- OSPF areas per interface (cloud side and underlay stay out of OSPF)
    for d in devs.values():
        for i in d.interfaces:
            if i.ip is None or i.mode == "underlay" or d.role == "cloud":
                continue
            if i.peer and devs[i.peer.split()[0]].role == "cloud":
                continue
            name = _subnet_name(d.hostname, i, sub, p2p_name, routed, t)
            key = unit_by_subnet.get(name)
            i.area = key if isinstance(key, int) else None

    areas = {unit_name(k): k for k in reqs if isinstance(k, int)}
    for k in sorted(k for k in reqs if isinstance(k, int)):
        blk = f"{blocks[k].network}/{blocks[k].prefix}" if k in blocks else inp.root_prefix
        log.add("ROUTE.area", unit=unit_name(k), area=k, block=blk)
    log.add("ROUTE.rid")
    log.add("ROUTE.ospf_auth")
    log.add("ROUTE.ref_bw", ref=C.OSPF_REF_BW_MBPS, default=C.OSPF_DEFAULT_REF_BW_MBPS)

    for d in devs.values():
        if not d.l3 or d.role == "cloud":
            continue
        rid = d.iface("Loopback0").ip
        o = OspfConfig(pid=C.OSPF_PID, router_id=rid, ref_bw=C.OSPF_REF_BW_MBPS)
        for i in d.interfaces:
            if i.area is not None:
                o.networks.append((i.ip, "0.0.0.0", i.area))
                if i.mode in ("svi", "loopback"):
                    o.passive.append(i.name)
                else:
                    i.ospf_key = C.OSPF_MD5_KEY
        o.auth_areas = sorted({a for _, _, a in o.networks})
        my_areas = {a for _, _, a in o.networks}
        if 0 in my_areas and len(my_areas) > 1:
            for a in sorted(my_areas - {0}):
                b = blocks[a]
                o.summaries.append((a, b.network, b.mask))
                count = sum(1 for k in unit_by_subnet.values() if k == a)
                log.add("ROUTE.summary", abr=d.hostname, area=a, block=f"{b.network}/{b.prefix}", count=count)
        d.ospf = o

    # ---- eBGP to cloud sites
    asn: dict[str, int] = {}
    clouds = [s.name for s in inp.sites if s.kind.value == "cloud"]
    for n, site in enumerate(clouds):
        vgw = devs[t.routers[site][0]]
        cloud_asn = C.CLOUD_ASN_BASE + n
        asn[vgw.hostname] = cloud_asn
        vgw.bgp = vgw.bgp or BgpConfig(asn=cloud_asn, router_id=vgw.iface("Loopback0").ip)
        for i in vgw.interfaces:
            if i.mode in ("routed", "loopback") and i.ip and (i.segment or i.mode == "loopback"):
                vgw.bgp.networks.append((B.int_to_ip(B.network(B.ip_to_int(i.ip), B.mask_to_prefix(B.ip_to_int(i.mask)))), i.mask))
        for i in vgw.interfaces:
            if i.mode not in ("routed", "tunnel") or not i.peer or i.segment:
                continue
            peer_host, peer_if = i.peer.split()
            ent = devs[peer_host]
            pi = ent.iface(peer_if)
            vgw.bgp.neighbors.append((pi.ip, C.ENTERPRISE_ASN))
            if ent.bgp is None:
                ent.bgp = BgpConfig(asn=C.ENTERPRISE_ASN, router_id=ent.iface("Loopback0").ip)
                for k, b in sorted(blocks.items(), key=lambda kv: str(kv[0])):
                    if isinstance(k, int):
                        ent.bgp.networks.append((b.network, b.mask))
                        ent.static_routes.append(StaticRoute(network=b.network, mask=b.mask, next_hop="Null0",
                                                              distance=C.FLOATING_STATIC_AD))
                if ent.ospf:
                    ent.ospf.redistribute_bgp = C.ENTERPRISE_ASN
                log.add("ROUTE.bgp_anchor", router=ent.hostname, ad=C.FLOATING_STATIC_AD,
                        count=len(ent.static_routes))
            ent.bgp.neighbors.append((i.ip, cloud_asn))
            asn[ent.hostname] = C.ENTERPRISE_ASN
            log.add("ROUTE.ebgp", ent=ent.hostname, ent_asn=C.ENTERPRISE_ASN, cloud=vgw.hostname, cloud_asn=cloud_asn)

    decision = RoutingDecision(
        protocol=PROTOCOL_LABEL[proto] + (" + eBGP" if clouds else ""),
        areas=areas, asn=asn,
        rationale=[r for r in log.items[start:] if r.domain == "ROUTE"],
    )
    return decision, subnets


def _p2p(devs, a, a_if, b, b_if, s: Subnet) -> None:
    ia, ib = devs[a].iface(a_if), devs[b].iface(b_if)
    ia.ip, ia.mask = s.first_usable, s.mask
    ib.ip, ib.mask = s.last_usable, s.mask


def _subnet_name(host: str, i: Interface, sub, p2p_name, routed, t: Topology) -> str:
    if i.segment:
        return i.segment
    if i.mode == "loopback":
        return f"{host} Loopback0"
    if i.mode == "tunnel":
        tn = next(x for x in t.tunnels if (x.a, x.a_if) == (host, i.name) or (x.b, x.b_if) == (host, i.name))
        return f"{tn.a} {tn.a_if}--{tn.b} {tn.b_if}"
    idx = next(n for n, c in enumerate(routed) if (c.a, c.a_if) == (host, i.name) or (c.b, c.b_if) == (host, i.name))
    return p2p_name[idx]


def _check_backbone_adjacency(t: Topology, others: list[str]) -> None:
    """Area 0 must be contiguous: each non-backbone site needs a direct circuit to the backbone."""
    bb = set(t.routers.get(t.backbone, []))
    for site in others:
        mine = set(t.routers.get(site, []))
        linked = any(
            (c.a in mine and c.b in bb) or (c.b in mine and c.a in bb)
            for c in t.cables if c.kind in ("routed", "underlay")
        )
        if not linked:
            raise TopologyError(
                f"site '{site}' has no direct link to backbone site '{t.backbone}'; area 0 would be "
                f"discontiguous (OSPF virtual links are not generated)", site=site, backbone=t.backbone)
