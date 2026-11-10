"""Phase 8: render Cisco IOS configs per device from Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from engine import constants as C
from engine.models import DesignResult, Device
from engine.topology import hostname

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE_BY_ROLE = {
    "access": "access_switch.j2",
    "core": "core_switch.j2",
    "distribution": "core_switch.j2",
    "router": "router.j2",
    "cloud": "router.j2",
}
IPSEC_PROFILE = "VTI-PROFILE"
DOMAIN = "netarch.local"

_env = Environment(
    loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True,
    undefined=StrictUndefined, keep_trailing_newline=True,
)
_env.filters["ios_name"] = hostname  # VLAN names: no spaces, IOS-safe


def render_device(d: Device) -> str:
    return _env.get_template(TEMPLATE_BY_ROLE[d.role]).render(
        d=d, domain=DOMAIN, ipsec_profile=IPSEC_PROFILE, psk=C.IPSEC_PSK,
        is_switch=d.role in ("access", "core", "distribution"),
    )


def render_all(result: DesignResult) -> dict[str, str]:
    return {d.hostname: render_device(d) for d in result.devices}


def export(result: DesignResult, out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for host, text in render_all(result).items():
        p = out / f"{host}.cfg"
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    return paths
