"""L1 media engine: picks cable + transceiver per link and proves the optical budget."""

from engine import constants as C
from engine.errors import InvalidParameterError, PhysicalDistanceViolationError
from engine.models import Link, MediaDecision, MediaPreference, Rationale
from engine.rationale import explain

CAT6A = "Cat6a UTP"
OM4 = "OM4 multimode fiber"
OS2 = "OS2 single-mode fiber"

_DB_PER_KM = {
    "10GBASE-SR": C.MMF_850_DB_PER_KM,
    "10GBASE-LR": C.OS2_1310_DB_PER_KM,
    "10GBASE-ER": C.OS2_1550_DB_PER_KM,
}


def _r(x: float) -> float:
    return round(x, 2)


def optical_budget(
    link: str, transceiver: str, distance_m: float,
    connectors: int = C.DEFAULT_CONNECTORS, splices: int = 0,
) -> tuple[bool, float, Rationale]:
    """Return (fits, total_loss_db, rationale). Fits when loss ≤ channel insertion loss."""
    km = distance_m / 1000
    db_per_km = _DB_PER_KM[transceiver]
    fiber = km * db_per_km
    # round before comparing: float noise must not flip a pass at the exact limit (e.g. OM4 at 400 m)
    total = _r(fiber + connectors * C.CONNECTOR_DB + splices * C.SPLICE_DB)
    allowed = C.CHANNEL_LOSS_DB[transceiver]
    margin = _r(allowed - total)
    if margin < 0:
        verdict = "FAIL"
    elif margin < C.LOW_MARGIN_DB:
        verdict = f"pass, but below the {C.LOW_MARGIN_DB} dB design margin: verify with an OTDR test"
    else:
        verdict = "pass"
    r = explain(
        "L1.budget", link=link, transceiver=transceiver, km=_r(km), db_per_km=db_per_km,
        fiber_loss_db=_r(fiber), connectors=connectors, connector_db=C.CONNECTOR_DB,
        splices=splices, splice_db=C.SPLICE_DB, total_loss_db=_r(total),
        allowed_db=allowed, margin_db=_r(margin), verdict=verdict,
    )
    return margin >= 0, total, r


def _smf(link: Link, why_lr: str, splices: int) -> MediaDecision:
    d, key = link.distance_m, link.key
    if d > C.ER_MAX_M:
        r = explain("L1.distance_exceeded", link=key, distance_m=d)
        raise PhysicalDistanceViolationError(r.text, link=key, distance_m=d, limit_m=C.ER_MAX_M)
    if d <= C.LR_MAX_M:
        ok, _, budget = optical_budget(key, "10GBASE-LR", d, splices=splices)
        if ok:
            return MediaDecision(
                link=key, distance_m=d, media=OS2, transceiver="10GBASE-LR",
                rationale=[explain("L1.smf_lr", link=key, distance_m=d, reason=why_lr), budget],
            )
        er_reason = f"the 10GBASE-LR optical budget fails at {d} m ({budget.inputs['total_loss_db']} dB loss)"
        lr_fail = [budget]
    else:
        er_reason = f"{d} m exceeds the 10 km 10GBASE-LR reach"
        lr_fail = []
    ok, total, budget = optical_budget(key, "10GBASE-ER", d, splices=splices)
    if not ok:
        r = explain("L1.budget_violation", link=key, total_loss_db=_r(total),
                    allowed_db=C.CHANNEL_LOSS_DB["10GBASE-ER"])
        raise PhysicalDistanceViolationError(r.text, link=key, distance_m=d, total_loss_db=_r(total))
    return MediaDecision(
        link=key, distance_m=d, media=OS2, transceiver="10GBASE-ER",
        rationale=[*lr_fail, explain("L1.smf_er", link=key, reason=er_reason), budget],
    )


def select_media(link: Link, splices: int = 0) -> MediaDecision:
    """Apply the assignment's L1 rules (≤100 m Cat6a, ≤400 m OM4, else OS2) honoring preferences."""
    d, key, pref = link.distance_m, link.key, link.media_preference
    if link.required_gbps > C.MAX_MODELLED_GBPS:
        raise InvalidParameterError(
            f"link {key} needs {link.required_gbps} Gb/s; only 10G transceivers are modelled",
            link=key, required_gbps=link.required_gbps,
        )

    if pref == MediaPreference.COPPER or (pref == MediaPreference.AUTO and d <= C.COPPER_MAX_M):
        if d > C.COPPER_MAX_M:
            r = explain("L1.copper_violation", link=key, distance_m=d)
            raise PhysicalDistanceViolationError(r.text, link=key, distance_m=d, limit_m=C.COPPER_MAX_M)
        return MediaDecision(
            link=key, distance_m=d, media=CAT6A, transceiver="10GBASE-T",
            rationale=[explain("L1.copper", link=key, distance_m=d)],
        )

    if pref == MediaPreference.MULTIMODE or (pref == MediaPreference.AUTO and d <= C.OM4_MAX_M):
        if d > C.OM4_MAX_M:
            r = explain("L1.mmf_violation", link=key, distance_m=d)
            raise PhysicalDistanceViolationError(r.text, link=key, distance_m=d, limit_m=C.OM4_MAX_M)
        reason = (
            "was explicitly requested as multimode and is within the 400 m OM4 reach"
            if pref == MediaPreference.MULTIMODE
            else "exceeds the 100 m copper limit of 10GBASE-T (IEEE 802.3an) but is within the 400 m OM4 reach"
        )
        ok, total, budget = optical_budget(key, "10GBASE-SR", d, splices=splices)
        if not ok:
            r = explain("L1.budget_violation", link=key, total_loss_db=_r(total),
                        allowed_db=C.CHANNEL_LOSS_DB["10GBASE-SR"])
            raise PhysicalDistanceViolationError(r.text, link=key, distance_m=d, total_loss_db=_r(total))
        return MediaDecision(
            link=key, distance_m=d, media=OM4, transceiver="10GBASE-SR",
            rationale=[explain("L1.mmf", link=key, distance_m=d, reason=reason), budget],
        )

    why = (
        "was explicitly requested as single-mode"
        if pref == MediaPreference.SINGLEMODE
        else "exceeds the 400 m attenuation/dispersion limit of OM4 multimode fiber"
    )
    return _smf(link, why, splices)


def check_latency(link: Link) -> Rationale | None:
    """One-way propagation delay vs the link's latency budget (None when no budget is set)."""
    if link.max_latency_ms is None:
        return None
    km = link.distance_m / 1000
    prop_ms = round(km * C.FIBER_US_PER_KM / 1000, 3)
    args = dict(link=link.key, km=_r(km), us_per_km=C.FIBER_US_PER_KM, prop_ms=prop_ms, budget_ms=link.max_latency_ms)
    if prop_ms > link.max_latency_ms:
        r = explain("L1.latency_violation", **args)
        raise PhysicalDistanceViolationError(r.text, link=link.key, prop_ms=prop_ms, budget_ms=link.max_latency_ms)
    return explain("L1.latency", headroom_ms=round(link.max_latency_ms - prop_ms, 3), **args)
