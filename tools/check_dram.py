"""Check every DDR4 DRAM on an Altium .SchDoc against the design spec.

Rules come from docs/SCHEMATIC_DRAM.md (Micron MT40A2G8SA-062E:F ball map,
JESD21-C 4.20.26 Table 9, Annex A Raw Card A3). Net names are the ones used
on the schematic.

Usage:
    py -3.11 tools/check_dram.py <file.SchDoc> [<file2.SchDoc> ...]
"""
import re
import sys
from collections import Counter, defaultdict

from schdoc_nets import extract

DRAM_TAG = "MT40A2G8SA"

SHARED = {  # ball -> net name (same on every DRAM)
    "L3": "A0", "L7": "A1", "M3": "A2", "K7": "A3", "K3": "A4", "L8": "A5", "L2": "A6",
    "M8": "A7", "M2": "A8", "M7": "A9", "J3": "A10_AP", "N2": "A11", "J7": "A12_BC",
    "N8": "A13", "H2": "WE", "H7": "A15_CAS", "H8": "A16_RAS", "H3": "ACT", "N3": "PAR",
    "K2": "BA0", "K8": "BA1", "J2": "BG0", "J8": "BG1", "F7": "CK0_T", "F8": "CK0_C",
    "G3": "CKE", "G7": "CS", "F3": "ODT", "L1": "RESET_N", "L9": "ALERT_n",
}
POWER = {**{b: "VDD" for b in "A1 C7 F1 F9 H1 J9 M1 N9 B2 B8 C1 C9 E2 E8".split()},
         **{b: "GND" for b in "A9 C8 E1 E9 G1 H9 K1 K9 N1 A2 A8 D1 D9 G9".split()},
         "B1": "VPP", "M9": "VPP", "J1": "VREFCA"}
NO_CONNECT = {"N7", "G2", "G8", "F2", "A3"}
DATA = {"C2": 0, "B7": 1, "D3": 2, "D7": 3, "D2": 4, "D8": 5, "E3": 6, "E7": 7,
        "C3": "DQS_T", "B3": "DQS_C", "A7": "DM"}
PER_CHIP_CAPS = {("GND", "VDD", "0.1uF"): 2, ("GND", "VDD", "1uF"): 1,
                 ("GND", "VPP", "0.1uF"): 2, ("VDD", "VREFCA", "0.1uF"): 1}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    pin_net, nets = {}, []
    warnings = []
    for f_i, path in enumerate(sys.argv[1:]):
        res = extract(path)
        if res["sheet_ports"]:
            warnings.append(f"{path}: {len(res['sheet_ports'])} sheet port(s) found; this checker does not "
                            "follow sheet ports - use power ports (VDD/VPP/VREFCA/GND) and net labels")
        for net in res["nets"]:
            nets.append(net)
        for net in res["nets"]:
            for m in net["pins"]:
                pin_net[(f_i, m["ref"], m["pin"])] = net

    def names_of(net):
        return set(net["names"])

    def other_pins(net, ref, pin):
        return [m for m in net["pins"] if not (m["ref"] == ref and m["pin"] == pin)]

    # group DRAM pins into chips by designator
    chips = defaultdict(dict)
    for (f_i, ref, pin), net in pin_net.items():
        comment = next((m["comment"] for m in net["pins"] if m["ref"] == ref), "")
        if DRAM_TAG not in comment:
            continue
        desig = ref.split("#")[0]
        key = desig if "?" not in desig else "U? (not annotated)"
        chips[key][pin] = (f_i, ref, net)

    fails, checks = [], 0

    def check(ok, msg):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(msg)

    for chip, pins in sorted(chips.items()):
        if len(pins) != 78:
            fails.append(f"{chip}: found {len(pins)} DRAM pins, expected 78 "
                         "(annotate first if several chips share 'U?')")
            continue
        for ball, want in {**SHARED, **POWER}.items():
            got = names_of(pins[ball][2])
            check(got == {want}, f"{chip}.{ball}: expected net {want}, got {sorted(got) or 'unnamed'}")
        for ball in NO_CONNECT:
            f_i, ref, net = pins[ball]
            check(not net["names"] and not other_pins(net, ref, ball),
                  f"{chip}.{ball}: should be unconnected, is on {sorted(net['names']) or other_pins(net, ref, ball)}")
        # ZQ -> 240R -> GND
        f_i, ref, net = pins["B9"]
        others = other_pins(net, ref, "B9")
        ok = len(others) == 1 and "240" in others[0]["comment"] and not net["names"]
        if ok:
            far = pin_net[(f_i, others[0]["ref"], "1" if others[0]["pin"] == "2" else "2")]
            ok = names_of(far) == {"GND"}
        check(ok, f"{chip}.B9 (ZQ): must go through one 240R to GND")
        # data byte through 15R series resistors
        byte_seen = set()
        for ball, what in DATA.items():
            f_i, ref, net = pins[ball]
            others = other_pins(net, ref, ball)
            if not (len(others) == 1 and "15R" in others[0]["comment"] and not net["names"]):
                check(False, f"{chip}.{ball}: must connect only to one 15R resistor")
                continue
            far = pin_net[(f_i, others[0]["ref"], "1" if others[0]["pin"] == "2" else "2")]
            label = next(iter(far["names"]), "")
            if isinstance(what, int):
                m = re.fullmatch(r"DQ(\d+)", label)
                ok = bool(m) and int(m.group(1)) % 8 == what
                if ok:
                    byte_seen.add(int(m.group(1)) // 8)
            else:
                m = re.fullmatch(r"(DQS|DM)(\d)(_T|_C)?", label)
                expect = {"DQS_T": ("DQS", "_T"), "DQS_C": ("DQS", "_C"), "DM": ("DM", None)}[what]
                ok = bool(m) and (m.group(1), m.group(3)) == expect
                if ok:
                    byte_seen.add(int(m.group(2)))
            check(ok and len(far["names"]) == 1, f"{chip}.{ball}: resistor far side is '{label}', wrong for {what}")
        check(len(byte_seen) == 1, f"{chip}: data pins map to bytes {sorted(byte_seen)}, must be one byte")

    # decoupling totals
    caps = Counter()
    seen = set()
    for (f_i, ref, pin), net in pin_net.items():
        comment = next((m["comment"] for m in net["pins"] if m["ref"] == ref), "")
        if not ref.startswith("C") or (f_i, ref) in seen:
            continue
        seen.add((f_i, ref))
        n1 = next(iter(pin_net.get((f_i, ref, "1"), {"names": []})["names"]), "?")
        n2 = next(iter(pin_net.get((f_i, ref, "2"), {"names": []})["names"]), "?")
        caps[tuple(sorted((n1, n2))) + (comment,)] += 1
    n_chips = len(chips)
    for key, per in PER_CHIP_CAPS.items():
        check(caps[key] >= per * n_chips,
              f"decoupling {key[2]} between {key[0]} and {key[1]}: have {caps[key]}, need {per * n_chips}")

    # nets with more than one name = accidental short
    for net in nets:
        if len(net["names"]) > 1:
            fails.append(f"net has multiple names (short?): {sorted(net['names'])}")

    print(f"DRAM chips found: {n_chips} -> {sorted(chips)}")
    print("Capacitors by net pair: " + ", ".join(f"{a}-{b} {v} x{n}" for (a, b, v), n in sorted(caps.items())))
    for w in warnings:
        print("  WARN:", w)
    print(f"Checks run: {checks}, failures: {len(fails)}")
    for f in fails:
        print("  FAIL:", f)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
