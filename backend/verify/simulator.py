"""Phase 11: forwarding simulator built only from parsed IOS configs + the physical cabling.

L2: per-VLAN broadcast domains over trunks (both ends must allow the VLAN and have it defined).
L3: connected + static + OSPF (Dijkstra, area summaries, external from BGP) + eBGP; RIB by AD;
FIB = longest-prefix match. ACLs: first match, implicit deny. `trace()` walks hop by hop.
"""

import heapq
from collections import defaultdict
from dataclasses import dataclass, field

from pydantic import BaseModel

from engine import bitmath as B
from engine.models import Cable
from verify.ios_parser import PAclEntry, PDevice, PIface

# Administrative distances (Cisco defaults, docs/standards.md)
AD = {"connected": 0, "static": 1, "ebgp": 20, "ospf": 110, "ospf_ext": 110}
# UNVERIFIED: platform-default interface bandwidths in Mb/s used for OSPF cost (docs/standards.md [verify])
BW_MBPS = {"TenGigabitEthernet": 10_000, "GigabitEthernet": 1_000, "Vlan": 1_000, "Tunnel": 0.1, "Loopback": None}
MAX_HOPS = 32


def _bw(ifname: str) -> float | None:
    for prefix, bw in BW_MBPS.items():
        if ifname.startswith(prefix):
            return bw
    return 1_000


def ospf_cost(ifname: str, ref_bw: int) -> int:
    bw = _bw(ifname)
    if bw is None:  # loopback stub
        return 1
    return max(1, min(65535, int(ref_bw / bw)))


def _net(ip: str, mask: str) -> tuple[int, int]:
    p = B.mask_to_prefix(B.ip_to_int(mask))
    return B.network(B.ip_to_int(ip), p), p


def _contains(net: int, p: int, ip: int) -> bool:
    return B.network(ip, p) == net


@dataclass
class Route:
    net: int
    prefix: int
    source: str            # connected | static | ospf | ospf_ext | ebgp | summary
    ad: int
    metric: int = 0
    out_if: str | None = None
    next_hop: str | None = None  # IP; None = directly connected; "Null0" = discard

    def __str__(self) -> str:
        via = "Null0" if self.next_hop == "Null0" else (self.next_hop or "connected")
        return f"{B.int_to_ip(self.net)}/{self.prefix} [{self.source} {self.ad}/{self.metric}] via {via}"


class Hop(BaseModel):
    device: str
    in_if: str | None = None
    out_if: str | None = None
    action: str           # forward | deliver | drop
    detail: str


class Trace(BaseModel):
    src: str
    dst: str
    proto: str
    port: int | None
    outcome: str          # delivered | dropped | no-route | loop
    reason: str
    hops: list[Hop]


@dataclass
class Host:
    ip: str
    mask: str
    gateway: str
    vlan: int | None = None   # None = attached to a routed interface (cloud subnet)
    segment: str = ""


