"""Render the saved PcbDoc to a PNG, top view, straight from the board file.

Draws the board outline, copper tracks and arcs on the chosen layers, vias, pads and the silkscreen,
so a picture of the layout can be produced without opening Altium.

Usage:
    py -3.11 tools/render_board.py <board.PcbDoc> <out.png> [--box x1,y1,x2,y2] [--dpi 300]
                                   [--layers L1,L3,L8] [--silk] [--light]
"""
import math
import os
import struct
import sys

import olefile
import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcblib                                     # noqa: E402

UNIT = 0.0254 / 10000
MM = 72.0 / 25.4                                  # PDF points per mm

# Altium-like layer colours: L1 red, inner layers, L8 blue
COPPER = {1: (0.84, 0.10, 0.10), 2: (0.45, 0.45, 0.45), 3: (0.35, 0.78, 0.90),
          4: (0.55, 0.40, 0.75), 5: (0.95, 0.60, 0.20), 6: (0.30, 0.75, 0.45),
          7: (0.80, 0.35, 0.60), 32: (0.20, 0.35, 0.90)}
NAMES = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6, "L7": 7, "L8": 32}
SILK, MULTI = 33, 74
PAD = (0.78, 0.74, 0.55)
VIA = (0.62, 0.62, 0.62)


def records(ole, stream, unpack):
    data, pos, out = ole.openstream(stream).read(), 0, []
    while pos < len(data):
        pos += 1
        n = struct.unpack_from("<I", data, pos)[0]
        r = data[pos + 4:pos + 4 + n]
        pos += 4 + n
        out.append(unpack(r))
    return out


def geometry(path):
    ole = olefile.OleFileIO(path)
    txt = ole.openstream("Board6/Data").read().decode("latin-1")
    board = dict(p.split("=", 1) for p in txt.strip("\x00").split("|") if "=" in p)

    def mm(v):
        return float(v.replace("mil", "")) * 0.0254

    n = 0
    while f"VX{n}" in board:
        n += 1
    outline = [(mm(board[f"VX{i}"]), mm(board[f"VY{i}"])) for i in range(n)]

    tracks = records(ole, "Tracks6/Data", lambda r: (
        r[0], *(v * UNIT for v in struct.unpack_from("<5i", r, 13))))
    arcs = records(ole, "Arcs6/Data", lambda r: (
        r[0], *(v * UNIT for v in struct.unpack_from("<3i", r, 13)),
        *struct.unpack_from("<2d", r, 25), struct.unpack_from("<i", r, 41)[0] * UNIT))
    vias = records(ole, "Vias6/Data", lambda r: tuple(
        v * UNIT for v in struct.unpack_from("<3i", r, 13)))

    pads, data, pos = [], ole.openstream("Pads6/Data").read(), 0
    while pos < len(data):
        t = data[pos]
        pos += 1
        subs = []
        for _ in range(pcblib.SUBRECORDS.get(t, 1)):
            ln = struct.unpack_from("<I", data, pos)[0]
            subs.append(data[pos + 4:pos + 4 + ln])
            pos += 4 + ln
        p = pcblib._decode(t, subs)
        w, h = p["w"], p["h"]
        if round(p["rot"]) % 180 == 90:
            w, h = h, w
        pads.append((subs[4][0], p["x"], p["y"], w, h))
    return outline, tracks, arcs, vias, pads


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args else default

    dpi = int(opt("--dpi", "300"))
    layers = [NAMES[s] for s in opt("--layers", "L1,L3,L8").split(",")]
    silk = "--silk" in args
    bg = (1, 1, 1) if "--light" in args else (0.04, 0.04, 0.06)

    outline, tracks, arcs, vias, pads = geometry(src)
    if opt("--box"):
        x1, y1, x2, y2 = (float(v) for v in opt("--box").split(","))
    else:
        xs, ys = [p[0] for p in outline], [p[1] for p in outline]
        x1, y1, x2, y2 = min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1

    doc = pymupdf.open()
    page = doc.new_page(width=(x2 - x1) * MM, height=(y2 - y1) * MM)

    def P(x, y):                                  # board mm -> page points, y flipped
        return pymupdf.Point((x - x1) * MM, (y2 - y) * MM)

    page.draw_rect(page.rect, color=bg, fill=bg)

    sh = page.new_shape()                         # board outline
    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        sh.draw_line(P(ax, ay), P(bx, by))
    sh.finish(color=(0.55, 0.85, 0.35), width=0.6)
    sh.commit()

    order = [ln for ln in (32, 7, 6, 5, 4, 3, 2, 1) if ln in layers]
    for ln in order:
        col = COPPER[ln]
        groups = {}                               # width -> list of polylines, one shape per width
        for lay, ax, ay, bx, by, w in tracks:
            if lay == ln:
                groups.setdefault(round(w, 4), []).append([(ax, ay), (bx, by)])
        for lay, cx, cy, r, sa, ea, w in arcs:
            if lay == ln:
                steps = max(3, int(abs(ea - sa) / 6) + 1)
                groups.setdefault(round(w, 4), []).append(
                    [(cx + r * math.cos(math.radians(sa + (ea - sa) * i / steps)),
                      cy + r * math.sin(math.radians(sa + (ea - sa) * i / steps)))
                     for i in range(steps + 1)])
        for w, polys in groups.items():
            sh = page.new_shape()
            for poly in polys:
                for a, b in zip(poly, poly[1:]):
                    sh.draw_line(P(*a), P(*b))
            sh.finish(color=col, width=max(w * MM, 0.3), lineCap=1, lineJoin=1)
            sh.commit()

    sh = page.new_shape()                         # pads (multi-layer and the drawn layers)
    for lay, x, y, w, h in pads:
        if lay == MULTI or lay in layers:
            sh.draw_rect(pymupdf.Rect(P(x - w / 2, y + h / 2), P(x + w / 2, y - h / 2)))
    sh.finish(color=None, fill=PAD)
    sh.commit()

    sh = page.new_shape()                         # vias
    for x, y, d in vias:
        sh.draw_circle(P(x, y), d / 2 * MM)
    sh.finish(color=None, fill=VIA)
    sh.commit()

    if silk:
        sh = page.new_shape()
        for lay, ax, ay, bx, by, w in tracks:
            if lay == SILK:
                sh.draw_line(P(ax, ay), P(bx, by))
        sh.finish(color=(0.85, 0.85, 0.85), width=0.3)
        sh.commit()

    page.get_pixmap(dpi=dpi).save(out)
    print(f"{out}: {(x2 - x1):.1f} x {(y2 - y1):.1f} mm at {dpi} dpi, layers {opt('--layers', 'L1,L3,L8')}")


if __name__ == "__main__":
    main()
