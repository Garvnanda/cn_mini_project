"""LLQ on router interfaces of links that carry a latency budget (D-026)."""

from engine import constants as C
from engine.models import DesignInput, Device
from engine.rationale import RationaleLog


def apply_qos(inp: DesignInput, devices: dict[str, Device], cables, log: RationaleLog) -> None:
    budget = {ln.key: ln.max_latency_ms for ln in inp.links if ln.max_latency_ms is not None}
    for c in cables:
        if c.link not in budget:
            continue
        for host, ifname in ((c.a, c.a_if), (c.b, c.b_if)):
            d = devices[host]
            if d.role not in ("router", "cloud"):
                continue
            d.qos = True
            d.iface(ifname).service_policy = C.QOS_POLICY
            log.add("QOS.llq", device=host, iface=ifname, link=c.link, pct=C.QOS_PRIORITY_PCT,
                    budget_ms=budget[c.link])
