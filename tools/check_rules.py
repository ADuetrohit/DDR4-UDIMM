"""Check the PcbDoc design rules against the values chosen from Annex A (Raw Card A3).

Reads the Rules6 stream of the Altium .PcbDoc and compares each expected rule's scope,
values, enabled state and priority. Rules not listed here are only printed.

Usage:
    py -3.11 tools/check_rules.py <board.PcbDoc>
"""
import sys

import olefile

MIL = 0.0254

# name: (kind, scope1, scope2, {field: mm}, enabled, priority or None)
EXPECTED = {
    # Block 1: clearance
    "Clearance_GoldFingers": ("Clearance", "InComponent('J1')", "InComponent('J1')", {"GAP": 0.2}, True, None),
    "Clearance_ViaToBGA": ("Clearance", "IsVia", "IsPad And HasFootprint('SA_MFG')", {"GAP": 0.175}, True, None),
    "Clearance_ViaToOtherPad": ("Clearance", "IsVia", "IsPad", {"GAP": 0.15}, True, None),
    "Clearance_ViaToVia": ("Clearance", "IsVia", "IsVia", {"GAP": 0.2}, True, None),
    "Clearance_LineToPad": ("Clearance", "IsTrack", "IsPad", {"GAP": 0.125}, True, None),
    "Clearance_PadToPad": ("Clearance", "IsPad", "IsPad", {"GAP": 0.25}, True, None),
    "Clearance_LineToShape": ("Clearance", "IsTrack", "InPolygon", {"GAP": 0.2}, True, None),
    "Clearance": ("Clearance", "All", "All", {"GAP": 0.1}, True, None),
    "ComponentClearance_Physical": ("ComponentClearance", "Not InComponent('J1')", "Not InComponent('J1')",
                                    {"GAP": 0.25}, True, None),
    "ComponentClearance": ("ComponentClearance", "All", "All", {}, False, None),
    # Block 2: width (Annex A: DQ 0.10, Address/CK 0.075, 0.075 minimum)
    "Width_POWER": ("Width", "InNetClass('POWER')", None,
                    {"MINLIMIT": 0.15, "PREFEREDWIDTH": 0.3, "MAXLIMIT": 2.0}, True, 1),
    "Width_CK": ("Width", "InNetClass('CK') Or InNetClass('CK_UNUSED')", None,
                 {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.075, "MAXLIMIT": 0.15}, True, 2),
    "Width_ADDR_CTRL": ("Width", "InNetClass('ADDR') Or InNetClass('CTRL') Or InNetClass('RESET') Or "
                        "InNetClass('ALERT')", None,
                        {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.075, "MAXLIMIT": 0.15}, True, 3),
    "Width_DATA": ("Width", "InNetClass('DATA')", None,
                   {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.1, "MAXLIMIT": 0.1}, True, 4),
    "Width_SPD": ("Width", "InNetClass('SPD')", None,
                  {"MINLIMIT": 0.1, "PREFEREDWIDTH": 0.15, "MAXLIMIT": 0.3}, True, 5),
    "Width": ("Width", "All", None, {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.1, "MAXLIMIT": 0.3}, True, 6),
}


def rules(path):
    data = olefile.OleFileIO(path).openstream("Rules6/Data").read()
    out, pos = {}, 0
    while pos + 6 <= len(data):
        n = int.from_bytes(data[pos + 2:pos + 6], "little")
        body = data[pos + 6:pos + 6 + n].decode("latin-1")
        pos += 6 + n
        kv = dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p)
        if "NAME" in kv:
            out[kv["NAME"]] = kv
    return out


def mm(value):
    return float(value.replace("mil", "")) * MIL if value and value.endswith("mil") else None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    have = rules(sys.argv[1])
    errors = []
    for name, (kind, s1, s2, values, enabled, prio) in EXPECTED.items():
        r = have.get(name)
        if r is None:
            errors.append(f"{name}: missing")
            continue
        got = {f: mm(r.get(f)) for f in values}
        print(f"  {kind:18} {name:28} {'on ' if r.get('ENABLED') == 'TRUE' else 'off'} "
              f"prio {r.get('PRIORITY')}  " + "  ".join(f"{f.lower()} {v:.3f}" for f, v in got.items() if v))
        if r.get("RULEKIND") != kind:
            errors.append(f"{name}: kind {r.get('RULEKIND')}, expected {kind}")
        if r.get("SCOPE1EXPRESSION") != s1 or (s2 is not None and r.get("SCOPE2EXPRESSION") != s2):
            errors.append(f"{name}: scope {r.get('SCOPE1EXPRESSION')!r} / {r.get('SCOPE2EXPRESSION')!r}")
        if (r.get("ENABLED") == "TRUE") != enabled:
            errors.append(f"{name}: should be {'enabled' if enabled else 'disabled'}")
        if prio is not None and r.get("PRIORITY") != str(prio):
            errors.append(f"{name}: priority {r.get('PRIORITY')}, expected {prio}")
        for f, want in values.items():
            if got[f] is None or abs(got[f] - want) > 0.001:
                errors.append(f"{name}: {f} {got[f]}, expected {want}")

    others = sorted(n for n in have if n not in EXPECTED)
    print(f"\nOther rules (not checked): {len(others)}")
    for e in errors:
        print("ERROR", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
