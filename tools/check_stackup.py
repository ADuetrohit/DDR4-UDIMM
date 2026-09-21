"""Check the PcbDoc layer stack and impedance profiles against Annex A (Raw Card A3).

Reads the Board6 stream of the Altium .PcbDoc and checks:
  - 8 copper layers, dielectric heights 70/80/420/80/420/80/70 um (Annex A fabrication table)
  - board thickness over the fingers 1.40 +/- 0.10 mm (without solder mask)
  - the six impedance profiles exist with their Annex A targets and tolerances
  - every enabled profile layer references only plane layers (L2, L4, L7) or the surface
  - no enabled profile layer needs a trace narrower than 0.075 mm (Annex A minimum)

Usage:
    py -3.11 tools/check_stackup.py <board.PcbDoc>
"""
import re
import sys

import olefile

MIL = 0.0254                                   # mm
DIELECTRIC_UM = [70, 80, 420, 80, 420, 80, 70]
PLANES = {2, 4, 7}                             # copper layer numbers used as references
MIN_WIDTH = 0.075                              # mm, Annex A minimum trace width
PROFILES = {"SE_50": (50, 10, False), "SE_55": (55, 10, False), "SE_40": (40, 10, False),
            "DIFF_83": (83, 15, True), "DIFF_93": (93, 15, True), "DIFF_70": (70, 15, True)}


def board_kv(path):
    data = olefile.OleFileIO(path).openstream("Board6/Data").read().decode("latin-1")
    kv = {}
    for part in re.split(r"[|\x00]", data):
        if "=" in part:
            k, v = part.split("=", 1)
            kv.setdefault(k, v)
    return kv


def mm(value):
    return float(value.replace("mil", "")) * MIL


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    kv = board_kv(sys.argv[1])
    errors = []

    stack, i = [], 0
    while f"V9_STACK_LAYER{i}_NAME" in kv:
        p = f"V9_STACK_LAYER{i}_"
        if p + "COPTHICK" in kv:
            stack.append(("Cu", kv[p + "NAME"], mm(kv[p + "COPTHICK"]), kv[p + "LAYERID"]))
        elif p + "DIELHEIGHT" in kv and kv.get(p + "DIELMATERIAL") != "Solder Resist":
            stack.append(("Diel", kv[p + "NAME"], mm(kv[p + "DIELHEIGHT"]), kv.get(p + "DIELCONST")))
        i += 1

    copper = [s for s in stack if s[0] == "Cu"]
    diel = [s for s in stack if s[0] == "Diel"]
    layer_no = {s[3]: n for n, s in enumerate(copper, 1)}
    names = {s[3]: s[1] for s in copper}
    total = sum(s[2] for s in stack)

    print("Layer stack (without solder mask):")
    for kind, name, t, extra in stack:
        tag = f"L{layer_no[extra]}" if kind == "Cu" else f"Dk {extra}"
        print(f"  {kind:4} {name:16} {t * 1000:6.1f} um  {tag}")
    print(f"  total {total:.3f} mm")

    if len(copper) != 8:
        errors.append(f"{len(copper)} copper layers, expected 8")
    got = [round(s[2] * 1000) for s in diel]
    if got != DIELECTRIC_UM:
        errors.append(f"dielectrics {got} um, expected {DIELECTRIC_UM}")
    if not 1.30 <= total <= 1.50:
        errors.append(f"thickness {total:.3f} mm outside 1.40 +/- 0.10")

    profiles, j = {}, 0
    while f"V9_IMPEDANCEPROFILE{j}_NAME" in kv:
        p = f"V9_IMPEDANCEPROFILE{j}_"
        profiles[kv[p + "ID"]] = (kv[p + "NAME"], float(kv[p + "IMPEDANCE"]),
                                  float(kv[p + "IMPEDANCE_TOLERANCE"]), kv[p + "ISDIFFPAIR"] == "TRUE")
        j += 1
    by_name = {v[0]: v for v in profiles.values()}
    for name, (z, tol, diff) in PROFILES.items():
        if name not in by_name:
            errors.append(f"profile {name} missing")
        elif by_name[name][1:] != (z, tol, diff):
            errors.append(f"profile {name} is {by_name[name][1:]}, expected {(z, tol, diff)}")

    print("\nImpedance widths (enabled layers):")
    entries = sorted({int(m.group(1)) for k in kv for m in [re.match(r"V9_TRACEIMPEDANCE(\d+)_", k)] if m})
    for t in entries:
        g = lambda k: kv.get(f"V9_TRACEIMPEDANCE{t}_{k}")
        if g("ENABLED") != "TRUE":
            continue
        prof = profiles.get(g("PROFILE_ID"), ("?",))[0]
        layer = g("LAYER_V7ID")
        refs = [r for r in (g("REF_TOP_V7ID"), g("REF_BOT_V7ID")) if r in layer_no]
        gap = f"  gap {mm(g('DIFF_PAIR_GAP')):.3f}" if prof.startswith("DIFF") else ""
        print(f"  {prof:8} L{layer_no[layer]} {names[layer]:14} w {mm(g('TRACE_WIDTH')):.4f} mm{gap}"
              f"  Z {float(g('CALC_IMPEDANCE')):.1f}  ref {', '.join('L%d' % layer_no[r] for r in refs)}")
        bad = [f"L{layer_no[r]}" for r in refs if layer_no[r] not in PLANES]
        if bad:
            errors.append(f"{prof} on L{layer_no[layer]} references signal layer {', '.join(bad)}")
        if mm(g("TRACE_WIDTH")) < MIN_WIDTH:
            errors.append(f"{prof} on L{layer_no[layer]} needs {mm(g('TRACE_WIDTH')):.4f} mm, "
                          f"below the {MIN_WIDTH} mm Annex A minimum; disable it on this layer")

    print()
    for e in errors:
        print("ERROR", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
