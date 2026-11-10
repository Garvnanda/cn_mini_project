"""Phase 12: automated verification of generated configs against the design intent."""

from pydantic import BaseModel

from engine import bitmath as B
from engine.configgen import render_all
from engine.models import DesignResult
from verify.ios_parser import ParseError, PDevice, parse_config
from verify.simulator import Host, Simulator, Trace


class Check(BaseModel):
    name: str
    passed: bool
    details: list[str] = []


class Probe(BaseModel):
    src: str            # segment name
    dst: str
    proto: str
    port: int | None
    expected: str       # delivered | dropped
    actual: str
    reason: str


class VerificationReport(BaseModel):
    passed: bool
    checks: list[Check]
    probes: list[Probe]
    traces: list[Trace]

    def summary(self) -> str:
        lines = [f"Verification: {'PASS' if self.passed else 'FAIL'}"]
        for c in self.checks:
            lines.append(f"  [{'ok' if c.passed else 'FAIL'}] {c.name}" + (f": {c.details[0]}" if c.details and not c.passed else ""))
        return "\n".join(lines)


def build_simulator(result: DesignResult, configs: dict[str, str] | None = None) -> tuple[Simulator, dict[str, PDevice]]:
    configs = configs if configs is not None else render_all(result)
    parsed = {h: parse_config(t) for h, t in configs.items()}
    sim = Simulator(parsed, result.cables, hosts=_hosts(result))
    return sim, parsed


def _hosts(result: DesignResult) -> list[Host]:
    subs = {s.name: s for s in result.subnets}
    cloud = {s.name for s in result.input.sites if s.kind.value == "cloud"}
    out = []
    for seg in result.input.segments:
        s = subs[seg.name]
        out.append(Host(ip=s.last_usable, mask=s.mask, gateway=s.gateway, segment=seg.name,
                        vlan=None if seg.location in cloud else seg.vlan))
    return out


def expected_action(result: DesignResult, src: str, dst: str, proto: str, port: int | None) -> str:
    """Intent: first matching policy of the source segment decides; default is allow (D-020)."""
    for p in result.input.policies:
        if p.src != src or p.dst != dst:
            continue
        if p.proto != "ip" and p.proto != proto:
            continue
        if p.port is not None and p.port != port:
            continue
        return "delivered" if p.action.value == "allow" else "dropped"
    return "delivered"


def verify(result: DesignResult, configs: dict[str, str] | None = None) -> VerificationReport:
    checks: list[Check] = []
    try:
        sim, parsed = build_simulator(result, configs)
    except ParseError as e:
        return VerificationReport(passed=False, checks=[Check(name="config_parse", passed=False, details=[e.message])],
                                  probes=[], traces=[])
    unparsed = [f"{h}: {line}" for h, d in parsed.items() for line in d.unparsed]
    checks.append(Check(name="config_parse", passed=not unparsed, details=unparsed))

    host_of = {h.segment: h for h in sim.hosts}
    traces: list[Trace] = []

    # gateway reachability
    bad = []
    for h in sim.hosts:
        t = sim.trace(h.ip, h.gateway)
        traces.append(t)
        if t.outcome != "delivered":
            bad.append(f"{h.segment}: {t.reason}")
    checks.append(Check(name="gateway_reachability", passed=not bad, details=bad))

    # reachability + policy intent (icmp between every pair, plus each policy's own proto/port)
    probes: list[Probe] = []
    cases = [(a, b, "icmp", None) for a in host_of for b in host_of if a != b]
    cases += [(p.src, p.dst, p.proto if p.proto != "ip" else "icmp", p.port) for p in result.input.policies]
    for a, b, proto, port in dict.fromkeys(cases):
        t = sim.trace(host_of[a].ip, host_of[b].ip, proto, port)
        traces.append(t)
        actual = "delivered" if t.outcome == "delivered" else "dropped"
        probes.append(Probe(src=a, dst=b, proto=proto, port=port, expected=expected_action(result, a, b, proto, port),
                            actual=actual, reason=t.reason))
    wrong = [f"{p.src} -> {p.dst} {p.proto}{' ' + str(p.port) if p.port else ''}: expected {p.expected}, got {p.actual} ({p.reason})"
             for p in probes if p.expected != p.actual]
    checks.append(Check(name="reachability_and_policy", passed=not wrong, details=wrong))

    loops = [f"{t.src} -> {t.dst}: {t.reason}" for t in traces if t.outcome == "loop"]
    checks.append(Check(name="no_routing_loops", passed=not loops, details=loops))
    checks.append(_overlap_check(sim))
    checks.append(_access_trunk_scope(sim, result))
    return VerificationReport(passed=all(c.passed for c in checks), checks=checks, probes=probes, traces=traces)


def _overlap_check(sim: Simulator) -> Check:
    """Distinct connected subnets must not overlap; identical subnets must sit on the same link/L2 domain."""
    nets: dict[tuple[int, int], list[tuple[str, str]]] = {}
    for h, d in sim.devices.items():
        for i in d.interfaces.values():
            if i.ip and not i.shutdown:
                p = B.mask_to_prefix(B.ip_to_int(i.mask))
                nets.setdefault((B.network(B.ip_to_int(i.ip), p), p), []).append((h, i.name))
    keys = sorted(nets)
    bad = []
    for (n1, p1), (n2, p2) in zip(keys, keys[1:]):
        if B.network(n2, p1) == n1 and (n1, p1) != (n2, p2):
            bad.append(f"{B.int_to_ip(n1)}/{p1} overlaps {B.int_to_ip(n2)}/{p2} ({nets[(n1, p1)][0]} vs {nets[(n2, p2)][0]})")
    for (n, p), members in nets.items():
        first = members[0]
        for m in members[1:]:
            if m not in sim.neighbors(*first) and first not in sim.neighbors(*m):
                bad.append(f"{B.int_to_ip(n)}/{p} configured on unconnected interfaces {first} and {m}")
    return Check(name="no_overlapping_subnets", passed=not bad, details=bad)


def _access_trunk_scope(sim: Simulator, result: DesignResult) -> Check:
    """Access stacks are leaves: trunks touching them may only carry VLANs that have access ports there."""
    bad = []
    for c in result.cables:
        if c.kind != "trunk":
            continue
        for leaf, leaf_if, other, other_if in ((c.a, c.a_if, c.b, c.b_if), (c.b, c.b_if, c.a, c.a_if)):
            ld = sim.devices[leaf]
            local = {i.access_vlan for i in ld.interfaces.values() if i.mode == "access" and not i.shutdown}
            if not local:
                continue  # not an access switch
            for host, ifname in ((leaf, leaf_if), (other, other_if)):
                i = sim.devices[host].interfaces[ifname]
                allowed = set(range(1, 4095)) if i.allowed_vlans is None else set(i.allowed_vlans)
                extra = allowed - local
                if extra:
                    shown = "all" if i.allowed_vlans is None else ",".join(map(str, sorted(extra)))
                    bad.append(f"{host} {ifname} carries VLAN(s) {shown} with no ports on {leaf}")
    return Check(name="access_trunk_scope", passed=not bad, details=bad)
