"""Phase 6: VLAN plan, pruned 802.1Q trunks, native VLAN, RSTP roots, SVIs + HSRP."""

from engine import constants as C
from engine.models import DesignInput, Interface
from engine.rationale import RationaleLog
from engine.topology import Topology


def pick_native(used: set[int]) -> int:
    """Dedicated unused VLAN for trunk native / parking: 999 unless taken, else highest free."""
    if C.NATIVE_VLAN_DEFAULT not in used:
        return C.NATIVE_VLAN_DEFAULT
    return next(v for v in range(4094, 1, -1) if v not in used)


def apply_l2(t: Topology, inp: DesignInput, log: RationaleLog) -> int:
    seg_name = {s.vlan: s.name for s in inp.segments}
    native = pick_native(set(seg_name))
    if t.blocks:
        log.add("L2.native", native=native)
        log.add("L2.edge_ports")

    for blk in t.blocks:
        block_vlans = {v: seg_name[v] for v in blk.vlans}
        log.add("L2.vlan_plan", block=blk.name, vlans=_fmt(blk.vlans))
        members = [*blk.gateways, *blk.access]
        for h in members:
            dev = t.devices[h]
            if dev.role != "access":
                dev.vlans = dict(block_vlans)
            dev.vlans[native] = "BLACKHOLE"
            for i in dev.interfaces:
                if i.mode == "unused":
                    i.vlan = native
                if i.mode != "trunk":
                    continue
                peer = t.devices[i.peer.split()[0]]
                if dev.role == "access":
                    allowed = _data(dev.vlans, native)
                elif peer.role == "access":
                    allowed = _data(peer.vlans, native)
                else:
                    allowed = blk.vlans
                i.allowed_vlans, i.native_vlan = list(allowed), native
                if dev.role == "access":
                    log.add("L2.trunk_prune", device=h, peer=peer.hostname, vlans=_fmt(allowed))

        gws = blk.gateways
        t.devices[gws[0]].stp_primary = list(blk.vlans)
        if len(gws) == 2:
            t.devices[gws[1]].stp_secondary = list(blk.vlans)
        log.add("L2.stp_root", block=blk.name, primary=gws[0],
                secondary=f" and secondary on {gws[1]}" if len(gws) == 2 else "")
        for n, gw in enumerate(gws):
            for v in blk.vlans:
                svi = Interface(name=f"Vlan{v}", mode="svi", vlan=v, segment=seg_name[v],
                                description=f"Gateway {seg_name[v]}")
                if len(gws) == 2:
                    svi.hsrp_group = v
                    svi.hsrp_priority = C.HSRP_ACTIVE_PRIORITY if n == 0 else C.HSRP_STANDBY_PRIORITY
                t.devices[gw].interfaces.append(svi)
        if len(gws) == 2:
            log.add("L2.hsrp", block=blk.name, gw1=gws[0], gw2=gws[1],
                    p1=C.HSRP_ACTIVE_PRIORITY, p2=C.HSRP_STANDBY_PRIORITY)
    return native


def _data(vlans: dict[int, str], native: int) -> list[int]:
    return sorted(v for v in vlans if v != native)


def _fmt(vlans) -> str:
    return ",".join(map(str, vlans))
