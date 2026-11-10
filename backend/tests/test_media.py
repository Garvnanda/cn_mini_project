import pytest

from engine import constants as C
from engine.errors import InvalidParameterError, PhysicalDistanceViolationError
from engine.media import CAT6A, OM4, OS2, optical_budget, select_media
from engine.models import Link


def link(d, pref="auto", gbps=10):
    return Link(a="A", b="B", distance_m=d, media_preference=pref, required_gbps=gbps)


@pytest.mark.parametrize(
    "d, media, xcvr",
    [
        (1, CAT6A, "10GBASE-T"),
        (100, CAT6A, "10GBASE-T"),
        (101, OM4, "10GBASE-SR"),
        (400, OM4, "10GBASE-SR"),
        (401, OS2, "10GBASE-LR"),
        (5_000, OS2, "10GBASE-LR"),
        (10_001, OS2, "10GBASE-ER"),
        (22_000, OS2, "10GBASE-ER"),
        (35_000, OS2, "10GBASE-ER"),
    ],
)
def test_auto_thresholds(d, media, xcvr):
    m = select_media(link(d))
    assert (m.media, m.transceiver) == (media, xcvr)
    assert m.rationale and all(r.standard_ref for r in m.rationale)


def test_spec_example_wording():
    text = " ".join(r.text for r in select_media(link(22_000)).rationale)
    assert "OS2" in text and "10 km" in text


def test_copper_101m_raises():
    with pytest.raises(PhysicalDistanceViolationError, match="100 m") as ei:
        select_media(link(101, "copper"))
    assert ei.value.details["limit_m"] == 100
    assert "attenuation" in ei.value.message


def test_copper_150m_raises():
    with pytest.raises(PhysicalDistanceViolationError):
        select_media(link(150, "copper"))


def test_copper_100m_ok():
    assert select_media(link(100, "copper")).media == CAT6A


def test_multimode_preference():
    assert select_media(link(50, "multimode")).media == OM4
    with pytest.raises(PhysicalDistanceViolationError, match="400 m"):
        select_media(link(401, "multimode"))


def test_singlemode_preference_short_link():
    m = select_media(link(50, "singlemode"))
    assert (m.media, m.transceiver) == (OS2, "10GBASE-LR")


def test_40km_fails_budget_with_tia_max_connectors():
    # 40 km x 0.25 dB/km + 2 x 0.75 dB = 11.5 dB > 11.0 dB ER channel loss (UNVERIFIED constants)
    with pytest.raises(PhysicalDistanceViolationError, match="loss"):
        select_media(link(40_000))


def test_38km_is_er_at_zero_margin():
    assert select_media(link(38_000)).transceiver == "10GBASE-ER"


@pytest.mark.parametrize("d", [40_001, 80_000])
def test_beyond_er(d):
    with pytest.raises(PhysicalDistanceViolationError, match="40 km"):
        select_media(link(d))


def test_lr_budget_fail_upgrades_to_er():
    m = select_media(link(10_000), splices=4)
    assert m.transceiver == "10GBASE-ER"
    assert any("budget fails" in r.text for r in m.rationale)


def test_er_budget_fail_raises():
    with pytest.raises(PhysicalDistanceViolationError, match="loss"):
        select_media(link(39_000), splices=10)


def test_budget_math():
    ok, loss, r = optical_budget("A--B", "10GBASE-LR", 5_000)
    assert ok
    assert loss == pytest.approx(5 * C.OS2_1310_DB_PER_KM + 2 * C.CONNECTOR_DB)
    assert r.inputs["margin_db"] == round(C.CHANNEL_LOSS_DB["10GBASE-LR"] - loss, 2)


def test_budget_fail():
    ok, _, r = optical_budget("A--B", "10GBASE-LR", 10_000, connectors=6)
    assert not ok and "FAIL" in r.text


def test_low_margin_warning():
    _, _, r = optical_budget("A--B", "10GBASE-LR", 9_000)
    assert "design margin" in r.text


def test_over_10g_rejected():
    with pytest.raises(InvalidParameterError, match="10G"):
        select_media(link(50, gbps=40))


def test_latency_budget_ok():
    from engine.media import check_latency
    r = check_latency(Link(a="A", b="B", distance_m=35_000, max_latency_ms=5))
    assert r.inputs["prop_ms"] == 0.175 and r.inputs["headroom_ms"] == 4.825


def test_latency_budget_violation():
    from engine.media import check_latency
    with pytest.raises(PhysicalDistanceViolationError, match="propagation"):
        check_latency(Link(a="A", b="B", distance_m=1_150_000, max_latency_ms=5))  # 5.75 ms


def test_latency_boundary():
    from engine.media import check_latency
    assert check_latency(Link(a="A", b="B", distance_m=1_000_000, max_latency_ms=5))  # exactly 5 ms
    assert check_latency(Link(a="A", b="B", distance_m=10)) is None
