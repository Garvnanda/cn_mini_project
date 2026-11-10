"""Domain models: design input (validated) and design output."""

from enum import Enum
from ipaddress import IPv4Network
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from engine.errors import InvalidParameterError, InvalidPrefixError

# ---------------------------------------------------------------- enums


class Profile(str, Enum):
    CAMPUS_LAN = "campus_lan"
    METRO_MAN = "metro_man"
    GLOBAL_WAN = "global_wan"
    CUSTOM = "custom"


class SiteKind(str, Enum):
    CAMPUS = "campus"
    HQ = "hq"
    BRANCH = "branch"
    DATACENTER = "datacenter"
    CLOUD = "cloud"


class SegmentRole(str, Enum):
    USER = "user"
    VOICE = "voice"
    GUEST = "guest"
    SERVER = "server"
    MGMT = "mgmt"
    IOT = "iot"


class MediaPreference(str, Enum):
    AUTO = "auto"
    COPPER = "copper"
    MULTIMODE = "multimode"
    SINGLEMODE = "singlemode"


class Resiliency(str, Enum):
    STANDARD = "standard"
    HIGH = "high"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class Transport(str, Enum):
    FIBER = "fiber"        # owned/dark fiber: L1 media engine designs the cable
    CARRIER = "carrier"    # provider L2/L3 service (EVPL, MPLS): provider owns L1
    INTERNET = "internet"  # public internet: carried inside an IPsec tunnel


# ---------------------------------------------------------------- input


class _Input(BaseModel):
    # Reject unknown keys: catches typos and junk fields from NL/LLM extraction.
    model_config = ConfigDict(extra="forbid")


class Site(_Input):
    name: str = Field(min_length=1)
    kind: SiteKind


class Building(_Input):
    name: str = Field(min_length=1)
    site: str


class Link(_Input):
    a: str
    b: str
    distance_m: float = Field(gt=0)
    required_gbps: float = Field(default=10, gt=0)
    media_preference: MediaPreference = MediaPreference.AUTO
    transport: Transport = Transport.FIBER

    @model_validator(mode="after")
    def _distinct_ends(self) -> "Link":
        if self.a == self.b:
            raise ValueError(f"link endpoints must differ (got '{self.a}' twice)")
        return self

    @property
    def key(self) -> str:
        return f"{self.a}--{self.b}"


class Segment(_Input):
    name: str = Field(min_length=1)
    vlan: int = Field(ge=2, le=4094)  # 1 = default VLAN, never used for data; 0/4095 reserved (802.1Q)
    hosts: int = Field(ge=1)
    role: SegmentRole
    location: str  # site or building name
    poe: bool = False


class Policy(_Input):
    src: str
    dst: str
    action: PolicyAction
    proto: Literal["ip", "tcp", "udp", "icmp"] = "ip"
    port: int | None = Field(default=None, ge=1, le=65535)

    @model_validator(mode="after")
    def _check(self) -> "Policy":
        if self.src == self.dst:
            raise ValueError(f"policy src and dst are the same segment '{self.src}'")
        if self.port is not None and self.proto not in ("tcp", "udp"):
            raise ValueError(f"port given but proto is '{self.proto}'; ports need tcp or udp")
        return self


class DesignInput(_Input):
    profile: Profile
    root_prefix: str
    sites: list[Site] = Field(min_length=1)
    buildings: list[Building] = []
    links: list[Link] = []
    segments: list[Segment] = Field(min_length=1)
    resiliency: Resiliency = Resiliency.STANDARD
    policies: list[Policy] = []

    @field_validator("root_prefix")
    @classmethod
    def _valid_root(cls, v: str) -> str:
        try:
            net = IPv4Network(v, strict=True)
        except ValueError as e:
            raise ValueError(f"root_prefix '{v}' is not a valid IPv4 network: {e}") from None
        if "/" not in v:
            raise ValueError(f"root_prefix '{v}' must include a prefix length, e.g. 10.0.0.0/16")
        return str(net)

    @model_validator(mode="after")
    def _cross_refs(self) -> "DesignInput":
        site_names = _unique([s.name for s in self.sites], "site name")
        bldg_names = _unique([b.name for b in self.buildings], "building name")
        if clash := site_names & bldg_names:
            raise ValueError(f"names used for both a site and a building: {sorted(clash)}")
        for b in self.buildings:
            if b.site not in site_names:
                raise ValueError(f"building '{b.name}' references unknown site '{b.site}'")
        places = site_names | bldg_names
        for ln in self.links:
            for end in (ln.a, ln.b):
                if end not in places:
                    raise ValueError(f"link {ln.key} references unknown site/building '{end}'")
        seg_names = _unique([s.name for s in self.segments], "segment name")
        _unique([s.vlan for s in self.segments], "VLAN id")
        for s in self.segments:
            if s.location not in places:
                raise ValueError(f"segment '{s.name}' references unknown location '{s.location}'")
        for p in self.policies:
            for ref in (p.src, p.dst):
                if ref not in seg_names:
                    raise ValueError(f"policy {p.src}->{p.dst} references unknown segment '{ref}'")
        return self


