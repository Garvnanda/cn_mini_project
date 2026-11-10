"""Phase 16: bill of materials + cost estimate. Prices are placeholders from data/prices.json."""

import json
import math
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel

from engine import constants as C
from engine.media import CAT6A, OM4
from engine.models import DesignResult, Rationale, Transport
from engine.rationale import explain

PRICES = Path(__file__).resolve().parent.parent / "data" / "prices.json"
OM3_MAX_M = 300   # 10GBASE-SR on OM3, IEEE 802.3ae (docs/standards.md)
CAT6_MAX_M = 55   # 10GBASE-T on Cat6, IEEE 802.3an (docs/standards.md)


class BomLine(BaseModel):
    item: str
    qty: float
    unit: str
    unit_price: float
    total: float
    rule_id: str      # decision that caused this line
    note: str = ""


class Bom(BaseModel):
    currency: str
    lines: list[BomLine]
    capex: float
    monthly: float
    poe_watts: dict[str, float]
    alternatives: list[Rationale]
    disclaimer: str


def load_prices(path: Path = PRICES) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _media_rule(result: DesignResult, link: str) -> str:
    m = next(x for x in result.media if x.link == link)
    return m.rationale[0].rule_id


def build_bom(result: DesignResult, prices: dict | None = None) -> Bom:
    p = prices or load_prices()
    slack = 1 + p["cable_slack_pct"] / 100
    lines: list[BomLine] = []

    def add(item, qty, unit, price, rule, note=""):
        if qty:
            lines.append(BomLine(item=item, qty=qty, unit=unit, unit_price=price, total=round(qty * price, 2),
                                 rule_id=rule, note=note))

    links = {ln.key: ln for ln in result.input.links}
    meters: dict[tuple[str, str], float] = defaultdict(float)
    xcvr: dict[tuple[str, str], int] = defaultdict(int)
    patch = 0
    for c in result.cables:
        if c.link is None:
            patch += 1
            continue
        ln = links[c.link]
        if ln.transport != Transport.FIBER:
            continue
        rule = _media_rule(result, c.link)
        meters[(c.media, rule)] += ln.distance_m * slack
        if c.transceiver != "10GBASE-T":
            xcvr[(c.transceiver, rule)] += 2  # one optic per cable end
    for (media, rule), m in sorted(meters.items()):
        add(media, math.ceil(m), "m", p["cable_per_m"][media], rule, f"incl. {p['cable_slack_pct']}% slack")
    add("Cat6a patch cord (in-building)", patch, "pcs", p["patch_cord_cat6a"], "L1.in_building")
    for (t, rule), n in sorted(xcvr.items()):
        add(f"SFP+ {t}", n, "pcs", p["transceiver"][t], rule)

    poe: dict[str, float] = {}
    members = defaultdict(int)
    for d in result.devices:
        if d.role == "access":
            members["access_48_poe" if d.poe_watts else "access_48"] += d.members
            if d.poe_watts:
                poe[d.hostname] = d.poe_watts
    add("48-port PoE+ access switch", members["access_48_poe"], "pcs", p["switch"]["access_48_poe"], "TOPO.poe")
    add("48-port access switch", members["access_48"], "pcs", p["switch"]["access_48"], "TOPO.access")
    roles = defaultdict(int)
    for d in result.devices:
        roles[d.role] += 1
    tier_rule = "TOPO.three_tier" if "three_tier" in result.tiers.values() else "TOPO.collapsed_core"
    add("Core switch", roles["core"], "pcs", p["switch"]["core"], tier_rule)
    add("Distribution switch", roles["distribution"], "pcs", p["switch"]["distribution"], "TOPO.three_tier")
    add("Router", roles["router"], "pcs", p["router"], "ROUTE.ospf_multi_site")
    add("Cloud virtual gateway", roles["cloud"], "pcs", p["cloud_vgw"], "ROUTE.ebgp", "billed by cloud provider")

    monthly = 0.0
    for kind in ("carrier", "internet"):
        circuits = sum(1 for c in result.cables if c.link and links[c.link].transport.value == kind)
        price = p["wan_service_per_month"][kind]
        add(f"{kind.title()} circuit (monthly)", circuits, "circuit/month", price, "L1.provider")
        monthly += circuits * price

    capex = round(sum(x.total for x in lines if not x.unit.endswith("/month")), 2)
    return Bom(currency=p["currency"], lines=lines, capex=capex, monthly=monthly, poe_watts=poe,
               alternatives=_alternatives(result, p, slack), disclaimer=p["_note"])


def _alternatives(result: DesignResult, p: dict, slack: float) -> list[Rationale]:
    """Suggest cheaper media only where every affected run still meets the cheaper medium's limit."""
    out = []
    for media, alt, limit in ((OM4, "OM3 multimode fiber", OM3_MAX_M), (CAT6A, "Cat6 UTP", CAT6_MAX_M)):
        runs = [m for m in result.media if m.media == media]
        if not runs or any(m.distance_m > limit for m in runs):
            continue
        meters = sum(m.distance_m for m in runs) * slack
        saving = round(meters * (p["cable_per_m"][media] - p["cable_per_m"][alt]))
        if saving > 0:
            out.append(explain("BOM.alternative", alt=alt, current=media, links=", ".join(m.link for m in runs),
                               limit=limit, saving=saving))
    return out


assert C.COPPER_MAX_M == 100  # Cat6 alternative only makes sense below the Cat6a reach
