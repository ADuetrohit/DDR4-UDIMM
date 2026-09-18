"""Check the 288-pin edge-connector sheet against the JEDEC pinout.

For every connector pin: a net-label pin must carry exactly its expected net
name, a power pin its power-port name, and an unused pin must be unconnected
and should carry a No-ERC marker. Also reports shorts (nets with two names)
and default Altium label names.

Usage:
    py -3.11 tools/check_connector.py <edge.SchDoc>
"""
import csv
import os
import re
import sys

from schdoc_nets import extract

CONNECTOR_COMMENT = "DDR4_UDIMM_288"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    res = extract(sys.argv[1])

    here = os.path.dirname(os.path.abspath(__file__))
    expected = {}
    with open(os.path.join(here, "..", "hardware", "libraries", "edge_connector",
                           "DDR4_UDIMM_288_pinout.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            expected[r["Pin"]] = (r["Net on this design"], r["Connect with"], r["JEDEC name"])

    pin_net = {}
    for net in res["nets"]:
        for m in net["pins"]:
            if m["comment"] == CONNECTOR_COMMENT:
                pin_net[m["pin"]] = (net, m["ref"])
    noerc = set()
    for k in res["noerc_pins"]:
        p = res["pins"][k]
        if res["components"][p["owner"]]["comment"] == CONNECTOR_COMMENT:
            noerc.add(p["pin"])

    fails, warns = [], []
    for pin, (want, how, jedec) in sorted(expected.items(), key=lambda x: int(x[0])):
        if pin not in pin_net:
            fails.append(f"pin {pin} ({jedec}): not found on this sheet (part not placed?)")
            continue
        net, ref = pin_net[pin]
        names = set(net["names"])
        others = [m for m in net["pins"] if m["pin"] != pin or m["ref"] != ref]
        if how.startswith("No-ERC"):
            if names or others:
                fails.append(f"pin {pin} ({jedec}): must be NOT connected, but is on "
                             f"{sorted(names) or 'a wire to other pins'}")
            elif pin not in noerc:
                warns.append(f"pin {pin} ({jedec}): unused, add a No-ERC mark")
        elif names != {want}:
            got = sorted(names) if names else "nothing (no label/port)"
            fails.append(f"pin {pin} ({jedec}): expected {how} '{want}', got {got}")

    for net in res["nets"]:
        if len(net["names"]) > 1:
            fails.append(f"SHORT: one net has several names {sorted(net['names'])}")
        for n in net["names"]:
            if re.fullmatch(r"NetLabel\d+", n):
                pins = sorted(m["pin"] for m in net["pins"])
                fails.append(f"default label name '{n}' on connector pins {pins}")

    ok = 288 - len([f for f in fails if f.startswith("pin ")])
    print(f"Connector pins found on sheet: {len(pin_net)} / 288")
    print(f"Pins correct: {ok} / 288, failures: {len(fails)}, missing No-ERC marks: {len(warns)}")
    for f in fails:
        print("  FAIL:", f)
    for w in warns:
        print("  WARN:", w)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
