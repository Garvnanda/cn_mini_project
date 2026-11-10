import pytest

from analysis.lint import RULES, lint_configs, lint_text
from engine.configgen import render_all
from tests.conftest import NAMES

BAD = """hostname BADSW
enable password cisco
spanning-tree mode pvst
vlan 10
 name USERS
interface GigabitEthernet0/1
 switchport mode trunk
interface GigabitEthernet0/2
 switchport mode access
 switchport access vlan 10
interface GigabitEthernet0/3
 speed 100
interface Vlan1
 ip address 10.0.0.2 255.255.255.0
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0
line vty 0 4
 password cisco
 transport input telnet
"""

GOOD = """hostname GOODSW
service password-encryption
enable secret s3cr3t-hash
username admin privilege 15 secret x
ip ssh version 2
spanning-tree mode rapid-pvst
vlan 10
 name USERS
vlan 999
 name BLACKHOLE
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10
interface GigabitEthernet0/2
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable
line vty 0 4
 login local
 transport input ssh
"""


def rules(dev):
    return {f.rule for f in dev.findings}


def test_bad_config_hits_expected_rules():
    d = lint_text(BAD)
    assert rules(d) >= {"SEC-01", "SEC-02", "SEC-03", "SEC-04", "SEC-05", "SEC-06", "SEC-07", "SEC-08",
                        "SEC-09", "SEC-10"}
    assert d.score == 100 - (15 + 8 + 8 + 3 + 8 + 15 + 3 + 8 + 8 + 15)  # each rule weight once


def test_clean_config_scores_100():
    d = lint_text(GOOD)
    assert d.findings == [] and d.score == 100


def test_unknown_lines_do_not_crash():
    assert lint_text("hostname X\ninterface Gi0/1\n duplex full\n mtu 9000\n").hostname == "X"


def test_rule_weight_counted_once_per_device():
    d = lint_text(GOOD.replace(" spanning-tree bpduguard enable\n", "") + "interface Gi0/3\n switchport mode access\n switchport access vlan 10\n spanning-tree portfast\n")
    assert [f.rule for f in d.findings].count("SEC-03") == 2 and d.score == 92


@pytest.mark.parametrize("name", NAMES)
def test_generated_configs_score_high(designs, name):
    rep = lint_configs(render_all(designs[name]))
    assert rep.score >= 80
    found = {f.rule for d in rep.devices for f in d.findings}
    assert found <= {"SEC-09", "SEC-11", "SEC-12"}  # OSPF auth pending owner OK; placeholders; default-allow


def test_rules_have_fix_text():
    assert all(fix for _, _, fix in RULES.values())
