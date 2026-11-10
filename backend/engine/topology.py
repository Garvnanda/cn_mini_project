"""Phase 5: devices, ports and cables. L2 (l2.py) and routing (routing.py) decorate the result."""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

from engine import constants as C
from engine.errors import TopologyError
from engine.models import (
    Cable, DesignInput, Device, Interface, Link, Resiliency, Segment, SiteKind, Transport,
)
from engine.rationale import RationaleLog


def hostname(*parts: str) -> str:
    """IOS hostname: letters, digits, hyphens; starts with a letter; ≤ 63 chars."""
    s = re.sub(r"[^A-Za-z0-9-]+", "-", "-".join(parts)).strip("-").upper()
    s = re.sub(r"-{2,}", "-", s)
    if not s or not s[0].isalpha():
        s = "N-" + s
    return s[:63]


@dataclass
class Block:
    """One L2 domain: its locations, gateway switches (SVIs) and access stacks."""
    name: str
    site: str
    locations: list[str]
    gateways: list[str]
    access: list[str] = field(default_factory=list)
    vlans: list[int] = field(default_factory=list)


@dataclass
class Tunnel:
    a: str
    a_if: str
    b: str
    b_if: str
    underlay: Cable
    link: str


@dataclass
class Topology:
    devices: dict[str, Device] = field(default_factory=dict)
    cables: list[Cable] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    tunnels: list[Tunnel] = field(default_factory=list)
    tiers: dict[str, str] = field(default_factory=dict)
    site_of: dict[str, str] = field(default_factory=dict)       # location -> site
    routers: dict[str, list[str]] = field(default_factory=dict)  # site -> routers (or cloud VGW)
    cores: dict[str, list[str]] = field(default_factory=dict)    # site -> core switches
    backbone: str = ""
    multi_site: bool = False
    _ports: dict[str, int] = field(default_factory=dict)

    def add(self, dev: Device) -> Device:
        if dev.hostname in self.devices:
            raise TopologyError(f"duplicate hostname '{dev.hostname}'", hostname=dev.hostname)
        self.devices[dev.hostname] = dev
        return dev

    def port(self, host: str) -> str:
        pattern, first = C.PORT_PATTERN[self.devices[host].role]
        n = self._ports.get(host, first)
        self._ports[host] = n + 1
        return pattern.format(n=n)

    def connect(self, a: str, b: str, kind: str, link: str | None = None) -> Cable:
        ai, bi = self.port(a), self.port(b)
        self.devices[a].interfaces.append(Interface(name=ai, mode=kind, peer=f"{b} {bi}", description=f"to {b} {bi}"))
        self.devices[b].interfaces.append(Interface(name=bi, mode=kind, peer=f"{a} {ai}", description=f"to {a} {ai}"))
        cable = Cable(a=a, a_if=ai, b=b, b_if=bi, kind=kind, link=link)
        self.cables.append(cable)
        return cable


def build_topology(inp: DesignInput, log: RationaleLog) -> Topology:
    t = Topology()
    sites = {s.name: s for s in inp.sites}
    t.site_of = {s: s for s in sites} | {b.name: b.site for b in inp.buildings}
    enterprise = [s for s in inp.sites if s.kind != SiteKind.CLOUD]
    clouds = [s for s in inp.sites if s.kind == SiteKind.CLOUD]
    if not enterprise:
        raise TopologyError("at least one non-cloud site is required")
    t.multi_site = len(enterprise) > 1 or bool(clouds)
    hubs = [s.name for s in enterprise if s.kind in (SiteKind.HQ, SiteKind.DATACENTER)]
    t.backbone = hubs[0] if hubs else enterprise[0].name

    links = {frozenset((ln.a, ln.b)): ln for ln in inp.links}
    for site in enterprise:
        _build_site(t, inp, site.name, links, log)
    for i, site in enumerate(clouds):
        vgw = t.add(Device(hostname=hostname(site.name, "VGW"), role="cloud", site=site.name,
                           location=site.name, l3=True))
        t.routers[site.name] = [vgw.hostname]
        for seg in inp.segments:
            if seg.location == site.name:
                ifname = t.port(vgw.hostname)
                vgw.interfaces.append(Interface(name=ifname, mode="routed", segment=seg.name,
                                                description=f"VPC subnet {seg.name}"))
    _connect_sites(t, inp, log)
    return t


