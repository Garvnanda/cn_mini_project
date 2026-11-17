# Live Batfish cross-check, 2026-11-18

Docker Desktop was started and the existing batfish/allinone image was run as
`netarchitect-batfish`, bound only to 127.0.0.1:9996. Image ID:
`sha256:54cb0ed94fd9a3c1ca0985f73e5be479e955cee9b9f6a6799b66be3364fd8e5c`.

Campus: 90 flows, zero disagreements. Metro: 21 flows, zero disagreements.
Global WAN: 21 flows, 14 disagreements. JSON files contain the actual comparisons.
These are static analyses, not actual device packet captures.

The WAN diagnostics report IPSEC_PHASE2_FAILED for the four directed tunnel
sessions. Parser warnings occur around the IKE hash/authentication policy and
placeholder enable secrets. The current Batfish Cisco grammar accepts MD5, SHA
and SHA2_256_128 in `cispol_hash`, rather than the generated `hash sha256`.
Cisco documents `hash sha256` in an IOS XE VTI example. This is evidence of a
parser coverage mismatch; it does not establish that every WAN disagreement is
only a parser problem or that real tunnels work. Do not downgrade cryptography
or relabel failed comparisons as agreement to obtain a green report.

Sources inspected:
- https://raw.githubusercontent.com/batfish/batfish/master/projects/batfish/src/main/antlr4/org/batfish/grammar/cisco/Cisco_crypto.g4
- https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/214728-configure-multi-sa-virtual-tunnel-interf.html

Reproduce from backend (PowerShell):
```powershell
$env:BATFISH_HOST='localhost'
.\.venv\Scripts\python.exe cli.py crosscheck campus_lan
.\.venv\Scripts\python.exe cli.py crosscheck metro_man
.\.venv\Scripts\python.exe cli.py crosscheck global_wan
```
The crosscheck command returns a nonzero exit code for disagreements or errors.
The report preserves parse warnings and IPsec session status for diagnosis.
