"""Check the saved gold-finger footprint against tools/gen_edge_footprint.py (MO-309F).

- 288 pads: designator, layer, position, size, SMD, rectangular, and no solder paste
- board outline on Mechanical 1 (every line and arc)
- solder-mask windows over the finger groups
- optionally: that a SchLib / SchDoc uses this footprint as its PCB model

Usage:
    py -3.11 tools/check_edge_footprint.py hardware/libraries/DDR4_UDIMM.PcbLib [--sch <file.SchLib|file.SchDoc> ...]
"""
import sys

import olefile

import gen_edge_footprint as g
import pcblib

TOL = 0.002     # mm


def close(a, b):
    return abs(a - b) <= TOL


def check_pads(prims, fails):
    want = {str(r["pad"]): r for r in g.pads()}
    got = {}
    for p in prims:
        if p["type"] == "pad":
            if p["name"] in got:
                fails.append(f"pad {p['name']} appears twice")
            got[p["name"]] = p
    missing = sorted(set(want) - set(got), key=int)
    extra = sorted(set(got) - set(want))
    if missing:
        fails.append(f"{len(missing)} pads missing: {missing[:10]}{' ...' if len(missing) > 10 else ''}")
    if extra:
        fails.append(f"unexpected pads: {extra[:10]}")
    offsets = set()
    bad_pos = 0
    pasted = []
    for name in sorted(set(want) & set(got), key=int):
        w, p = want[name], got[name]
        if p["layer"] != w["layer"]:
            fails.append(f"pad {name}: layer {p['layer']}, expected {w['layer']}")
        if not (close(p["x"], w["x"]) and close(p["y"], w["y"])):
            bad_pos += 1
            offsets.add((round(p["x"] - w["x"], 2), round(p["y"] - w["y"], 2)))
        if not (close(p["w"], w["w"]) and close(p["h"], w["h"])):
            fails.append(f"pad {name}: size {p['w']} x {p['h']}, expected {w['w']} x {w['h']}")
        if p["hole"] != 0:
            fails.append(f"pad {name}: has a {p['hole']} mm hole, must be SMD")
        if p["shape"] != 2:
            fails.append(f"pad {name}: shape code {p['shape']}, expected rectangular (2)")
        if abs(p["rot"] % 180) > 0.01:
            fails.append(f"pad {name}: rotated {p['rot']} deg")
        if not (p["paste_mode"] == "manual" and p["paste"] <= -g.PAD_W / 2):
            pasted.append(name)
    if bad_pos:
        hint = f"; every pad is shifted by {offsets.pop()} mm (footprint origin)" if len(offsets) == 1 else ""
        fails.append(f"{bad_pos} pads off position{hint}")
    if pasted:
        fails.append(f"{len(pasted)} pads would get solder paste (e.g. pad {pasted[0]}): set Paste Mask Expansion "
                     f"to Manual, {g.PASTE_EXPANSION} mm on every finger")
    return len(got)


def _arc_key(a0, a1):
    return round(a0 % 360, 2), round(a1 % 360, 2)


def check_outline(prims, fails):
    want_lines, want_arcs = [], []
    for s in g.outline():
        (want_lines if s[0] == "line" else want_arcs).append(s[1:])
    lines = [p for p in prims if p["type"] == "track" and p["layer"] == "Mechanical1"]
    arcs = [p for p in prims if p["type"] == "arc" and p["layer"] == "Mechanical1"]
    for x1, y1, x2, y2 in want_lines:
        hit = [t for t in lines if (close(t["x1"], x1) and close(t["y1"], y1) and close(t["x2"], x2) and close(t["y2"], y2))
               or (close(t["x1"], x2) and close(t["y1"], y2) and close(t["x2"], x1) and close(t["y2"], y1))]
        if not hit:
            fails.append(f"outline line ({x1}, {y1}) -> ({x2}, {y2}) missing on Mechanical 1")
    for cx, cy, r, a0, a1 in want_arcs:
        hit = [a for a in arcs if close(a["cx"], cx) and close(a["cy"], cy) and close(a["r"], r)
               and _arc_key(a["a0"], a["a1"]) == _arc_key(a0, a1)]
        if not hit:
            fails.append(f"outline arc centre ({cx}, {cy}) R{r} {a0}-{a1} deg missing on Mechanical 1")
    if len(lines) != len(want_lines) or len(arcs) != len(want_arcs):
        fails.append(f"Mechanical 1 has {len(lines)} lines + {len(arcs)} arcs, expected "
                     f"{len(want_lines)} + {len(want_arcs)}")
    return len(lines), len(arcs)


def check_mask(prims, fails):
    fills = [p for p in prims if p["type"] == "fill"]
    for x1, y1, x2, y2 in g.mask_openings():
        for layer in ("TopSolder", "BottomSolder"):
            hit = [f for f in fills if f["layer"] == layer and close(min(f["x1"], f["x2"]), x1)
                   and close(min(f["y1"], f["y2"]), y1) and close(max(f["x1"], f["x2"]), x2)
                   and close(max(f["y1"], f["y2"]), y2)]
            if not hit:
                fails.append(f"solder-mask window {layer} ({x1}, {y1})-({x2}, {y2}) missing")
    return len(fills)


def check_sch_link(path, fails):
    """The symbol (or placed part) must carry a PCBLIB model named after the footprint."""
    ole = olefile.OleFileIO(path)
    found = 0
    for e in ole.listdir():
        text = ole.openstream(e).read().decode("latin-1", "replace")
        for rec in text.split("|RECORD=45|")[1:]:
            fields = dict(kv.split("=", 1) for kv in rec.split("\x00")[0].split("|") if "=" in kv)
            fields = {k.upper(): v for k, v in fields.items()}
            if fields.get("MODELTYPE", "").upper() == "PCBLIB" and fields.get("MODELNAME") == g.FOOTPRINT:
                found += 1
    if not found:
        fails.append(f"{path}: no PCB footprint model '{g.FOOTPRINT}' attached")
    return found


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    lib, sch = args[0], [a for a in args[1:] if a != "--sch"]
    fails = []
    names = pcblib.footprints(lib)
    if g.FOOTPRINT not in names:
        print(f"footprints in {lib}: {names}")
        sys.exit(f"RESULT: FAIL - footprint {g.FOOTPRINT} not found")
    prims = pcblib.read(lib, g.FOOTPRINT)
    n_pads = check_pads(prims, fails)
    n_lines, n_arcs = check_outline(prims, fails)
    n_fills = check_mask(prims, fails)
    print(f"{g.FOOTPRINT}: {n_pads} pads, outline {n_lines} lines + {n_arcs} arcs, {n_fills} fills")
    for path in sch:
        print(f"{path}: {check_sch_link(path, fails)} footprint link(s)")
    others = sorted({f"{p['type']} on {p['layer']}" for p in prims if p["type"] not in ("pad", "track", "arc", "fill")})
    if others:
        print("other primitives:", ", ".join(others))
    print(f"Failures: {len(fails)}")
    for f in fails[:60]:
        print("  FAIL:", f)
    if len(fails) > 60:
        print(f"  ... and {len(fails) - 60} more")
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
