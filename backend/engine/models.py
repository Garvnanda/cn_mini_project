"""Domain models: design input (validated) and design output."""

from enum import Enum
from ipaddress import IPv4Network
from typing import Any

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
    proto: str = "ip"
    port: int | None = Field(default=None, ge=1, le=65535)


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
    domain: str  # e.g. "L1", "VLSM", "L2", "L3", "topology"
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
    broadcast: str | None  # None for /31 and /32
    first_usable: str
    last_usable: str
    usable_hosts: int
    utilization_pct: float


class RoutingDecision(BaseModel):
    protocol: str
    areas: dict[str, int] = {}
    asn: dict[str, int] = {}
    rationale: list[Rationale]


class Interface(BaseModel):
    name: str
    description: str = ""
    mode: str  # access | trunk | routed | svi | loopback
    vlan: int | None = None
    allowed_vlans: list[int] = []
    native_vlan: int | None = None
    ip: str | None = None
    mask: str | None = None
    peer: str | None = None


class Device(BaseModel):
    hostname: str
    role: str  # core | distribution | access | router | edge | cloud
    site: str
    interfaces: list[Interface] = []


class DesignResult(BaseModel):
    input: DesignInput
    media: list[MediaDecision] = []
    subnets: list[Subnet] = []
    routing: RoutingDecision | None = None
    devices: list[Device] = []
    rationale: list[Rationale] = []
