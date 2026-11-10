"""Phase 15: security posture linter for IOS configs (generated or pasted)."""

from pydantic import BaseModel

from verify.ios_parser import PDevice, parse_config

WEIGHT = {"high": 15, "medium": 8, "low": 3, "info": 0}

# rule id -> (severity, title, fix)
RULES: dict[str, tuple[str, str, str]] = {
    "SEC-01": ("high", "Trunk allows all VLANs", "switchport trunk allowed vlan <only the VLANs needed>"),
    "SEC-02": ("medium", "Trunk native VLAN is VLAN 1", "switchport trunk native vlan <unused VLAN>"),
    "SEC-03": ("medium", "Access port without BPDU Guard", "spanning-tree bpduguard enable"),
    "SEC-04": ("low", "Access port without PortFast", "spanning-tree portfast"),
    "SEC-05": ("medium", "Port in default VLAN 1 left enabled", "shutdown, or assign a real VLAN"),
    "SEC-06": ("high", "VTY lines accept telnet (or transport not restricted)", "transport input ssh"),
    "SEC-07": ("low", "Passwords not encrypted in config", "service password-encryption"),
    "SEC-08": ("medium", "SSH version 2 not enforced", "ip ssh version 2"),
    "SEC-09": ("medium", "OSPF runs without authentication", "area <n> authentication message-digest + keys"),
    "SEC-10": ("high", "No enable secret (or plaintext enable password)", "enable secret <secret>"),
    "SEC-11": ("medium", "Placeholder secrets (CHANGE_ME) present", "replace every CHANGE_ME value"),
    "SEC-12": ("info", "ACL ends with 'permit ip any any'", "intended for default-allow policies (D-020)"),
    "SEC-13": ("high", "VTY lines without local login", "login local"),
}


class Finding(BaseModel):
    rule: str
    severity: str
    title: str
    where: str
    fix: str


class DeviceLint(BaseModel):
    hostname: str
    score: int
    findings: list[Finding]


class LintReport(BaseModel):
    score: int
    devices: list[DeviceLint]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.devices:
            for f in d.findings:
                out[f.severity] = out.get(f.severity, 0) + 1
        return out


def lint_device(d: PDevice) -> DeviceLint:
    found: list[Finding] = []

    def add(rule: str, where: str) -> None:
        sev, title, fix = RULES[rule]
        found.append(Finding(rule=rule, severity=sev, title=title, where=where, fix=fix))

    is_switch = d.is_switch
    for i in d.interfaces.values():
        if i.mode == "trunk":
            if i.allowed_vlans is None:
                add("SEC-01", i.name)
            if i.native_vlan in (None, 1):
                add("SEC-02", i.name)
        elif i.mode == "access" and not i.shutdown:
            if not i.bpduguard:
                add("SEC-03", i.name)
            if not i.portfast:
                add("SEC-04", i.name)
            if i.access_vlan in (None, 1):
                add("SEC-05", i.name)
        elif is_switch and i.mode is None and i.switchport is None and not i.ip and not i.shutdown \
                and not i.name.lower().startswith(("vlan", "loopback", "tunnel")):
            add("SEC-05", i.name)  # switch port with no config = dynamic port in VLAN 1
    if d.vty_transport is None or any(x in ("telnet", "all") for x in d.vty_transport):
        add("SEC-06", "line vty")
    if not d.vty_login_local and not d.vty_password:
        add("SEC-13", "line vty")
    if "password-encryption" not in d.services:
        add("SEC-07", "global")
    if not d.ssh_v2:
        add("SEC-08", "global")
    if d.ospf and not d.ospf.area_auth and not any(i.ospf_auth for i in d.interfaces.values()):
        add("SEC-09", f"router ospf {d.ospf.pid}")
    if not d.enable_secret or d.enable_password:
        add("SEC-10", "global")
    if d.placeholder_secrets:
        add("SEC-11", "global")
    for name, entries in d.acls.items():
        if entries and entries[-1].action == "permit" and entries[-1].proto == "ip" \
                and entries[-1].src == "any" and entries[-1].dst == "any":
            add("SEC-12", f"ip access-list {name}")
    penalty = sum(WEIGHT[RULES[r][0]] for r in {f.rule for f in found})  # each rule counts once per device
    return DeviceLint(hostname=d.hostname or "unnamed", score=max(0, 100 - penalty), findings=found)


def lint_configs(configs: dict[str, str]) -> LintReport:
    devs = [lint_device(parse_config(text, strict=False)) for text in configs.values()]
    score = round(sum(d.score for d in devs) / len(devs)) if devs else 100
    return LintReport(score=score, devices=devs)


def lint_text(text: str) -> DeviceLint:
    """Lint one pasted config."""
    return lint_device(parse_config(text, strict=False))
