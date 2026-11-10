"""Phase 17: versioned design snapshots and a 3-layer diff (decisions, IP plan, configs)."""

import difflib
from collections import defaultdict

from pydantic import BaseModel

from engine.configgen import render_all
from engine.models import DesignResult

SNAPSHOT_VERSION = 1

# rules that answer the same question share a family, so a changed answer shows as "changed"
FAMILY = {
    **dict.fromkeys(["L1.copper", "L1.mmf", "L1.smf_lr", "L1.smf_er", "L1.provider"], "L1.media"),
    **dict.fromkeys(["ROUTE.ospf_single", "ROUTE.ospf_large_flat", "ROUTE.ospf_multi_campus",
                     "ROUTE.ospf_multi_site"], "ROUTE.protocol"),
    **dict.fromkeys(["TOPO.collapsed_core", "TOPO.three_tier"], "TOPO.tier"),
}
IDENT = ["link", "name", "site", "block", "device", "peer", "abr", "area", "unit", "location", "switch",
         "src", "dst", "element", "router", "acl", "ent", "cloud"]


class DecisionChange(BaseModel):
    key: str
    change: str  # added | removed | changed
    old: list[str] = []
    new: list[str] = []
    old_rules: list[str] = []
    new_rules: list[str] = []


class SubnetChange(BaseModel):
    name: str
    change: str
    old: str | None = None
    new: str | None = None


class DesignDiff(BaseModel):
    decisions: list[DecisionChange]
    subnets: list[SubnetChange]
    configs: dict[str, str]  # hostname -> unified diff
    devices_added: list[str]
    devices_removed: list[str]

    @property
    def empty(self) -> bool:
        return not (self.decisions or self.subnets or self.configs or self.devices_added or self.devices_removed)


def snapshot(result: DesignResult) -> dict:
    return {"version": SNAPSHOT_VERSION, "design": result.model_dump(mode="json")}


def load_snapshot(data: dict) -> DesignResult:
    if data.get("version") != SNAPSHOT_VERSION:
        raise ValueError(f"unsupported snapshot version {data.get('version')}")
    return DesignResult.model_validate(data["design"])


def _key(r) -> str:
    ident = [f"{f}={r.inputs[f]}" for f in IDENT if f in r.inputs]
    return f"{FAMILY.get(r.rule_id, r.rule_id)}[{', '.join(ident)}]"


def _group(result: DesignResult):
    g = defaultdict(list)
    for r in result.rationale:
        g[_key(r)].append(r)
    return g


def diff(a: DesignResult, b: DesignResult) -> DesignDiff:
    ga, gb = _group(a), _group(b)
    decisions = []
    for k in sorted(ga.keys() | gb.keys()):
        old, new = [r.text for r in ga.get(k, [])], [r.text for r in gb.get(k, [])]
        if old == new:
            continue
        change = "added" if not old else "removed" if not new else "changed"
        decisions.append(DecisionChange(key=k, change=change, old=old, new=new,
                                        old_rules=[r.rule_id for r in ga.get(k, [])],
                                        new_rules=[r.rule_id for r in gb.get(k, [])]))

    sa = {s.name: f"{s.network}/{s.prefix}" for s in a.subnets}
    sb = {s.name: f"{s.network}/{s.prefix}" for s in b.subnets}
    subnets = []
    for n in sorted(sa.keys() | sb.keys()):
        if sa.get(n) != sb.get(n):
            change = "added" if n not in sa else "removed" if n not in sb else "changed"
            subnets.append(SubnetChange(name=n, change=change, old=sa.get(n), new=sb.get(n)))

    ca, cb = render_all(a), render_all(b)
    configs = {}
    for h in sorted(ca.keys() & cb.keys()):
        if ca[h] != cb[h]:
            configs[h] = "".join(difflib.unified_diff(
                ca[h].splitlines(keepends=True), cb[h].splitlines(keepends=True), f"a/{h}.cfg", f"b/{h}.cfg"))
    return DesignDiff(decisions=decisions, subnets=subnets, configs=configs,
                      devices_added=sorted(cb.keys() - ca.keys()), devices_removed=sorted(ca.keys() - cb.keys()))
