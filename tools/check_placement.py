"""Check component positions in the PcbDoc against hardware/placement.csv.

Compares every designator's X, Y (mm from the board origin) and rotation with the JEDEC-derived
placement written by tools/gen_placement.py.

Usage:
    py -3.11 tools/check_placement.py <board.PcbDoc> [tolerance_mm]
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


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    tol = float(sys.argv[2]) if len(sys.argv) == 3 else 0.01
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    want = list(csv.DictReader(open(os.path.join(root, "hardware", "placement.csv"), encoding="utf-8")))
    have = components(sys.argv[1])
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