def _build_site(t: Topology, inp: DesignInput, site: str, links: dict, log: RationaleLog) -> None:
    redundant = inp.resiliency == Resiliency.HIGH
    kind = next(s.kind for s in inp.sites if s.name == site)
    bldgs = [b.name for b in inp.buildings if b.site == site]
    locs = bldgs or [site]

    def degree(loc: str) -> int:
        return sum(1 for ln in inp.links if loc in (ln.a, ln.b) and t.site_of[ln.a] == t.site_of[ln.b] == site)

    hub = max(locs, key=lambda loc: (degree(loc), -locs.index(loc)))
    segs_at: dict[str, list[Segment]] = defaultdict(list)
    for seg in inp.segments:
        if t.site_of[seg.location] == site:
            segs_at[hub if seg.location == site else seg.location].append(seg)
    endpoints = sum(s.hosts for v in segs_at.values() for s in v)

    tier = "three_tier" if len(bldgs) >= C.THREE_TIER_MIN_BUILDINGS else "collapsed_core"
    t.tiers[site] = tier
    log.add(f"TOPO.{tier}", site=site, buildings=len(bldgs) or 1,
            threshold=C.THREE_TIER_MIN_BUILDINGS, endpoints=endpoints)

    def uplink_link(loc_a: str, loc_b: str) -> str | None:
        if loc_a == loc_b:
            return None
        ln: Link | None = links.get(frozenset((loc_a, loc_b)))
        if ln is None:
            raise TopologyError(
                f"no link between '{loc_a}' and '{loc_b}': every building needs a direct link to the "
                f"building holding its gateway switches", a=loc_a, b=loc_b)
        return ln.key

    pair = 2 if redundant else 1
    cores: list[str] = []
    if segs_at:
        for i in range(1, pair + 1):
            cores.append(t.add(Device(hostname=hostname(site, f"CORE{i}"), role="core", site=site,
                                      location=hub, l3=True)).hostname)
        if len(cores) == 2:
            t.connect(cores[0], cores[1], "routed")
    t.cores[site] = cores

    if tier == "collapsed_core":
        blocks = [Block(name=site, site=site, locations=locs, gateways=cores)] if cores else []
    else:
        blocks = []
        for b in locs:
            if not segs_at.get(b):
                continue
            dists = [t.add(Device(hostname=hostname(b, f"DIST{i}"), role="distribution", site=site,
                                  location=b, l3=True)).hostname for i in range(1, pair + 1)]
            for d in dists:
                for c in cores:
                    t.connect(d, c, "routed", uplink_link(b, hub))
            blocks.append(Block(name=b, site=site, locations=[b], gateways=dists))

    for blk in blocks:
        if len(blk.gateways) == 2:
            t.connect(blk.gateways[0], blk.gateways[1], "trunk")
        gw_loc = t.devices[blk.gateways[0]].location
        for loc in blk.locations:
            if not segs_at.get(loc):
                continue
            for acc in _access_stacks(t, loc, site, segs_at[loc], log):
                blk.access.append(acc)
                for gw in blk.gateways:
                    t.connect(acc, gw, "trunk", uplink_link(loc, gw_loc))
        blk.vlans = sorted({v for a in blk.access for v in t.devices[a].vlans})
    t.blocks.extend(blocks)

    routers: list[str] = []
    if t.multi_site:
        n = pair if kind in (SiteKind.HQ, SiteKind.DATACENTER) else 1
        for i in range(1, n + 1):
            r = t.add(Device(hostname=hostname(site, f"R{i}"), role="router", site=site, location=hub, l3=True))
            routers.append(r.hostname)
            if cores:
                t.connect(r.hostname, cores[min(i, len(cores)) - 1], "routed")
    t.routers[site] = routers

    if redundant:
        what = " and ".join(x for x in [
            "core switches" if len(cores) == 2 else "",
            "distribution switches" if tier == "three_tier" else "",
            "routers" if len(routers) == 2 else "",
        ] if x) or "gateways"
        log.add("TOPO.redundant", site=site, what=what)


def _access_stacks(t: Topology, loc: str, site: str, segs: list[Segment], log: RationaleLog) -> list[str]:
    per, max_m = C.ACCESS_PORTS_PER_MEMBER, C.STACK_MAX_MEMBERS
    ports = sum(s.hosts for s in segs)
    members = math.ceil(ports / per)
    n_stacks = math.ceil(members / max_m)
    base, extra = divmod(members, n_stacks)
    sizes = [base + (1 if k < extra else 0) for k in range(n_stacks)]

    # flat list of (stack index, member, port) slots, filled segment by segment
    slots = [(k, m, p) for k, size in enumerate(sizes) for m in range(1, size + 1) for p in range(1, per + 1)]
    stacks = []
    for k, size in enumerate(sizes, start=1):
        stacks.append(t.add(Device(hostname=hostname(loc, f"ACC{k}"), role="access", site=site,
                                   location=loc, members=size)))
    cursor = 0
    poe_ports = defaultdict(int)
    for seg in segs:
        run = slots[cursor:cursor + seg.hosts]
        cursor += seg.hosts
        # group consecutive slots on the same stack + member into one `interface range`
        groups: dict[tuple[int, int], list[int]] = defaultdict(list)
        for k, m, p in run:
            groups[(k, m)].append(p)
        for (k, m), ps in groups.items():
            dev = stacks[k]
            dev.vlans[seg.vlan] = seg.name
            if seg.poe:
                poe_ports[k] += len(ps)
            dev.interfaces.append(_port_range(m, ps[0], ps[-1], "access", seg.vlan, f"{seg.name} ({seg.role.value})"))
    # spare ports
    spare = slots[cursor:]
    groups = defaultdict(list)
    for k, m, p in spare:
        groups[(k, m)].append(p)
    for (k, m), ps in groups.items():
        stacks[k].interfaces.append(_port_range(m, ps[0], ps[-1], "unused", None, "unused"))

    log.add("TOPO.access", location=loc, ports=ports, members=members, per=per, stacks=n_stacks,
            max_members=max_m, spare=len(spare))
    for k, n in poe_ports.items():
        stacks[k].poe_watts = n * C.POE_WATTS_PER_PORT
        log.add("TOPO.poe", switch=stacks[k].hostname, poe_ports=n, watts_per=C.POE_WATTS_PER_PORT,
                watts=stacks[k].poe_watts)
    return [s.hostname for s in stacks]


