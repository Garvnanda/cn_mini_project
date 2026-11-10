"""Phase 14: what-if failure engine + single-point-of-failure analysis."""

import copy

from pydantic import BaseModel

from engine import constants as C
from engine.configgen import render_all
from engine.errors import InvalidParameterError
from engine.models import Cable, DesignResult, Rationale
from engine.rationale import explain
from verify.ios_parser import parse_config
from verify.simulator import Simulator, Trace
from verify.verifier import _hosts


class FlowChange(BaseModel):
    src: str
    dst: str
    before: str
    after: str
    before_path: list[str]
    after_path: list[str]
    reason: str


class FailureImpact(BaseModel):
    failed: list[str]
    broken: list[FlowChange]
    rerouted: list[FlowChange]
    unaffected: int
    rationale: list[Rationale]

    @property
    def survives(self) -> bool:
        return not self.broken


class SpofReport(BaseModel):
    spof_devices: list[str]
    spof_cables: list[str]
    score: int
    rationale: list[Rationale]


def cable_id(c: Cable) -> str:
    return f"{c.a}:{c.a_if}--{c.b}:{c.b_if}"


def _match_cables(result: DesignResult, spec: str) -> list[Cable]:
    """'A--B' = every cable between devices A and B; 'A:IF--B:IF' = one cable."""
    a, sep, b = spec.partition("--")
    if not sep:
        raise InvalidParameterError(f"link spec '{spec}' must look like DEV--DEV or DEV:IF--DEV:IF", spec=spec)
    out = []
    for c in result.cables:
        for x, y in ((a, b), (b, a)):
            if ":" in x and f"{c.a}:{c.a_if}" == x and f"{c.b}:{c.b_if}" == y:
                out.append(c)
            elif ":" not in x and {c.a, c.b} == {x, y}:
                out.append(c)
    if not out:
        raise InvalidParameterError(f"no cable matches '{spec}'", spec=spec)
    return list({cable_id(c): c for c in out}.values())


def _path(t: Trace) -> list[str]:
    return [h.device for h in t.hops]


def _matrix(sim: Simulator) -> dict[tuple[str, str], Trace]:
    return {(a.segment, b.segment): sim.trace(a.ip, b.ip) for a in sim.hosts for b in sim.hosts if a is not b}


def simulate_failure(result: DesignResult, links: list[str] = (), nodes: list[str] = (),
                     configs: dict[str, str] | None = None) -> FailureImpact:
    configs = configs if configs is not None else render_all(result)
    base = {h: parse_config(t) for h, t in configs.items()}
    hosts = _hosts(result)
    before = _matrix(Simulator(base, result.cables, hosts=hosts))

    failed_devs = copy.deepcopy(base)
    rat: list[Rationale] = []
    names = []
    for n in nodes:
        if n not in failed_devs:
            raise InvalidParameterError(f"unknown device '{n}'", device=n)
        for i in failed_devs[n].interfaces.values():
            i.shutdown = True
        names.append(n)
        rat.append(_node_rationale(result, n))
    for spec in links:
        for c in _match_cables(result, spec):
            failed_devs[c.a].interfaces[c.a_if].shutdown = True
            failed_devs[c.b].interfaces[c.b_if].shutdown = True
            names.append(cable_id(c))
            rat.append(explain("WHATIF.rstp" if c.kind == "trunk" else "WHATIF.ospf", element=cable_id(c),
                               dead=C.OSPF_DEAD_S, hello=C.OSPF_HELLO_S))
    after = _matrix(Simulator(failed_devs, result.cables, hosts=hosts))

    broken, rerouted, same = [], [], 0
    for key, tb in before.items():
        ta = after[key]
        fc = FlowChange(src=key[0], dst=key[1], before=tb.outcome, after=ta.outcome,
                        before_path=_path(tb), after_path=_path(ta), reason=ta.reason)
        if tb.outcome == "delivered" and ta.outcome != "delivered":
            broken.append(fc)
        elif _path(tb) != _path(ta):
            rerouted.append(fc)
        else:
            same += 1
    return FailureImpact(failed=names, broken=broken, rerouted=rerouted, unaffected=same, rationale=rat)


def _node_rationale(result: DesignResult, host: str) -> Rationale:
    d = result.device(host)
    if any(i.hsrp_group is not None and i.hsrp_priority == C.HSRP_ACTIVE_PRIORITY for i in d.interfaces):
        return explain("WHATIF.hsrp", element=host, hold=C.HSRP_HOLD_S, hello=C.HSRP_HELLO_S)
    return explain("WHATIF.ospf", element=host, dead=C.OSPF_DEAD_S, hello=C.OSPF_HELLO_S)


def _hosting(result: DesignResult) -> set[str]:
    """Devices that attach segments: access stacks and cloud VGWs."""
    return {d.hostname for d in result.devices
            if d.role == "access" or (d.role == "cloud" and any(i.segment for i in d.interfaces))}


def _split(result: DesignResult, hosting: set[str], skip_dev: str | None = None, skip_cable: str | None = None) -> set[str]:
    """Hosting devices cut off from the first reachable hosting device after removing one element."""
    adj: dict[str, set[str]] = {d.hostname: set() for d in result.devices if d.hostname != skip_dev}
    for c in result.cables:
        if cable_id(c) == skip_cable or skip_dev in (c.a, c.b):
            continue
        adj[c.a].add(c.b)
        adj[c.b].add(c.a)
    targets = sorted(hosting - {skip_dev})
    if not targets:
        return set()
    seen, stack = {targets[0]}, [targets[0]]
    while stack:
        for n in adj[stack.pop()] - seen:
            seen.add(n)
            stack.append(n)
    return set(targets) - seen


def spof_analysis(result: DesignResult) -> SpofReport:
    hosting = _hosting(result)
    rat: list[Rationale] = []
    devs, cabs = [], []
    infra = [d.hostname for d in result.devices if d.role != "access"]
    for h in infra:
        cut = _split(result, hosting, skip_dev=h)
        if cut:
            devs.append(h)
            rat.append(explain("WHATIF.spof", element=h, count=len(cut), examples=", ".join(sorted(cut)[:3])))
    for c in result.cables:
        cut = _split(result, hosting, skip_cable=cable_id(c))
        if cut:
            cabs.append(cable_id(c))
            rat.append(explain("WHATIF.spof", element=cable_id(c), count=len(cut), examples=", ".join(sorted(cut)[:3])))
    total = len(infra) + len(result.cables)
    spof = len(devs) + len(cabs)
    score = round(100 * (1 - spof / total)) if total else 100
    rat.append(explain("WHATIF.score", score=score, spof=spof, total=total))
    return SpofReport(spof_devices=devs, spof_cables=cabs, score=score, rationale=rat)
