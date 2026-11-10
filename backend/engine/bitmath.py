"""Integer bitwise IPv4 math. No `ipaddress` here (D-007): it is the test oracle only."""

from engine.constants import ALL_ONES, IPV4_BITS
from engine.errors import InvalidPrefixError


def ip_to_int(ip: str) -> int:
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        raise InvalidPrefixError(f"invalid IPv4 address '{ip}'", ip=ip)
    a, b, c, d = map(int, parts)
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(n: int) -> str:
    return f"{(n >> 24) & 255}.{(n >> 16) & 255}.{(n >> 8) & 255}.{n & 255}"


def _check_prefix(p: int) -> None:
    if not 0 <= p <= IPV4_BITS:
        raise InvalidPrefixError(f"prefix length /{p} out of range 0-32", prefix=p)


def prefix_to_mask(p: int) -> int:
    _check_prefix(p)
    return (ALL_ONES << (IPV4_BITS - p)) & ALL_ONES


def mask_to_prefix(mask: int) -> int:
    inv = ~mask & ALL_ONES
    if inv & (inv + 1):  # host part must be contiguous ones
        raise InvalidPrefixError(f"non-contiguous mask {int_to_ip(mask)}", mask=int_to_ip(mask))
    return IPV4_BITS - inv.bit_length()


def wildcard(p: int) -> int:
    return ~prefix_to_mask(p) & ALL_ONES


def block_size(p: int) -> int:
    _check_prefix(p)
    return 1 << (IPV4_BITS - p)


def network(ip: int, p: int) -> int:
    return ip & prefix_to_mask(p)


def broadcast(ip: int, p: int) -> int:
    return network(ip, p) | wildcard(p)


def is_aligned(ip: int, p: int) -> bool:
    return ip & wildcard(p) == 0


def parse_cidr(cidr: str) -> tuple[int, int]:
    """'10.0.0.0/16' -> (int, 16). Rejects host bits set."""
    if cidr.count("/") != 1:
        raise InvalidPrefixError(f"'{cidr}' is not CIDR notation", cidr=cidr)
    ip_s, p_s = cidr.split("/")
    if not p_s.isdigit():
        raise InvalidPrefixError(f"invalid prefix length in '{cidr}'", cidr=cidr)
    ip, p = ip_to_int(ip_s), int(p_s)
    _check_prefix(p)
    if not is_aligned(ip, p):
        raise InvalidPrefixError(
            f"'{cidr}' has host bits set (network is {int_to_ip(network(ip, p))}/{p})", cidr=cidr
        )
    return ip, p


def usable_hosts(p: int) -> int:
    """Usable addresses: /31 = 2 (RFC 3021), /32 = 1, else 2^(32-p) - 2."""
    _check_prefix(p)
    if p == 32:
        return 1
    if p == 31:
        return 2
    return block_size(p) - 2


def hosts_to_prefix(hosts: int, gateway: bool = True) -> int:
    """Smallest prefix (≤ /30) whose usable count holds `hosts` (+1 gateway when gateway=True)."""
    if hosts < 1:
        raise ValueError("hosts must be ≥ 1")
    need_total = hosts + (1 if gateway else 0) + 2  # + network + broadcast
    block = 1 << (need_total - 1).bit_length()       # smallest power of two ≥ need_total
    return IPV4_BITS - block.bit_length() + 1
