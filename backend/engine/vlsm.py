"""Bitwise VLSM allocator: largest-first, aligned, non-overlapping."""

from dataclasses import dataclass
from typing import Literal

from engine import bitmath as B
from engine.errors import AddressSpaceExhaustedError
from engine.models import Rationale, Subnet
from engine.rationale import explain

Kind = Literal["lan", "p2p", "loopback", "block"]


@dataclass(frozen=True)
class AllocRequest:
    name: str
    hosts: int = 1
    kind: Kind = "lan"
    vlan: int | None = None

    @property
    def prefix(self) -> int:
        if self.kind == "p2p":
            return 31  # RFC 3021
        if self.kind == "loopback":
            return 32
        if self.kind == "block":  # container of exactly `hosts` addresses (a power of two)
            if self.hosts & (self.hosts - 1):
                raise ValueError(f"block size {self.hosts} is not a power of two")
            return 32 - (self.hosts.bit_length() - 1)
        return B.hosts_to_prefix(self.hosts, gateway=True)

    @property
    def needed(self) -> int:
        """Addresses actually used: hosts + gateway for LANs; 2 for p2p; 1 for loopback."""
        if self.kind == "block":
            return self.hosts
        return {"p2p": 2, "loopback": 1}.get(self.kind, self.hosts + 1)


def _subnet(req: AllocRequest, net: int) -> tuple[Subnet, Rationale]:
    p = req.prefix
    usable = B.usable_hosts(p)
    util = round(req.needed / usable * 100, 2)
    if req.kind == "lan":
        first, last = net + 1, B.broadcast(net, p) - 1
        gw, bc = B.int_to_ip(first), B.int_to_ip(B.broadcast(net, p))
        r = explain("VLSM.subnet", name=req.name, hosts=req.hosts, needed=req.needed, prefix=p,
                    host_bits=32 - p, usable=usable, util=util)
    elif req.kind == "block":
        first, last = net, B.broadcast(net, p)
        gw, bc = None, None
        usable = B.block_size(p)
        util = 100.0
        r = explain("VLSM.block", name=req.name, network=B.int_to_ip(net), prefix=p, size=usable)
    else:
        first, last = net, B.broadcast(net, p)
        gw, bc = None, None
        rule = "VLSM.p2p" if req.kind == "p2p" else "VLSM.loopback"
        r = explain(rule, name=req.name)
    s = Subnet(
        name=req.name, vlan=req.vlan, requested_hosts=req.needed if req.kind != "lan" else req.hosts,
        network=B.int_to_ip(net), prefix=p, mask=B.int_to_ip(B.prefix_to_mask(p)),
        wildcard=B.int_to_ip(B.wildcard(p)), gateway=gw, broadcast=bc,
        first_usable=B.int_to_ip(first), last_usable=B.int_to_ip(last),
        usable_hosts=usable, utilization_pct=util,
    )
    return s, r


def allocate(root: str, requests: list[AllocRequest]) -> tuple[list[Subnet], list[Rationale]]:
    """Allocate every request inside `root`. Raises AddressSpaceExhaustedError if it can't fit.

    Requests are sorted by block size descending (ties by name, for determinism). Because every
    block is a power of two and sizes never grow, a single cursor stays aligned for each block.
    """
    base, root_p = B.parse_cidr(root)
    root_size = B.block_size(root_p)
    names = [r.name for r in requests]
    if len(set(names)) != len(names):
        raise ValueError("duplicate request names")

    ordered = sorted(requests, key=lambda r: (r.prefix, r.name))
    needed = sum(1 << (32 - r.prefix) for r in ordered)  # prefix may be < 0 for absurd host counts
    if needed > root_size:
        min_prefix = 32 - (needed - 1).bit_length()
        r = explain("VLSM.exhausted", root=root, available=root_size, needed=needed, min_prefix=min_prefix)
        raise AddressSpaceExhaustedError(r.text, root=root, available=root_size, needed=needed)

    subnets, rationale, cursor = [], [], base
    for req in ordered:
        assert B.is_aligned(cursor, req.prefix), f"cursor misaligned for {req.name}"
        s, r = _subnet(req, cursor)
        subnets.append(s)
        rationale.append(r)
        cursor += B.block_size(req.prefix)

    requested = sum(r.needed for r in requests)
    rationale.append(explain(
        "VLSM.efficiency", root=root, root_size=root_size, allocated=needed,
        root_util=round(needed / root_size * 100, 2), requested=requested,
        eff=round(requested / needed * 100, 2), waste=needed - requested,
    ))
    return subnets, rationale
