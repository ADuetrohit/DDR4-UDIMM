"""Minimal reader for Altium PcbLib footprints (pads, tracks, arcs, fills).

A PcbLib is an OLE compound file; each footprint has a '<name>/Data' stream holding
binary primitive records. Layouts follow KiCad's Altium importer (altium_parser_pcb.cpp).
Coordinates are returned in mm, relative to the footprint origin, y pointing up.

Usage:
    py -3.11 tools/pcblib.py <lib.PcbLib>              # list footprints
    py -3.11 tools/pcblib.py <lib.PcbLib> <footprint>  # dump its primitives
"""
import struct
import sys

import olefile

UNIT = 0.0254 / 10000          # Altium internal unit (1/10000 mil) in mm
SUBRECORDS = {1: 1, 2: 6, 3: 1, 4: 1, 5: 2, 6: 1, 11: 1, 12: 1}
LAYERS = {1: "Top", 32: "Bottom", 33: "TopOverlay", 34: "BottomOverlay", 35: "TopPaste",
          36: "BottomPaste", 37: "TopSolder", 38: "BottomSolder", 56: "KeepOut", 74: "MultiLayer",
          **{56 + i: f"Mechanical{i}" for i in range(1, 17)}}
MASK_MODE = {0: "none", 1: "rule", 2: "manual"}


def _mm(v):
    return round(v * UNIT, 4)


def _layer(b):
    return LAYERS.get(b, f"L{b}")


def footprints(path):
    ole = olefile.OleFileIO(path)
    return sorted({e[0] for e in ole.listdir() if len(e) == 2 and e[1] == "Data" and e[0] != "Library"
                   and e[0] != "FileVersionInfo"})


def _stream_name(ole, name):
    # stream names are cut to 31 characters; the full name is in <stream>/Parameters
    for e in ole.listdir():
        if len(e) == 2 and e[1] == "Parameters":
            params = ole.openstream(e).read().decode("latin-1")
            if f"|PATTERN={name}|" in params + "|" or e[0] == name:
                return e[0]
    raise KeyError(f"footprint {name!r} not found")


def read(path, name):
    ole = olefile.OleFileIO(path)
    data = ole.openstream(_stream_name(ole, name) + "/Data").read()
    pos = 4 + struct.unpack_from("<I", data, 0)[0]        # skip the name block
    prims = []
    while pos < len(data):
        rtype = data[pos]
        pos += 1
        subs = []
        for _ in range(SUBRECORDS.get(rtype, 1)):
            n = struct.unpack_from("<I", data, pos)[0]
            subs.append(data[pos + 4: pos + 4 + n])
            pos += 4 + n
        prims.append(_decode(rtype, subs))
    return prims


def _decode(rtype, subs):
    if rtype == 2:                                         # pad
        name = subs[0][1:1 + subs[0][0]].decode("latin-1")
        s = subs[4]
        x, y, tx, ty, mx, my, bx, by, hole = struct.unpack_from("<9i", s, 13)
        top_shape, mid_shape, bot_shape = s[49], s[50], s[51]
        rot = struct.unpack_from("<d", s, 52)[0]
        paste, solder = struct.unpack_from("<2i", s, 86)
        paste_mode, solder_mode = s[101], s[102]
        return {"type": "pad", "name": name, "layer": _layer(s[0]), "x": _mm(x), "y": _mm(y),
                "w": _mm(tx), "h": _mm(ty), "bot_w": _mm(bx), "bot_h": _mm(by), "hole": _mm(hole),
                "shape": top_shape, "rot": round(rot, 3),
                "paste": _mm(paste), "paste_mode": MASK_MODE.get(paste_mode, paste_mode),
                "solder": _mm(solder), "solder_mode": MASK_MODE.get(solder_mode, solder_mode)}
    s = subs[0]
    if rtype == 4:                                         # track
        x1, y1, x2, y2, w = struct.unpack_from("<5i", s, 13)
        return {"type": "track", "layer": _layer(s[0]), "x1": _mm(x1), "y1": _mm(y1),
                "x2": _mm(x2), "y2": _mm(y2), "w": _mm(w)}
    if rtype == 1:                                         # arc
        cx, cy, r = struct.unpack_from("<3i", s, 13)
        a0, a1 = struct.unpack_from("<2d", s, 25)
        w = struct.unpack_from("<i", s, 41)[0]
        return {"type": "arc", "layer": _layer(s[0]), "cx": _mm(cx), "cy": _mm(cy), "r": _mm(r),
                "a0": round(a0, 3), "a1": round(a1, 3), "w": _mm(w)}
    if rtype == 6:                                         # fill
        x1, y1, x2, y2 = struct.unpack_from("<4i", s, 13)
        return {"type": "fill", "layer": _layer(s[0]), "x1": _mm(x1), "y1": _mm(y1),
                "x2": _mm(x2), "y2": _mm(y2), "rot": round(struct.unpack_from("<d", s, 29)[0], 3)}
    names = {3: "via", 5: "text", 11: "region", 12: "body"}
    return {"type": names.get(rtype, f"record{rtype}"), "layer": _layer(s[0]) if s else None}


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print("\n".join(footprints(sys.argv[1])))
    else:
        for p in read(sys.argv[1], sys.argv[2]):
            print(p)
