"""Phase 10: parse Cisco IOS config text back into a device model (the verifier's only input).

Covers the command set in docs/ios_reference.md. Unknown lines are kept in `unparsed`
so the verifier can report them instead of silently ignoring them.
"""

from pydantic import BaseModel

from engine.errors import NetArchError


class ParseError(NetArchError):
    """Config text could not be parsed."""


class PAclEntry(BaseModel):
    action: str
    proto: str
    src: str        # network or "any"
    src_wc: str     # wildcard ("255.255.255.255" for any)
    dst: str
    dst_wc: str
    port: int | None = None


class PHsrp(BaseModel):
    ip: str | None = None
    priority: int = 100  # IOS default
    preempt: bool = False


class PIface(BaseModel):
    name: str
    range: bool = False
    description: str = ""
    switchport: bool | None = None   # None = not stated (platform default)
    mode: str | None = None          # access | trunk
    access_vlan: int | None = None
    native_vlan: int | None = None
    allowed_vlans: list[int] | None = None  # None = all
    portfast: bool = False
    bpduguard: bool = False
    ip: str | None = None
    mask: str | None = None
    shutdown: bool = False
    acl_in: str | None = None
    acl_out: str | None = None
    hsrp: dict[int, PHsrp] = {}
    hsrp_version: int = 1
    tunnel_source: str | None = None
    tunnel_destination: str | None = None
    tunnel_mode: str | None = None
    tunnel_profile: str | None = None


class POspf(BaseModel):
    pid: int
    router_id: str | None = None
    ref_bw: int = 100
    networks: list[tuple[str, str, int]] = []
    passive: list[str] = []
    passive_default: bool = False
    summaries: list[tuple[int, str, str]] = []
    redistribute_bgp: int | None = None


class PBgp(BaseModel):
    asn: int
    router_id: str | None = None
    neighbors: list[tuple[str, int]] = []
    networks: list[tuple[str, str]] = []


class PStatic(BaseModel):
    network: str
    mask: str
    next_hop: str
    distance: int | None = None


class PDevice(BaseModel):
    hostname: str = ""
    ip_routing: bool = False
    vlans: dict[int, str] = {}
    stp_mode: str | None = None
    stp_primary: list[int] = []
    stp_secondary: list[int] = []
    interfaces: dict[str, PIface] = {}
    ospf: POspf | None = None
    bgp: PBgp | None = None
    statics: list[PStatic] = []
    acls: dict[str, list[PAclEntry]] = {}
    isakmp_peers: list[str] = []
    unparsed: list[str] = []

    @property
    def is_switch(self) -> bool:
        return self.stp_mode is not None or bool(self.vlans)


def parse_vlan_list(s: str) -> list[int]:
    s = s.strip()
    if s == "none":
        return []
    if s == "all":
        return list(range(1, 4095))
    out: list[int] = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


def _addr(tokens: list[str]) -> tuple[str, str, list[str]]:
    """Consume an ACL address spec: any | host X | net wildcard."""
    if tokens[0] == "any":
        return "any", "255.255.255.255", tokens[1:]
    if tokens[0] == "host":
        return tokens[1], "0.0.0.0", tokens[2:]
    return tokens[0], tokens[1], tokens[2:]


def parse_acl_entry(line: str) -> PAclEntry:
    t = line.split()
    action, proto, rest = t[0], t[1], t[2:]
    src, swc, rest = _addr(rest)
    dst, dwc, rest = _addr(rest)
    port = int(rest[1]) if len(rest) >= 2 and rest[0] == "eq" else None
    return PAclEntry(action=action, proto=proto, src=src, src_wc=swc, dst=dst, dst_wc=dwc, port=port)


def parse_config(text: str) -> PDevice:
    d = PDevice()
    ctx: tuple[str, str | int] | None = None  # (kind, key)
    for n, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.strip().startswith("!"):
            if raw.strip().startswith("!"):
                ctx = None
            continue
        indented = raw[0] == " "
        line = raw.strip()
        t = line.split()
        try:
            if not indented:
                ctx = _top(d, line, t)
            else:
                _sub(d, ctx, line, t)
        except (IndexError, ValueError) as e:
            raise ParseError(f"line {n}: cannot parse {line!r}: {e}", line=n, text=line) from None
    return d