@dataclass
class Simulator:
    devices: dict[str, PDevice]
    cables: list[Cable]
    hosts: list[Host] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._links: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
        self._build_l2()
        self._build_links()
        self.rib: dict[str, list[Route]] = {}
        self._build_rib()

    # ------------------------------------------------------------------ L2
    def _up(self, host: str, ifname: str) -> PIface | None:
        i = self.devices[host].interfaces.get(ifname)
        return None if i is None or i.shutdown else i

    def _carries(self, host: str, ifname: str, vlan: int) -> bool:
        i = self._up(host, ifname)
        if i is None or i.mode != "trunk" or vlan not in self.devices[host].vlans:
            return False
        return i.allowed_vlans is None or vlan in i.allowed_vlans

    def _build_l2(self) -> None:
        """Union-find over switches per VLAN -> broadcast domain id for (host, vlan)."""
        parent: dict[tuple[str, int], tuple[str, int]] = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        vlans = {v for d in self.devices.values() for v in d.vlans}
        for c in self.cables:
            if c.kind != "trunk":
                continue
            for v in vlans:
                if self._carries(c.a, c.a_if, v) and self._carries(c.b, c.b_if, v):
                    parent[find((c.a, v))] = find((c.b, v))
        self._domain = lambda host, v: find((host, v))

    def domain(self, host: str, vlan: int):
        return self._domain(host, vlan)

    def access_switches(self, vlan: int) -> list[str]:
        return [h for h, d in self.devices.items() for i in d.interfaces.values()
                if i.mode == "access" and i.access_vlan == vlan and not i.shutdown]

    # ------------------------------------------------------------------ L3 adjacency
    def _l3_ifaces(self):
        for h, d in self.devices.items():
            for i in d.interfaces.values():
                if i.ip and not i.shutdown:
                    yield h, i

    def _build_links(self) -> None:
        """(host, if) -> set of (host, if) reachable without routing (same wire / L2 domain / tunnel)."""
        for c in self.cables:
            ia, ib = self._up(c.a, c.a_if), self._up(c.b, c.b_if)
            if ia and ib and ia.ip and ib.ip and ia.mode is None and ib.mode is None:
                self._links[(c.a, c.a_if)].add((c.b, c.b_if))
                self._links[(c.b, c.b_if)].add((c.a, c.a_if))
        svis = [(h, i) for h, i in self._l3_ifaces() if i.name.startswith("Vlan")]
        for h1, i1 in svis:
            v = int(i1.name[4:])
            for h2, i2 in svis:
                if h1 != h2 and i2.name == i1.name and self.domain(h1, v) == self.domain(h2, v):
                    self._links[(h1, i1.name)].add((h2, i2.name))
        tunnels = [(h, i) for h, i in self._l3_ifaces() if i.tunnel_destination]
        owner = {i.ip: (h, i) for h, i in self._l3_ifaces()}
        for h, i in tunnels:
            src = self._up(h, i.tunnel_source or "")
            peer = owner.get(i.tunnel_destination)
            if not src or not src.ip or not peer:
                continue
            ph, pi = peer
            # the peer's tunnel must point back at our underlay address, and underlay must be wired
            for _, pt in [(ph, t) for t in self.devices[ph].interfaces.values() if t.tunnel_destination == src.ip]:
                if (ph, pi.name) in self._links[(h, src.name)] and not pt.shutdown:
                    self._links[(h, i.name)].add((ph, pt.name))

    def neighbors(self, host: str, ifname: str) -> set[tuple[str, str]]:
        return self._links[(host, ifname)]

    # ------------------------------------------------------------------ routing
    def _ospf_if_area(self, d: PDevice, i: PIface) -> int | None:
        if not d.ospf or not i.ip or i.shutdown:
            return None
        ip = B.ip_to_int(i.ip)
        for net, wc, area in d.ospf.networks:
            w = B.ip_to_int(wc)
            if ip & ~w & 0xFFFFFFFF == B.ip_to_int(net) & ~w & 0xFFFFFFFF:
                return area
        return None

    @staticmethod
    def _auth_ok(d: PDevice, i: PIface, pd: PDevice, pi: PIface, area: int) -> bool:
        """Adjacency forms only if both ends agree on authentication and keys (RFC 2328 Appendix D)."""
        auth_a, auth_b = area in d.ospf.area_auth, area in pd.ospf.area_auth
        if auth_a != auth_b:
            return False
        return not auth_a or (i.ospf_key is not None and i.ospf_key == pi.ospf_key)

    def _passive(self, d: PDevice, ifname: str) -> bool:
        return d.ospf.passive_default or ifname in d.ospf.passive

    def _build_rib(self) -> None:
        rib: dict[str, list[Route]] = defaultdict(list)
        for h, d in self.devices.items():
            for i in d.interfaces.values():
                if i.ip and not i.shutdown:
                    n, p = _net(i.ip, i.mask)
                    rib[h].append(Route(n, p, "connected", AD["connected"], out_if=i.name))
            for s in d.statics:
                n, p = _net(s.network, s.mask)
                rib[h].append(Route(n, p, "static", s.distance or AD["static"], next_hop=s.next_hop))

        # OSPF adjacency graph: edges (a, a_if) -> (b, b_if ip) with cost of a_if
        areas: dict[str, set[int]] = defaultdict(set)
        adv: dict[str, list[tuple[int, int, int]]] = defaultdict(list)  # host -> (net, prefix, area)
        graph: dict[str, list[tuple[str, int, str, str]]] = defaultdict(list)
        for h, d in self.devices.items():
            for i in d.interfaces.values():
                a = self._ospf_if_area(d, i)
                if a is None:
                    continue
                areas[h].add(a)
                n, p = _net(i.ip, i.mask)
                adv[h].append((n, p, a))
                if self._passive(d, i.name):
                    continue
                for ph, pif in self.neighbors(h, i.name):
                    pd = self.devices[ph]
                    pi = pd.interfaces[pif]
                    if self._ospf_if_area(pd, pi) == a and pd.ospf and not self._passive(pd, pif) \
                            and _net(pi.ip, pi.mask) == (n, p) and self._auth_ok(d, i, pd, pi, a):
                        graph[h].append((ph, ospf_cost(i.name, d.ospf.ref_bw), i.name, pi.ip))

        def spf(src: str):
            dist, first = {src: 0}, {src: None}
            pq = [(0, src)]
            while pq:
                c, u = heapq.heappop(pq)
                if c > dist[u]:
                    continue
                for v, w, oif, nh in sorted(graph[u]):
                    nc = c + w
                    if nc < dist.get(v, 1 << 60):
                        dist[v] = nc
                        first[v] = (oif, nh) if u == src else first[u]
                        heapq.heappush(pq, (nc, v))
            return dist, first

        # summaries: (area, net, prefix, abr)
        summaries = [(a, *_net(net, mask), h) for h, d in self.devices.items() if d.ospf
                     for a, net, mask in d.ospf.summaries if a in areas[h] and 0 in areas[h]]
        ospf_routers = [h for h, d in self.devices.items() if d.ospf]
        for h in ospf_routers:
            dist, first = spf(h)
            best: dict[tuple[int, int], Route] = {}

            def offer(n, p, cost, src):
                if src == h or src not in dist:
                    return
                oif, nh = first[src]
                r = Route(n, p, "ospf", AD["ospf"], cost, oif, nh)
                if (n, p) not in best or cost < best[(n, p)].metric:
                    best[(n, p)] = r

            for r_host, items in adv.items():
                for n, p, a in items:
                    covering = [s for s in summaries if s[0] == a and _contains(s[1], s[2], n) and s[2] <= p]
                    if covering and a not in areas[h]:
                        continue  # hidden behind the ABR summary
                    offer(n, p, dist.get(r_host, 0), r_host)
            for a, sn, sp, abr in summaries:
                if a in areas[h] and abr != h:
                    continue
                if abr == h:
                    rib[h].append(Route(sn, sp, "summary", AD["ospf"], 0, next_hop="Null0"))
                else:
                    offer(sn, sp, dist.get(abr, 0), abr)
            rib[h].extend(best.values())
        self.rib = rib

        # eBGP: sessions up when both sides configure each other over a directly linked subnet
        learned: dict[str, list[Route]] = defaultdict(list)
        for h, d in self.devices.items():
            if not d.bgp:
                continue
            for nip, ras in d.bgp.neighbors:
                peer = self._owner_linked(h, nip)
                if not peer:
                    continue
                ph, pif = peer
                pd = self.devices[ph]
                my_ip = self.devices[h].interfaces[self._egress(h, nip)].ip
                if not pd.bgp or pd.bgp.asn != ras or (my_ip, d.bgp.asn) not in pd.bgp.neighbors:
                    continue
                for net, mask in pd.bgp.networks:
                    n, p = _net(net, mask)
                    if any(r.net == n and r.prefix == p for r in self.rib[ph]):  # network needs exact RIB match
                        learned[h].append(Route(n, p, "ebgp", AD["ebgp"], 0, self._egress(h, nip), nip))
        for h, routes in learned.items():
            self.rib[h].extend(routes)
            d = self.devices[h]
            if d.ospf and d.ospf.redistribute_bgp == (d.bgp.asn if d.bgp else None):
                dist_all = {o: spf(o) for o in ospf_routers}
                for o in ospf_routers:
                    if o == h:
                        continue
                    dist, first = dist_all[o]
                    if h in dist:
                        oif, nh = first[h]
                        for r in routes:
                            self.rib[o].append(Route(r.net, r.prefix, "ospf_ext", AD["ospf_ext"], 20, oif, nh))

    def _egress(self, host: str, ip: str) -> str | None:
        r = self.lookup(host, ip, connected_only=True)
        return r.out_if if r else None

    def _owner_linked(self, host: str, ip: str) -> tuple[str, str] | None:
        oif = self._egress(host, ip)
        if not oif:
            return None
        for ph, pif in self.neighbors(host, oif):
            if self.devices[ph].interfaces[pif].ip == ip:
                return ph, pif
        return None

    def lookup(self, host: str, ip: str, connected_only: bool = False) -> Route | None:
        x = B.ip_to_int(ip)
        cands = [r for r in self.rib.get(host, []) if _contains(r.net, r.prefix, x)
                 and (not connected_only or r.source == "connected")]
        if not cands:
            return None
        return min(cands, key=lambda r: (-r.prefix, r.ad, r.metric))

    # ------------------------------------------------------------------ ACL
    @staticmethod
    def acl_permits(entries: list[PAclEntry], src: str, dst: str, proto: str, port: int | None) -> tuple[bool, str]:
        s, t = B.ip_to_int(src), B.ip_to_int(dst)
        for n, e in enumerate(entries, start=1):
            if e.proto != "ip" and e.proto != proto:
                continue
            sw, dw = B.ip_to_int(e.src_wc), B.ip_to_int(e.dst_wc)
            if e.src != "any" and (s & ~sw & 0xFFFFFFFF) != (B.ip_to_int(e.src) & ~sw & 0xFFFFFFFF):
                continue
            if e.dst != "any" and (t & ~dw & 0xFFFFFFFF) != (B.ip_to_int(e.dst) & ~dw & 0xFFFFFFFF):
                continue
            if e.port is not None and e.port != port:
                continue
            text = f"line {n}: {e.action} {e.proto} {e.src} {e.dst}" + (f" eq {e.port}" if e.port else "")
            return e.action == "permit", text
        return False, "implicit deny"

    # ------------------------------------------------------------------ trace
    def _own_ips(self, host: str) -> set[str]:
        out = set()
        for i in self.devices[host].interfaces.values():
            if i.shutdown or not i.ip:
                continue
            out.add(i.ip)
            for g in i.hsrp.values():
                if g.ip and self._hsrp_active(host, i, g.ip):
                    out.add(g.ip)
        return out

    def _hsrp_active(self, host: str, i: PIface, vip: str) -> bool:
        v = int(i.name[4:]) if i.name.startswith("Vlan") else None
        best = None
        for ph, pi in [(host, i.name), *self.neighbors(host, i.name)]:
            p = self.devices[ph].interfaces[pi]
            for g in p.hsrp.values():
                if g.ip == vip and not p.shutdown:
                    key = (g.priority, B.ip_to_int(p.ip))
                    if best is None or key > best[0]:
                        best = (key, ph)
        return best is not None and best[1] == host and v is not None

    def _host_of(self, ip: str) -> Host | None:
        return next((h for h in self.hosts if h.ip == ip), None)

    def _host_reachable_from(self, host: str, ifname: str, h: Host) -> bool:
        i = self.devices[host].interfaces[ifname]
        if h.vlan is None:  # routed (cloud) subnet: host sits directly on the interface subnet
            return not i.name.startswith("Vlan") and _net(i.ip, i.mask) == _net(h.ip, h.mask)
        if i.name != f"Vlan{h.vlan}":
            return False
        dom = self.domain(host, h.vlan)
        return any(self.domain(sw, h.vlan) == dom for sw in self.access_switches(h.vlan))

    def _gateway_owner(self, h: Host) -> tuple[str, str] | None:
        for dev, d in self.devices.items():
            for i in d.interfaces.values():
                if i.shutdown or not i.ip:
                    continue
                if h.gateway in self._own_ips(dev) and (i.ip == h.gateway or any(g.ip == h.gateway for g in i.hsrp.values())):
                    if self._host_reachable_from(dev, i.name, h):
                        return dev, i.name
        return None

    def trace(self, src: str, dst: str, proto: str = "icmp", port: int | None = None) -> Trace:
        hops: list[Hop] = []

        def done(outcome, reason):
            return Trace(src=src, dst=dst, proto=proto, port=port, outcome=outcome, reason=reason, hops=hops)

        h = self._host_of(src)
        if h is None:
            return done("dropped", f"source {src} is not a known host")
        if _contains(*_net(h.ip, h.mask), B.ip_to_int(dst)) and self._host_of(dst):
            hops.append(Hop(device=f"host {src}", action="deliver", detail="same subnet, delivered at L2"))
            return done("delivered", "same subnet")
        gw = self._gateway_owner(h)
        if gw is None:
            hops.append(Hop(device=f"host {src}", action="drop", detail=f"gateway {h.gateway} not reachable at L2"))
            return done("dropped", f"gateway {h.gateway} unreachable from {h.segment or src}")
        dev, in_if = gw
        hops.append(Hop(device=f"host {src}", out_if=f"VLAN {h.vlan}" if h.vlan else None, action="forward",
                        detail=f"to default gateway {h.gateway} on {dev}"))
        visited: set[str] = set()
        for _ in range(MAX_HOPS):
            d = self.devices[dev]
            iface = d.interfaces[in_if]
            if iface.acl_in:
                ok, why = self.acl_permits(d.acls.get(iface.acl_in, []), src, dst, proto, port)
                if not ok:
                    hops.append(Hop(device=dev, in_if=in_if, action="drop", detail=f"ACL {iface.acl_in} in: {why}"))
                    return done("dropped", f"denied by {iface.acl_in} on {dev} {in_if} ({why})")
            if dst in self._own_ips(dev):
                hops.append(Hop(device=dev, in_if=in_if, action="deliver", detail="destination is this device"))
                return done("delivered", f"reached {dev}")
            if dev in visited:
                hops.append(Hop(device=dev, in_if=in_if, action="drop", detail="routing loop"))
                return done("loop", f"packet returned to {dev}")
            visited.add(dev)
            r = self.lookup(dev, dst)
            if r is None:
                hops.append(Hop(device=dev, in_if=in_if, action="drop", detail="no route"))
                return done("no-route", f"{dev} has no route to {dst}")
            if r.next_hop == "Null0":
                hops.append(Hop(device=dev, in_if=in_if, action="drop", detail=f"discard route {r}"))
                return done("dropped", f"{dev} discards via {r}")
            out_if = r.out_if or self._egress(dev, r.next_hop)  # static next hop: recursive lookup
            if out_if is None:
                hops.append(Hop(device=dev, in_if=in_if, action="drop", detail=f"next hop {r.next_hop} unresolvable"))
                return done("dropped", f"{dev}: next hop {r.next_hop} not on a connected subnet")
            eg = d.interfaces[out_if]
            if eg.acl_out:
                ok, why = self.acl_permits(d.acls.get(eg.acl_out, []), src, dst, proto, port)
                if not ok:
                    hops.append(Hop(device=dev, in_if=in_if, out_if=out_if, action="drop", detail=f"ACL {eg.acl_out} out: {why}"))
                    return done("dropped", f"denied by {eg.acl_out} out on {dev}")
            if r.next_hop is None:  # connected
                target = self._host_of(dst)
                if target and self._host_reachable_from(dev, out_if, target):
                    hops.append(Hop(device=dev, in_if=in_if, out_if=out_if, action="deliver",
                                    detail=f"connected {r}; delivered to host"))
                    return done("delivered", f"delivered by {dev}")
                nh = dst
            else:
                nh = r.next_hop
            nxt = next(((ph, pif) for ph, pif in self.neighbors(dev, out_if)
                        if self.devices[ph].interfaces[pif].ip == nh or nh in self._own_ips(ph)
                        and self.devices[ph].interfaces[pif].ip), None)
            if nxt is None:
                hops.append(Hop(device=dev, in_if=in_if, out_if=out_if, action="drop", detail=f"next hop {nh} unreachable"))
                return done("dropped", f"{dev}: next hop {nh} not reachable on {out_if}")
            enc = " (IPsec encrypted)" if eg.tunnel_mode == "ipsec ipv4" else ""
            hops.append(Hop(device=dev, in_if=in_if, out_if=out_if, action="forward", detail=f"route {r}{enc}"))
            dev, in_if = nxt
        return done("loop", f"exceeded {MAX_HOPS} hops")
