"""Check the termination sheet (TERM.SchDoc) against docs/SCHEMATIC_SUPPORT.md.

Usage:
    py -3.11 tools/check_term.py <TERM.SchDoc>
"""
import sys
from collections import Counter, defaultdict

from schdoc_nets import extract

CA_NETS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10_AP", "A11", "A12_BC",
           "A13", "WE", "A15_CAS", "A16_RAS", "BA0", "BA1", "BG0", "BG1", "ACT", "PAR", "CS", "CKE", "ODT"]


def kind(comment):
    c = comment.upper().replace(" ", "")
    for key, tags in {"39R": ("0739", "39R"), "75R": ("0775", "75R"), "47R": ("0747", "47R"),
                      "4.7uF": ("4.7U", "475"), "0.01uF": ("0.01U", "103"), "0.1uF": ("0.1U", "104")}.items():
        if any(t in c for t in tags):
            return key
    return comment


def main():
    res = extract(sys.argv[1])
    pins_of = defaultdict(dict)
    for net in res["nets"]:
        for m in net["pins"]:
            pins_of[m["ref"]][m["pin"]] = (net, m["comment"])

    def ends(ref):
        pair = []
        for pin in ("1", "2"):
            net, _ = pins_of[ref][pin]
            pair.append(tuple(sorted(net["names"])) if net["names"] else ("<node %d>" % id(net),))
        return pair

    parts = defaultdict(list)
    for ref, pins in pins_of.items():
        comment = next(iter(pins.values()))[1]
        if set(pins) == {"1", "2"}:
            parts[kind(comment)].append(ref)

    fails = []
    # 26 x 39R: CA/CTRL net <-> VTT, each net exactly once
    seen = Counter()
    ck0_nodes = []
    for ref in parts["39R"]:
        a, b = ends(ref)
        names = {a[0], b[0]}
        if "VTT" in names and len(names) == 2:
            seen[(names - {"VTT"}).pop()] += 1
        elif names & {"CK0_T", "CK0_C"}:
            ck0_nodes.append(((names & {"CK0_T", "CK0_C"}).pop(), (names - {"CK0_T", "CK0_C"}).pop()))
        else:
            fails.append(f"39R {ref} connects {sorted(names)}: expected <CA net>-VTT or CK0 termination")
    for n in CA_NETS:
        if seen[n] != 1:
            fails.append(f"termination for {n}: found {seen[n]} x 39R to VTT, need exactly 1")
    for n in seen:
        if n not in CA_NETS:
            fails.append(f"unexpected 39R from {n} to VTT")
    # CK0: two 39R meeting at one node, node -> 0.01uF -> VDD
    if sorted(x[0] for x in ck0_nodes) != ["CK0_C", "CK0_T"] or len({x[1] for x in ck0_nodes}) != 1:
        fails.append(f"CK0 termination wrong: {ck0_nodes}")
    else:
        node = ck0_nodes[0][1]
        ok = any(set(n[0] for n in ends(r)) == {node, "VDD"} for r in parts["0.01uF"])
        if not ok:
            fails.append("CK0 termination node must go through 0.01uF to VDD")
    # single parts
    def pair_count(k, want_pair):
        return sum(1 for r in parts[k] if {e[0] for e in ends(r)} == set(want_pair))
    checks = [("75R", ("CK1_T", "CK1_C"), 1), ("47R", ("ALERT_n", "VDD"), 1),
              ("0.1uF", ("VTT", "VDD"), 14), ("0.1uF", ("VPP", "GND"), 1),
              ("0.1uF", ("VREFCA", "VDD"), 1), ("4.7uF", ("VDD", "GND"), 4)]
    for k, pair, need in checks:
        have = pair_count(k, pair)
        if have < need:
            fails.append(f"{k} between {pair[0]} and {pair[1]}: have {have}, need {need}")
    # anything wired to the wrong rails
    for k in ("0.1uF", "4.7uF", "0.01uF", "47R", "75R"):
        for r in parts[k]:
            p = {e[0] for e in ends(r)}
            known = [set(c[1]) for c in checks if c[0] == k] + ([{"VDD"} | p] if k == "0.01uF" else [])
            if not any(p == s for s in known):
                fails.append(f"{k} {r} connects {sorted(p)} (not an expected pair)")
    for net in res["nets"]:
        if len(net["names"]) > 1:
            fails.append(f"SHORT: one net has several names {sorted(net['names'])}")

    print("Parts found:", {k: len(v) for k, v in parts.items()})
    print(f"Failures: {len(fails)}")
    for f in fails:
        print("  FAIL:", f)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