def _top(d: PDevice, line: str, t: list[str]):
    if t[0] == "hostname":
        d.hostname = t[1]
    elif line == "ip routing":
        d.ip_routing = True
    elif t[0] == "vlan" and len(t) == 2:
        d.vlans[int(t[1])] = ""
        return ("vlan", int(t[1]))
    elif line.startswith("spanning-tree mode"):
        d.stp_mode = t[2]
    elif line.startswith("spanning-tree vlan"):
        vlans = parse_vlan_list(t[2])
        (d.stp_primary if t[-1] == "primary" else d.stp_secondary).extend(vlans)
    elif t[0] == "interface":
        is_range = t[1] == "range"
        name = " ".join(t[2:] if is_range else t[1:])
        d.interfaces[name] = PIface(name=name, range=is_range)
        return ("interface", name)
    elif line.startswith("router ospf"):
        d.ospf = POspf(pid=int(t[2]))
        return ("ospf", 0)
    elif line.startswith("router bgp"):
        d.bgp = PBgp(asn=int(t[2]))
        return ("bgp", 0)
    elif line.startswith("ip route "):
        d.statics.append(PStatic(network=t[2], mask=t[3], next_hop=t[4], distance=int(t[5]) if len(t) > 5 else None))
    elif line.startswith("ip access-list extended"):
        d.acls[t[3]] = []
        return ("acl", t[3])
    elif line.startswith("crypto isakmp key"):
        d.isakmp_peers.append(t[-1])
    elif line.startswith(("crypto isakmp policy", "crypto ipsec", "line ")):
        return ("ignore", 0)
    elif line in ("end",) or t[0] in (
        "service", "no", "ip", "enable", "username", "crypto", "banner",
    ):
        pass  # management-plane lines with no forwarding effect
    else:
        d.unparsed.append(line)
    return None


def _sub(d: PDevice, ctx, line: str, t: list[str]) -> None:
    if ctx is None:
        d.unparsed.append(line)
        return
    kind, key = ctx
    if kind == "vlan" and t[0] == "name":
        d.vlans[key] = t[1]
    elif kind == "interface":
        _iface(d.interfaces[key], line, t)
    elif kind == "ospf":
        o = d.ospf
        if t[0] == "router-id":
            o.router_id = t[1]
        elif line.startswith("auto-cost reference-bandwidth"):
            o.ref_bw = int(t[2])
        elif line == "passive-interface default":
            o.passive_default = True
        elif t[0] == "passive-interface":
            o.passive.append(" ".join(t[1:]))
        elif t[0] == "network":
            o.networks.append((t[1], t[2], int(t[4])))
        elif t[0] == "area" and t[2] == "range":
            o.summaries.append((int(t[1]), t[3], t[4]))
        elif line.startswith("redistribute bgp"):
            o.redistribute_bgp = int(t[2])
        else:
            d.unparsed.append(line)
    elif kind == "bgp":
        b = d.bgp
        if line.startswith("bgp router-id"):
            b.router_id = t[2]
        elif t[0] == "neighbor" and t[2] == "remote-as":
            b.neighbors.append((t[1], int(t[3])))
        elif t[0] == "network":
            b.networks.append((t[1], t[3]))
        else:
            d.unparsed.append(line)
    elif kind == "acl":
        d.acls[key].append(parse_acl_entry(line))
    elif kind == "ignore":
        pass
    else:
        d.unparsed.append(line)


def _iface(i: PIface, line: str, t: list[str]) -> None:
    if t[0] == "description":
        i.description = line[len("description "):]
    elif line == "no switchport":
        i.switchport = False
    elif line == "switchport mode access":
        i.switchport, i.mode = True, "access"
    elif line == "switchport mode trunk":
        i.switchport, i.mode = True, "trunk"
    elif line.startswith("switchport access vlan"):
        i.access_vlan = int(t[3])
    elif line.startswith("switchport trunk native vlan"):
        i.native_vlan = int(t[4])
    elif line.startswith("switchport trunk allowed vlan"):
        i.allowed_vlans = parse_vlan_list(t[4])
    elif line == "spanning-tree portfast":
        i.portfast = True
    elif line == "spanning-tree bpduguard enable":
        i.bpduguard = True
    elif t[:2] == ["ip", "address"]:
        i.ip, i.mask = t[2], t[3]
    elif line == "shutdown":
        i.shutdown = True
    elif line == "no shutdown":
        i.shutdown = False
    elif t[:2] == ["ip", "access-group"]:
        if t[3] == "in":
            i.acl_in = t[2]
        else:
            i.acl_out = t[2]
    elif t[0] == "standby":
        if t[1] == "version":
            i.hsrp_version = int(t[2])
            return
        g = i.hsrp.setdefault(int(t[1]), PHsrp())
        if t[2] == "ip":
            g.ip = t[3]
        elif t[2] == "priority":
            g.priority = int(t[3])
        elif t[2] == "preempt":
            g.preempt = True
    elif line.startswith("tunnel source"):
        i.tunnel_source = t[2]
    elif line.startswith("tunnel destination"):
        i.tunnel_destination = t[2]
    elif line.startswith("tunnel mode"):
        i.tunnel_mode = " ".join(t[2:])
    elif line.startswith("tunnel protection ipsec profile"):
        i.tunnel_profile = t[4]
    else:
        raise ValueError("unknown interface command")
