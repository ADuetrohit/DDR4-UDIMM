"""Check the 288-pin edge-connector symbol in an Altium .SchLib against the JEDEC pinout.

Compares every pin (number, name, part, electrical type, side, description) with
hardware/libraries/edge_connector/*.tsv produced by gen_edge_connector.py.

Usage:
    py -3.11 tools/check_edge_symbol.py <library.SchLib> [component storage name]
"""
import csv
import glob
import os
import struct
import sys

import olefile

ELECTRICAL = {0: "Input", 1: "I/O", 2: "Output", 3: "Open Collector", 4: "Passive",
              5: "HiZ", 6: "Open Emitter", 7: "Power"}
PART_LETTER = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}


def pascal(buf, i):
    n = buf[i]
    return buf[i + 1:i + 1 + n].decode("latin-1"), i + 1 + n


def read_binary_pins(data):
    """Decode Altium's binary pin records (record header type byte = 1)."""
    pins, i = [], 0
    while i + 4 <= len(data):
        hdr = struct.unpack_from("<I", data, i)[0]
        ln, typ = hdr & 0xFFFFFF, hdr >> 24
        rec = data[i + 4:i + 4 + ln]
        i += 4 + ln
        if typ != 1 or struct.unpack_from("<i", rec, 0)[0] != 2:
            continue
        part = struct.unpack_from("<h", rec, 5)[0]
        desc, j = pascal(rec, 12)
        etype = rec[j + 1]
        conglom = rec[j + 2]
        length, x, y = struct.unpack_from("<hhh", rec, j + 3)
        name, k = pascal(rec, j + 13)
        desig, k = pascal(rec, k)
        pins.append({"part": part, "desc": desc, "etype": ELECTRICAL.get(etype, str(etype)),
                     "orient": conglom & 3, "x": x, "y": y, "name": name, "pin": desig})
    return pins


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ole = olefile.OleFileIO(sys.argv[1])
    comps = sorted({e[0] for e in ole.listdir() if len(e) == 2 and e[1] == "Data"})
    comp = sys.argv[2] if len(sys.argv) > 2 else comps[0]
    pins = read_binary_pins(ole.openstream(f"{comp}/Data").read())

    here = os.path.dirname(os.path.abspath(__file__))
    expected = {}
    order = {}
    for path in sorted(glob.glob(os.path.join(here, "..", "hardware", "libraries", "edge_connector", "symbol_wizard_part_*.tsv"))):
        letter = path[-5]
        with open(path, encoding="utf-8", newline="") as f:
            for idx, row in enumerate(csv.reader(f, delimiter="\t")):
                group, name, pin, etype, desc, side = row
                expected[pin] = {"part": letter, "name": name, "etype": etype, "desc": desc, "side": side}
                order.setdefault((letter, side), []).append(pin)

    fails, seen = [], {}
    for p in pins:
        seen.setdefault(p["pin"], 0)
        seen[p["pin"]] += 1
        e = expected.get(p["pin"])
        if not e:
            fails.append(f"pin {p['pin']} ({p['name']}) is not a JEDEC pin number")
            continue
        side = "Left" if p["orient"] == 2 else "Right" if p["orient"] == 0 else f"orient{p['orient']}"
        got = {"part": PART_LETTER.get(p["part"], str(p["part"])), "name": p["name"],
               "etype": p["etype"], "desc": p["desc"], "side": side}
        for key in ("part", "name", "etype", "desc", "side"):
            if got[key] != e[key]:
                fails.append(f"pin {p['pin']}: {key} is '{got[key]}', expected '{e[key]}'")
    for pin, n in seen.items():
        if n > 1:
            fails.append(f"pin {pin} appears {n} times")
    missing = sorted(set(expected) - set(seen), key=int)
    if missing:
        fails.append(f"missing pins: {missing}")

    # cosmetic: does each side read top-to-bottom in the intended order?
    notes = []
    for (letter, side), want in sorted(order.items()):
        placed = sorted((p for p in pins if PART_LETTER.get(p["part"]) == letter and
                         ("Left" if p["orient"] == 2 else "Right") == side), key=lambda p: -p["y"])
        got_order = [p["pin"] for p in placed]
        wanted = want if side == "Left" else want[::-1]
        if got_order != wanted:
            if got_order == wanted[::-1]:
                notes.append(f"Part {letter} {side}: reads bottom-to-top (cosmetic only)")
            else:
                notes.append(f"Part {letter} {side}: pin order differs from the table (cosmetic only)")

    parts = sorted({PART_LETTER.get(p["part"], p["part"]) for p in pins})
    print(f"Component '{comp}': {len(pins)} pins in parts {parts}")
    for n in notes:
        print("  NOTE:", n)
    print(f"Pins checked: {len(pins)}, failures: {len(fails)}")
    for f in fails:
        print("  FAIL:", f)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
