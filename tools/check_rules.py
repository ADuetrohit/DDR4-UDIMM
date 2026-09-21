"""Check the PcbDoc design rules against the values chosen from Annex A (Raw Card A3).

Reads the Rules6 stream of the Altium .PcbDoc and compares each expected rule's scope,
values, enabled state and priority. Rules not listed here are only counted.
Also checks the DATA_DRAM net class and the differential pairs (DifferentialPairs6): CK0, CK1, DQS0-7 on the
connector side and DQS0_DRAM-DQS7_DRAM between the 15 ohm resistors and the DRAMs.

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
    "Width_DATA": ("Width", "InNetClass('DATA') Or InNetClass('DATA_DRAM')", None,
                   {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.1, "MAXLIMIT": 0.1}, True, 4),
    "Width_SPD": ("Width", "InNetClass('SPD')", None,
                  {"MINLIMIT": 0.1, "PREFEREDWIDTH": 0.15, "MAXLIMIT": 0.3}, True, 5),
    "Width": ("Width", "All", None, {"MINLIMIT": 0.075, "PREFEREDWIDTH": 0.1, "MAXLIMIT": 0.3}, True, 6),
    # Block 3: differential pairs (Annex A: DQS 0.10/0.10, CK 0.075/0.10 or 0.15/0.10).
    # MINLIMIT/MAXLIMIT are the gap; *WIDTH fields are checked on every copper layer.
    "DiffPair_DQS": ("DiffPairsRouting", "InDifferentialPairClass('DP_DQS')", None,
                     {"MINLIMIT": 0.1, "MOSTFREQGAP": 0.1, "MAXLIMIT": 0.127, "MAXUNCOUPLEDLENGTH": 3.0,
                      "MINWIDTH": 0.075, "PREFWIDTH": 0.1, "MAXWIDTH": 0.1}, True, 1),
    "DiffPair_CK": ("DiffPairsRouting", "InDifferentialPairClass('DP_CK')", None,
                    {"MINLIMIT": 0.1, "MOSTFREQGAP": 0.1, "MAXLIMIT": 0.127, "MAXUNCOUPLEDLENGTH": 3.0,
                     "MINWIDTH": 0.075, "PREFWIDTH": 0.075, "MAXWIDTH": 0.15}, True, 2),
    "DiffPairsRouting": ("DiffPairsRouting", "All", None,
                         {"MINLIMIT": 0.1, "MOSTFREQGAP": 0.1, "MAXLIMIT": 0.127, "MAXUNCOUPLEDLENGTH": 3.0,
                          "MINWIDTH": 0.075, "PREFWIDTH": 0.1, "MAXWIDTH": 0.15}, True, 3),
    # Block 4: routing layers (Annex A A3 fabrication table); L2, L4, L7 are planes
    "RoutingLayers_POWER": ("RoutingLayers", "InNetClass('POWER')", None, {"LAYERS": {1, 2, 3, 4, 5, 6, 7, 8}}, True, 1),
    "RoutingLayers_DATA": ("RoutingLayers", "InNetClass('DATA') Or InNetClass('DATA_DRAM')", None,
                           {"LAYERS": {1, 3, 8}}, True, 2),
    "RoutingLayers_CK": ("RoutingLayers", "InNetClass('CK') Or InNetClass('CK_UNUSED')", None,
                         {"LAYERS": {1, 6, 8}}, True, 3),
    "RoutingLayers_ADDR": ("RoutingLayers", "InNetClass('ADDR') Or InNetClass('CTRL') Or InNetClass('RESET') Or "
                           "InNetClass('ALERT')", None, {"LAYERS": {1, 3, 5, 6, 8}}, True, 4),
    "RoutingLayers": ("RoutingLayers", "All", None, {"LAYERS": {1, 3, 5, 6, 8}}, True, 5),
    # Block 5: vias and BGA fanout. DRAM pads 0.34 mm at 0.8 mm pitch: a via centred between four balls
    # can be up to 0.44 mm across with 0.175 mm via-to-BGA clearance
    "RoutingVias_POWER": ("RoutingVias", "InNetClass('POWER')", None,
                          {"MINWIDTH": 0.4, "WIDTH": 0.5, "MAXWIDTH": 0.6,
                           "MINHOLEWIDTH": 0.2, "HOLEWIDTH": 0.25, "MAXHOLEWIDTH": 0.3}, True, 1),
    "RoutingVias": ("RoutingVias", "All", None,
                    {"MINWIDTH": 0.4, "WIDTH": 0.4, "MAXWIDTH": 0.45,
                     "MINHOLEWIDTH": 0.2, "HOLEWIDTH": 0.2, "MAXHOLEWIDTH": 0.25}, True, 2),
    "Fanout_BGA": ("FanoutControl", "IsBGA", None,
                   {"FANOUTSTYLE": "BGA", "BGAVIAMODE": "Centered"}, True, 1),
    "HoleSize": ("HoleSize", "All", None, {"MINLIMIT": 0.2, "MAXLIMIT": 0.3}, True, None),
    "MinimumAnnularRing": ("MinimumAnnularRing", "All", None, {"MINIMUMRING": 0.1}, True, None),
}

# RoutingLayers keys for copper L1..L8 (Altium numbers inner layers Mid Layer 1..6)
ROUTING_KEYS = {1: "TOP LAYER_V5", **{n: f"MID LAYER {n - 1}_V5" for n in range(2, 8)}, 8: "BOTTOM LAYER_V5"}

# DATA_DRAM net class: DRAM side of the 88 data resistors, i.e. NetRn_1 except the ZQ nets (n = 12k+1)
DATA_DRAM = {f"NetR{n}_1" for n in range(1, 97) if n % 12 != 1}

# per-layer width fields in DiffPairsRouting rules (8 copper layers)
LAYER_KEYS = ["TOPLAYER"] + [f"MIDLAYER{i}" for i in range(1, 7)] + ["BOTTOMLAYER"]


# pair name: (positive net, negative net). On DRAM sheet k (U1..U8) the DQS resistors are
# R(12k+9) for DQS_t and R(12k+10) for DQS_c; the DRAM side of each is the unnamed net NetRn_1.
PAIRS = {"CK0": ("CK0_T", "CK0_C"), "CK1": ("CK1_T", "CK1_C")}
for k in range(8):
    PAIRS[f"DQS{k}"] = (f"DQS{k}_T", f"DQS{k}_C")
    PAIRS[f"DQS{k}_DRAM"] = (f"NetR{12 * k + 9}_1", f"NetR{12 * k + 10}_1")


def records(path, stream):
    ole = olefile.OleFileIO(path)
    if not ole.exists(stream):
        return []
    data = ole.openstream(stream).read()
    out, pos = [], 0
    while pos + 4 <= len(data):
        n = int.from_bytes(data[pos:pos + 4], "little")
        body = data[pos + 4:pos + 4 + n].decode("latin-1")
        pos += 4 + n
        out.append(dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p))
    return out


def rules(path):
    data = olefile.OleFileIO(path).openstream("Rules6/Data").read()
    out, pos = {}, 0
    while pos + 6 <= len(data):
        n = int.from_bytes(data[pos + 2:pos + 6], "little")
        body = data[pos + 6:pos + 6 + n].decode("latin-1")
        pos += 6 + n
        kv = dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p)
        if "NAME" in kv:
            out[kv["NAME"].strip()] = kv
    return out


def mm(value):
    return float(value.replace("mil", "")) * MIL if value and value.endswith("mil") else None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    have = rules(sys.argv[1])
    errors = []
    warnings = [f"rule name {r['NAME']!r} has leading/trailing spaces" for r in have.values()
                if r["NAME"] != r["NAME"].strip()]
    for name, (kind, s1, s2, values, enabled, prio) in EXPECTED.items():
        r = have.get(name)
        if r is None:
            errors.append(f"{name}: missing")
            continue
        got = {}
        for f in values:
            if f == "LAYERS":
                allowed = {n for n, key in ROUTING_KEYS.items() if r.get(key) == "TRUE"}
                print(f"  {kind:18} {name:28} {'on ' if r.get('ENABLED') == 'TRUE' else 'off'} "
                      f"prio {r.get('PRIORITY')}  layers " + ", ".join(f"L{n}" for n in sorted(allowed)))
                if allowed != values[f]:
                    errors.append(f"{name}: layers {sorted(allowed)}, expected {sorted(values[f])}")
                continue
            if isinstance(values[f], str):
                if r.get(f) != values[f]:
                    errors.append(f"{name}: {f} {r.get(f)!r}, expected {values[f]!r}")
                continue
            if f.endswith("WIDTH") and kind == "DiffPairsRouting":
                per_layer = {mm(r.get(f"{lk}_{f}")) for lk in LAYER_KEYS}
                got[f] = per_layer.pop() if len(per_layer) == 1 else None
            else:
                got[f] = mm(r.get(f))
        if got:
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
            if f == "LAYERS" or isinstance(want, str):
                continue
            if got[f] is None or abs(got[f] - want) > 0.001:
                errors.append(f"{name}: {f} {got[f]}, expected {want}")

    pairs = {r.get("NAME"): (r.get("POSITIVENETNAME"), r.get("NEGATIVENETNAME"))
             for r in records(sys.argv[1], "DifferentialPairs6/Data")}
    print(f"\nDifferential pairs: {len(pairs)} (expected {len(PAIRS)})")
    for name, nets in PAIRS.items():
        if name not in pairs:
            errors.append(f"differential pair {name} missing ({nets[0]} / {nets[1]})")
        elif pairs[name] != nets:
            errors.append(f"differential pair {name} is {pairs[name]}, expected {nets}")
    for name in sorted(set(pairs) - set(PAIRS)):
        errors.append(f"unexpected differential pair {name} {pairs[name]}")

    classes = {r.get("NAME"): {v for k, v in r.items() if k[:1] == "M" and k[1:].isdigit()}
               for r in records(sys.argv[1], "Classes6/Data") if r.get("KIND") == "0"}
    dd = classes.get("DATA_DRAM")
    print(f"Net class DATA_DRAM: {len(dd) if dd is not None else 'missing'} nets (expected {len(DATA_DRAM)})")
    if dd is None:
        errors.append("net class DATA_DRAM missing")
    elif dd != DATA_DRAM:
        errors.append(f"DATA_DRAM missing {sorted(DATA_DRAM - dd)}, extra {sorted(dd - DATA_DRAM)}")

    others = sorted(n for n in have if n not in EXPECTED)
    print(f"\nOther rules (not checked): {len(others)}")
    for w in warnings:
        print("WARNING", w)
    for e in errors:
        print("ERROR", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
