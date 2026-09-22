"""Measure routed trace lengths per net from the PcbDoc, JEDEC style.

Sums every track and arc of each net and reports physical length, width and layers, plus the
velocity-compensated stripline-equivalent length used by JESD21-C 4.20.26 §6.3.4: microstrip
(outer layers L1/L8) length / 1.1 + stripline (inner layers) length. Vias are not included.

For each byte lane that has routing it also lists the finger-side halves (finger -> 15 ohm), the
segment Annex A calls TL0 (3.1-6.0 mm for Raw Card A3).

Usage:
    py -3.11 tools/check_lengths.py <board.PcbDoc> [net ...]      # listed nets, or every routed net
"""
import math
import struct
import sys

import olefile

UNIT = 0.0254 / 10000                  # Altium internal unit in mm
OUTER = {1: "L1", 32: "L8"}            # microstrip layers (Altium layer ids)
INNER = {2: "L2", 3: "L3", 4: "L4", 5: "L5", 6: "L6", 7: "L7"}


def nets(ole):
    data = ole.openstream("Nets6/Data").read()
    out, pos = [], 0
    while pos + 4 <= len(data):
        n = int.from_bytes(data[pos:pos + 4], "little")
        body = data[pos + 4:pos + 4 + n].decode("latin-1")
        pos += 4 + n
        out.append(dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p).get("NAME"))
    return out


def segments(ole, names):
    """Yield (net, layer id, length mm, width mm) for every track and arc with a net."""
    for stream, kind in (("Tracks6/Data", "track"), ("Arcs6/Data", "arc")):
        if not ole.exists(stream):
            continue
        data, pos = ole.openstream(stream).read(), 0
        while pos < len(data):
            pos += 1
            n = struct.unpack_from("<I", data, pos)[0]
            r = data[pos + 4:pos + 4 + n]
            pos += 4 + n
            net = struct.unpack_from("<H", r, 3)[0]
            if net >= len(names):
                continue
            if kind == "track":
                x1, y1, x2, y2, w = struct.unpack_from("<5i", r, 13)
                length = math.hypot(x2 - x1, y2 - y1) * UNIT
            else:
                _, _, rad = struct.unpack_from("<3i", r, 13)
                a0, a1 = struct.unpack_from("<2d", r, 25)
                w = struct.unpack_from("<i", r, 41)[0]
                length = rad * UNIT * math.radians((a1 - a0) % 360)
            yield names[net], r[0], length, w * UNIT


def measure(path):
    ole = olefile.OleFileIO(path)
    out = {}
    for net, layer, length, width in segments(ole, nets(ole)):
        m = out.setdefault(net, {"len": 0.0, "comp": 0.0, "layers": set(), "widths": set()})
        m["len"] += length
        m["comp"] += length / 1.1 if layer in OUTER else length
        m["layers"].add(OUTER.get(layer) or INNER.get(layer) or f"id{layer}")
        m["widths"].add(round(width, 3))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    m = measure(sys.argv[1])
    wanted = sys.argv[2:] or sorted(m)
    print(f"{'net':12} {'length':>8} {'comp.':>8}  layers   widths (mm)")
    for net in wanted:
        if net not in m:
            print(f"{net:12} not routed")
            continue
        x = m[net]
        print(f"{net:12} {x['len']:8.3f} {x['comp']:8.3f}  {','.join(sorted(x['layers'])):8} "
              f"{', '.join(map(str, sorted(x['widths'])))}")

    for k in range(8):                                 # byte lanes: finger -> 15 ohm (TL0)
        names = [f"DQ{8 * k + j}" for j in range(8)] + [f"DQS{k}_T", f"DQS{k}_C", f"DM{k}"]
        if not any(n in m for n in names):
            continue
        print(f"\nByte {k}: finger -> 15 ohm (TL0), compensated mm: "
              + ", ".join(f"{n} {m[n]['comp']:.2f}" for n in names if n in m))
    return 0


if __name__ == "__main__":
    main()
