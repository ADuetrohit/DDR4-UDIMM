"""Whole-schematic check across every sheet of the project.

- merges nets by name across sheets (Global net identifier scope)
- flags named nets that reach fewer than 2 pins, and pins left dangling on
  unnamed single-pin nets without a No-ERC marker
- flags nets that carry two names (shorts)
- counts parts by value and compares them with the BOM

Usage:
    py -3.11 tools/check_project.py <sheet1.SchDoc> [<sheet2.SchDoc> ...]
"""
import csv
import glob
import os
import re
import sys
from collections import Counter, defaultdict

from schdoc_nets import extract

# BOM MPN -> tokens that identify the part in a schematic Comment
BOM_MATCH = {
    "MT40A2G8SA-062E:F": ("MT40A2G8SA",),
    "34AA04T-I/MUY": ("34AA04",),
    "RC0402FR-07240RL": ("240R", "07240"),
    "RC0402FR-0715RL": ("15R", "0715"),
    "RC0402FR-0739RL": ("39R", "0739"),
    "RC0402FR-0747RL": ("47R", "0747"),
    "RC0402FR-0775RL": ("75R", "0775"),
    "GRM155R71H103KA88D": ("0.01UF", "103KA"),
    "GRM155R71C104KA88D": ("0.1UF", "104KA"),
    "CL05A105KP5NNNC": ("1UF", "105KP"),
    "CL10A475KO8NNNC": ("4.7UF", "475K"),
}


def classify(comment):
    c = comment.upper().replace(" ", "")
    for mpn, tokens in BOM_MATCH.items():
        for t in tokens:
            if t == "1UF" and ("0.1UF" in c or "0.01UF" in c):
                continue
            if t in c:
                return mpn
    return None


def main():
    sheets = sys.argv[1:]
    if not sheets:
        sys.exit(__doc__)

    by_name = defaultdict(list)          # name -> [(sheet, pin members)]
    fails, warns = [], []
    parts = Counter()
    seen_parts = set()
    for path in sheets:
        sheet = os.path.basename(path)
        res = extract(path)
        for owner, comp in res["components"].items():
            key = (sheet, owner)
            if key in seen_parts:
                continue
            seen_parts.add(key)
            mpn = classify(comp["comment"])
            if comp["comment"] == "DDR4_UDIMM_288":
                parts["DDR4_UDIMM_288 (part)"] += 1
            elif mpn:
                parts[mpn] += 1
            else:
                parts["unrecognised: " + comp["comment"]] += 1
        for net in res["nets"]:
            if len(net["names"]) > 1:
                fails.append(f"{sheet}: SHORT, one net has names {net['names']}")
            if net["names"]:
                for n in net["names"]:
                    by_name[n].append((sheet, net["pins"]))
            elif len(net["pins"]) == 1 and not net.get("noerc"):
                m = net["pins"][0]
                warns.append(f"{sheet}: dangling pin {m['ref'].split('#')[0]}.{m['pin']} ({m['name']}) "
                             f"on '{m['comment']}' with no connection and no No-ERC")

    for name, groups in sorted(by_name.items()):
        n_pins = sum(len(p) for _, p in groups)
        if n_pins < 2:
            fails.append(f"net '{name}' reaches only {n_pins} pin(s) on {sorted({s for s, _ in groups})}")

    # the DRAM is a 2-part symbol and the connector a 5-part symbol
    counts = dict(parts)
    counts["MT40A2G8SA-062E:F"] = counts.get("MT40A2G8SA-062E:F", 0) / 2
    here = os.path.dirname(os.path.abspath(__file__))
    bom_files = sorted(glob.glob(os.path.join(here, "..", "bom", "BOM_v*.csv")),
                       key=lambda p: int(re.search(r"_v(\d+)", p).group(1)))
    bom = list(csv.DictReader(open(bom_files[-1], encoding="utf-8")))
    print(f"Sheets: {len(sheets)}   nets by name: {len(by_name)}   BOM: {os.path.basename(bom_files[-1])}")
    print(f"{'MPN':<22} {'BOM':>5} {'schematic':>10}")
    for row in bom:
        want = int(row["Qty_on_board"])
        got = counts.get(row["MPN"], 0)
        flag = "" if got == want else "   <-- mismatch"
        print(f"{row['MPN']:<22} {want:>5} {got:>10g}{flag}")
        if got != want:
            fails.append(f"{row['MPN']}: BOM says {want}, schematic has {got:g}")
    j = counts.get("DDR4_UDIMM_288 (part)", 0)
    print(f"{'edge connector parts':<22} {5:>5} {j:>10}")
    if j != 5:
        fails.append(f"edge connector: expected 5 parts (J1A-J1E), found {j}")
    for k, v in counts.items():
        if k.startswith("unrecognised"):
            fails.append(f"{v} x {k}")

    print(f"Failures: {len(fails)}, warnings: {len(warns)}")
    for f in fails:
        print("  FAIL:", f)
    for w in warns:
        print("  WARN:", w)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
