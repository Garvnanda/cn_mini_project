"""Phase 8.3: segment policies -> extended ACLs, applied inbound on the source gateway."""

from collections import defaultdict

from engine.models import Acl, AclEntry, DesignInput, Device, Subnet
from engine.rationale import RationaleLog
from engine.topology import hostname


def build_acls(inp: DesignInput, devices: list[Device], subnets: list[Subnet], log: RationaleLog) -> None:
    sub = {s.name: s for s in subnets}
    by_src = defaultdict(list)
    for p in inp.policies:
        by_src[p.src].append(p)
    for src, pols in by_src.items():
        name = "ACL-" + hostname(src) + "-IN"
        s = sub[src]
        entries = []
        for p in pols:
            d = sub[p.dst]
            entries.append(AclEntry(
                action="permit" if p.action.value == "allow" else "deny", proto=p.proto,
                src=s.network, src_wc=s.wildcard, dst=d.network, dst_wc=d.wildcard, port=p.port,
            ))
            log.add("ACL.policy", src=src, dst=p.dst, action=entries[-1].action, proto=p.proto,
                    port=f" port {p.port}" if p.port else "", acl=name)
        entries.append(AclEntry(action="permit", proto="ip", src="any", src_wc="", dst="any", dst_wc=""))
        log.add("ACL.default", acl=name, src=src)
        acl = Acl(name=name, entries=entries)
        for dev in devices:
            hits = [i for i in dev.interfaces if i.segment == src]
            for i in hits:
                i.acl_in = name
            if hits:
                dev.acls.append(acl)