def _port_range(member: int, first: int, last: int, mode: str, vlan: int | None, desc: str) -> Interface:
    a = C.ACCESS_PORT.format(m=member, p=first)
    name = a if first == last else f"{a} - {last}"
    return Interface(name=name, range=first != last, mode=mode, vlan=vlan, description=desc)


def _connect_sites(t: Topology, inp: DesignInput, log: RationaleLog) -> None:
    for ln in inp.links:
        sa, sb = t.site_of[ln.a], t.site_of[ln.b]
        if sa == sb:
            continue
        ra, rb = t.routers.get(sa, []), t.routers.get(sb, [])
        if not ra or not rb:
            raise TopologyError(f"link {ln.key}: site without a router", link=ln.key)
        if len(ra) == 2 and len(rb) == 2:
            pairs = [(ra[0], rb[0]), (ra[1], rb[1])]
        elif len(ra) == 2:
            pairs = [(ra[0], rb[0]), (ra[1], rb[0])]
        elif len(rb) == 2:
            pairs = [(ra[0], rb[0]), (ra[0], rb[1])]
        else:
            pairs = [(ra[0], rb[0])]
        internet = ln.transport == Transport.INTERNET
        for x, y in pairs:
            cable = t.connect(x, y, "underlay" if internet else "routed", ln.key)
            if internet:
                xt, yt = _tunnel_name(t, x), _tunnel_name(t, y)
                t.devices[x].interfaces.append(Interface(name=xt, mode="tunnel", peer=f"{y} {yt}",
                                                         tunnel_source=cable.a_if, description=f"IPsec to {y}"))
                t.devices[y].interfaces.append(Interface(name=yt, mode="tunnel", peer=f"{x} {xt}",
                                                         tunnel_source=cable.b_if, description=f"IPsec to {x}"))
                t.tunnels.append(Tunnel(a=x, a_if=xt, b=y, b_if=yt, underlay=cable, link=ln.key))
        if len(pairs) == 2:
            log.add("TOPO.dual_homed", link=ln.key, n=2, pairs=", ".join(f"{x}–{y}" for x, y in pairs))

    # every site must be reachable from the backbone
    adj = defaultdict(set)
    for ln in inp.links:
        adj[t.site_of[ln.a]].add(t.site_of[ln.b])
        adj[t.site_of[ln.b]].add(t.site_of[ln.a])
    seen, stack = {t.backbone}, [t.backbone]
    while stack:
        for n in adj[stack.pop()] - seen:
            seen.add(n)
            stack.append(n)
    if missing := {s.name for s in inp.sites} - seen:
        raise TopologyError(f"sites not connected to {t.backbone}: {sorted(missing)}", sites=sorted(missing))


def _tunnel_name(t: Topology, host: str) -> str:
    n = sum(1 for i in t.devices[host].interfaces if i.mode == "tunnel") + 1
    return f"Tunnel{n}"


def graph(devices: list[Device], cables: list[Cable]) -> dict:
    """Adjacency for the UI: nodes with a simple layered layout (x = site, y = role tier)."""
    tier_y = {"cloud": 0, "router": 1, "core": 2, "distribution": 3, "access": 4}
    sites = list(dict.fromkeys(d.site for d in devices))
    col: dict[tuple[str, int], int] = defaultdict(int)
    nodes = []
    for d in devices:
        y = tier_y[d.role]
        x = sites.index(d.site) * 1000 + col[(d.site, y)] * 160
        col[(d.site, y)] += 1
        nodes.append({"id": d.hostname, "role": d.role, "site": d.site, "x": x, "y": y * 150})
    edges = [{"a": c.a, "a_if": c.a_if, "b": c.b, "b_if": c.b_if, "kind": c.kind, "media": c.media} for c in cables]
    return {"nodes": nodes, "edges": edges}
