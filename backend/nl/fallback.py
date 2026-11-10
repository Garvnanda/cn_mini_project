"""Offline keyword/regex parser: natural language -> partial DesignInput dict.

It only copies facts that appear in the text. Anything missing is reported in `missing`
(the user fills it in the confirm step); it never invents distances or host counts.
"""

import re

CLOUD_WORDS = ("cloud", "vpc", "aws", "azure", "gcp")
SITE_WORDS = r"(?:branch(?:es)?|remote(?: sites?)?|remotes|offices|sites|cities)"


def _int(s: str) -> int:
    return int(s.replace(",", ""))


def _distances_m(text: str) -> list[float]:
    out = []
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(km|kilomet(?:er|re)s?|m|meters?|metres?)\b", text):
        v = float(num)
        out.append(v * 1000 if unit.startswith("k") else v)
    return out


def parse(text: str) -> tuple[dict, list[str], list[str]]:
    """Return (input dict, assumptions, missing facts)."""
    t = text.lower()
    assumptions: list[str] = []
    missing: list[str] = []

    users = sum(_int(n) for n, _ in re.findall(r"(\d[\d,]*)\s*(users|endpoints|hosts|employees|staff|people)", t))
    iot = sum(_int(n) for n in re.findall(r"(\d[\d,]*)\s*(?:iot|sensors|scanners|devices)", t))
    buildings = re.search(r"(\d+)[\s-]*buildings?", t)
    sites_n = re.search(rf"(\d+)[\s-]*{SITE_WORDS}", t)
    cloud = any(w in t for w in CLOUD_WORDS)
    dists = _distances_m(t)
    latency = re.search(r"(\d+(?:\.\d+)?)\s*ms\b", t)
    poe = bool(re.search(r"\bpoe\b|access points?|\baps?\b|ip phones?", t))
    guest = "guest" in t
    redundant = bool(re.search(r"redundan|dual[- ]homed|failover|high[- ]availability|resilien", t))
    internet = bool(re.search(r"ipsec|internet|vpn", t))

    if cloud or (sites_n and int(sites_n.group(1)) >= 3 and "cit" in t):
        profile = "global_wan"
    elif sites_n or re.search(r"\bhq\b|headquarters|branch|metro", t) or any(d > 400 for d in dists):
        profile = "metro_man"
    elif buildings or "campus" in t:
        profile = "campus_lan"
    else:
        profile = "custom"

    d: dict = {"profile": profile, "root_prefix": "10.0.0.0/16", "sites": [], "buildings": [],
               "links": [], "segments": [], "policies": []}
    assumptions.append("root_prefix 10.0.0.0/16 (RFC 1918 private space) assumed; change it if you have a plan")
    if redundant:
        d["resiliency"] = "high"
    hosts = users or iot
    role = "iot" if iot and not users else "user"
    if not hosts:
        missing.append("number of users / endpoints")

    def seg(name: str, vlan: int, n: int, loc: str, r: str = role, **kw) -> None:
        if n > 0:
            d["segments"].append({"name": name, "vlan": vlan, "hosts": n, "role": r, "location": loc, **kw})

    if profile == "campus_lan" or (profile == "custom" and buildings):
        n = int(buildings.group(1)) if buildings else 1
        d["sites"].append({"name": "Campus", "kind": "campus"})
        names = [f"Bldg{i}" for i in range(1, n + 1)]
        d["buildings"] = [{"name": b, "site": "Campus"} for b in names]
        for i, b in enumerate(names[1:]):
            if i < len(dists):
                d["links"].append({"a": names[0], "b": b, "distance_m": dists[i]})
            else:
                missing.append(f"distance from {names[0]} to {b}")
        for i, b in enumerate(names):
            seg(f"Users-{b}", 10 + i, hosts // n + (1 if i < hosts % n else 0), b)
        if n > 1 and hosts:
            assumptions.append(f"{hosts} endpoints split evenly across {n} buildings")
    elif profile == "custom":
        d["sites"].append({"name": "Office", "kind": "campus"})
        seg("Users", 10, hosts, "Office")
    else:
        remotes = int(sites_n.group(1)) if sites_n else 0
        cities = profile == "global_wan" and "cit" in t
        if cities:
            remotes -= 1  # "4 cities" = HQ + 3 others
        names = ["HQ"] + [f"Site{i}" for i in range(1, max(remotes, 0) + 1)]
        d["sites"] = [{"name": names[0], "kind": "hq"}] + [{"name": s, "kind": "branch"} for s in names[1:]]
        for i, s in enumerate(names[1:]):
            link = {"a": "HQ", "b": s, "distance_m": dists[i]} if i < len(dists) else None
            if link is None:
                missing.append(f"distance from HQ to {s}")
                continue
            if profile == "global_wan" or link["distance_m"] > 40_000:
                link["transport"] = "internet" if internet else "carrier"
                assumptions.append(f"HQ--{s} uses a {link['transport']} service (long-haul)")
            if latency:
                link["max_latency_ms"] = float(latency.group(1))
            d["links"].append(link)
        for i, s in enumerate(names):
            seg(f"{s}-Users", 10 * (i + 1), hosts // len(names) + (1 if i < hosts % len(names) else 0), s)
        if hosts and len(names) > 1:
            assumptions.append(f"{hosts} endpoints split evenly across {len(names)} sites")
        if cloud:
            d["sites"].append({"name": "CloudVPC", "kind": "cloud"})
            d["links"].append({"a": "HQ", "b": "CloudVPC", "distance_m": 1000, "transport": "internet"})
            assumptions.append("cloud VPC reached from HQ over an internet IPsec tunnel (distance not used)")
            missing.append("number of hosts in the cloud VPC")

    if poe:
        missing.append("number of PoE devices (access points / phones)")
    if guest:
        missing.append("number of guest devices (a guest segment + deny policy can then be added)")
    if not d["policies"]:
        del d["policies"]
    if not d["buildings"]:
        del d["buildings"]
    return d, assumptions, missing
