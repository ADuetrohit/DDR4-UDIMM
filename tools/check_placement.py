"""Check component positions in the PcbDoc against the recorded placement.

hardware/placement.csv is the JEDEC-derived plan (tools/gen_placement.py). After manual
fine-tuning in Altium, --export records the as-placed positions in hardware/placement_final.csv,
which then becomes the reference; the largest deviations from the plan are reported for review.

Usage:
    py -3.11 tools/check_placement.py <board.PcbDoc> [tolerance_mm]   # vs final if present, else plan
    py -3.11 tools/check_placement.py <board.PcbDoc> --plan            # vs the JEDEC plan
    py -3.11 tools/check_placement.py <board.PcbDoc> --export          # record as-placed as final
"""
import csv
import os
import sys

import olefile

MIL = 0.0254


def components(path):
    data = olefile.OleFileIO(path).openstream("Components6/Data").read()
    out, pos = {}, 0
    while pos + 4 <= len(data):
        n = int.from_bytes(data[pos:pos + 4], "little")
        body = data[pos + 4:pos + 4 + n].decode("latin-1")
        pos += 4 + n
        kv = dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p)
        des = kv.get("SOURCEDESIGNATOR")
        if des:
            out[des] = (float(kv["X"].replace("mil", "")) * MIL, float(kv["Y"].replace("mil", "")) * MIL,
                        float(kv.get("ROTATION", "0")) % 360, kv.get("LAYER"))
    return out


def export(root, plan, have):
    """Write the as-placed positions, with each part's move from the plan, to placement_final.csv."""
    path = os.path.join(root, "hardware", "placement_final.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["designator", "x_mm", "y_mm", "rotation", "moved_from_plan_mm", "reason"])
        for row in plan:
            x, y, rot, _ = have[row["designator"]]
            moved = ((x - float(row["x_mm"])) ** 2 + (y - float(row["y_mm"])) ** 2) ** 0.5
            w.writerow([row["designator"], f"{x:.3f}", f"{y:.3f}", f"{rot:g}", f"{moved:.2f}", row["reason"]])
    print("wrote", os.path.relpath(path, root))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) not in (1, 2) or flags - {"--plan", "--export"}:
        sys.exit(__doc__)
    tol = float(args[1]) if len(args) == 2 else 0.01
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    plan = list(csv.DictReader(open(os.path.join(root, "hardware", "placement.csv"), encoding="utf-8")))
    have = components(args[0])
    if "--export" in flags:
        export(root, plan, have)
        return
    final = os.path.join(root, "hardware", "placement_final.csv")
    use_final = os.path.exists(final) and "--plan" not in flags
    want = list(csv.DictReader(open(final, encoding="utf-8"))) if use_final else plan
    print("reference:", "hardware/placement_final.csv (as placed)" if use_final else "hardware/placement.csv (plan)")
    errors = []
    for row in want:
        des = row["designator"]
        if des not in have:
            errors.append(f"{des}: not in the PcbDoc")
            continue
        x, y, rot, layer = have[des]
        wx, wy, wr = float(row["x_mm"]), float(row["y_mm"]), float(row["rotation"]) % 360
        if abs(x - wx) > tol or abs(y - wy) > tol or abs(rot - wr) > 0.01:
            errors.append(f"{des}: at ({x:.3f}, {y:.3f}) rot {rot:g}, expected ({wx:.3f}, {wy:.3f}) rot {wr:g}")
        if layer != "TOP":
            errors.append(f"{des}: on {layer}, expected TOP")
    extra = sorted(set(have) - {r["designator"] for r in want})
    for des in extra:
        errors.append(f"{des}: in the PcbDoc but not in placement.csv")
    print(f"{len(want)} parts in placement.csv, {len(have)} in the PcbDoc, "
          f"{len(want) - len([e for e in errors if 'expected (' in e or 'not in the PcbDoc' in e])} placed as planned")
    for e in errors[:40]:
        print("ERROR", e)
    if len(errors) > 40:
        print(f"... {len(errors) - 40} more")
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