def _unique(items: list, what: str) -> set:
    seen, dupes = set(), set()
    for i in items:
        (dupes if i in seen else seen).add(i)
    if dupes:
        raise ValueError(f"duplicate {what}: {sorted(dupes, key=str)}")
    return seen


def parse_design_input(data: dict[str, Any]) -> DesignInput:
    """Validate raw input; convert Pydantic errors into typed NetArch errors."""
    try:
        return DesignInput.model_validate(data)
    except ValidationError as e:
        errors = [
            {"loc": ".".join(map(str, err["loc"])), "msg": err["msg"]} for err in e.errors()
        ]
        if any(err["loc"] == "root_prefix" for err in errors):
            raise InvalidPrefixError("invalid root prefix", errors=errors) from None
        raise InvalidParameterError(
            f"{len(errors)} invalid parameter(s): " + "; ".join(f"{x['loc']}: {x['msg']}" for x in errors),
            errors=errors,
        ) from None


# ---------------------------------------------------------------- output


class Rationale(BaseModel):
    rule_id: str
    domain: str  # e.g. "L1", "VLSM", "L2", "ROUTE", "TOPO", "ACL"
    inputs: dict[str, Any] = {}
    threshold: str | None = None
    standard_ref: str
    text: str


class MediaDecision(BaseModel):
    link: str
    distance_m: float
    media: str
    transceiver: str
    rationale: list[Rationale]


class Subnet(BaseModel):
    name: str
    vlan: int | None
    requested_hosts: int
    network: str
    prefix: int
    mask: str
    wildcard: str
    gateway: str | None
    broadcast: str | None  # None for /31, /32 and container blocks
    first_usable: str
    last_usable: str
    usable_hosts: int
    utilization_pct: float
    unit: str | None = None  # addressing unit (OSPF area / cloud) it was carved from


class RoutingDecision(BaseModel):
    protocol: str
    areas: dict[str, int] = {}   # unit name -> OSPF area
    asn: dict[str, int] = {}     # hostname -> BGP ASN
    rationale: list[Rationale]


class Interface(BaseModel):
    name: str
    mode: str  # access | trunk | routed | underlay | svi | loopback | tunnel | unused
    description: str = ""
    range: bool = False          # rendered as `interface range <name>`
    vlan: int | None = None
    allowed_vlans: list[int] = []
    native_vlan: int | None = None
    ip: str | None = None
    mask: str | None = None
    peer: str | None = None      # "HOST IFNAME"
    segment: str | None = None   # LAN segment this L3 interface is gateway for
    hsrp_group: int | None = None
    hsrp_vip: str | None = None
    hsrp_priority: int | None = None
    area: int | None = None      # OSPF area; None = not in OSPF
    acl_in: str | None = None
    tunnel_source: str | None = None
    tunnel_destination: str | None = None
    media: str | None = None
    transceiver: str | None = None


class OspfConfig(BaseModel):
    pid: int
    router_id: str
    ref_bw: int
    networks: list[tuple[str, str, int]] = []   # (ip, wildcard, area)
    passive: list[str] = []
    summaries: list[tuple[int, str, str]] = []  # (area, network, mask)
    redistribute_bgp: int | None = None


class BgpConfig(BaseModel):
    asn: int
    router_id: str
    neighbors: list[tuple[str, int]] = []       # (ip, remote-as)
    networks: list[tuple[str, str]] = []        # (network, mask)


class AclEntry(BaseModel):
    action: str  # permit | deny
    proto: str
    src: str
    src_wc: str
    dst: str
    dst_wc: str
    port: int | None = None


class Acl(BaseModel):
    name: str
    entries: list[AclEntry]


class StaticRoute(BaseModel):
    network: str
    mask: str
    next_hop: str  # IP or interface (e.g. Null0)
    distance: int | None = None  # AD override (floating static)


class Device(BaseModel):
    hostname: str
    role: str  # core | distribution | access | router | cloud
    site: str
    location: str
    l3: bool = False
    members: int = 1  # stack members (access switches)
    interfaces: list[Interface] = []
    vlans: dict[int, str] = {}
    stp_primary: list[int] = []
    stp_secondary: list[int] = []
    ospf: OspfConfig | None = None
    bgp: BgpConfig | None = None
    acls: list[Acl] = []
    static_routes: list[StaticRoute] = []
    ipsec_peers: list[str] = []
    poe_watts: float = 0

    def iface(self, name: str) -> Interface:
        return next(i for i in self.interfaces if i.name == name)


class Cable(BaseModel):
    a: str
    a_if: str
    b: str
    b_if: str
    kind: str  # trunk | routed | underlay
    link: str | None = None  # input Link.key; None = in-building patch
    media: str = ""
    transceiver: str = ""


class DesignResult(BaseModel):
    input: DesignInput
    media: list[MediaDecision] = []
    subnets: list[Subnet] = []
    routing: RoutingDecision | None = None
    devices: list[Device] = []
    cables: list[Cable] = []
    tiers: dict[str, str] = {}
    rationale: list[Rationale] = []

    def device(self, hostname: str) -> Device:
        return next(d for d in self.devices if d.hostname == hostname)
