"""Extract the netlist from an Altium .SchDoc (binary) file.

Reads components, pins, wires, junctions, net labels and power ports, and
joins them geometrically the way Altium does, so a schematic can be checked
without exporting a netlist from Altium.

Usage:
    py -3.11 tools/schdoc_nets.py <file.SchDoc>            # print every net
    py -3.11 tools/schdoc_nets.py <file.SchDoc> --json     # machine-readable

Requires: py -3.11 -m pip install --user olefile
"""
import json
import struct
import sys
from collections import defaultdict

import olefile

UNIT = 10  # Altium stores coordinates in units of 10 mil


def read_records(path):
    data = olefile.OleFileIO(path).openstream("FileHeader").read()
    recs, i = [], 0
    while i + 4 <= len(data):
        ln = struct.unpack_from("<I", data, i)[0] & 0xFFFFFF
        i += 4
        raw = data[i:i + ln].rstrip(b"\x00").decode("latin-1", "replace")
        i += ln
        if raw.startswith("|"):
            recs.append({k.upper(): v for k, v in
                         (kv.split("=", 1) for kv in raw.strip("|").split("|") if "=" in kv)})
    return recs


def coord(rec, key):
    whole = int(rec.get(key, "0") or 0)
    frac = int(rec.get(key + "_FRAC", "0") or 0)
    return whole * UNIT + frac * UNIT / 100000.0


def pt(rec, xk="LOCATION.X", yk="LOCATION.Y"):
    return (round(coord(rec, xk), 3), round(coord(rec, yk), 3))


def on_segment(p, a, b, tol=0.5):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if min(ax, bx) - tol <= px <= max(ax, bx) + tol and min(ay, by) - tol <= py <= max(ay, by) + tol:
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        length = max(abs(bx - ax), abs(by - ay), 1e-9)
        return abs(cross) / length <= tol
    return False


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def extract(path):
    recs = read_records(path)
    body = recs[1:]  # record 0 is the sheet header; OWNERINDEX counts from here

    comps = {}
    for idx, r in enumerate(body):
        if r.get("RECORD") == "1":
            comps[idx] = {"part": r.get("CURRENTPARTID", "1"), "mode": r.get("DISPLAYMODE") or "0",
                          "designator": "?", "comment": "",
                          "lib": r.get("LIBREFERENCE", ""), "desc": r.get("COMPONENTDESCRIPTION", "")}
    for r in body:
        owner = int(r.get("OWNERINDEX", "-1") or -1)
        if owner in comps and r.get("RECORD") == "34":
            comps[owner]["designator"] = r.get("TEXT", "?")
        if owner in comps and r.get("RECORD") == "41" and r.get("NAME", "").lower() == "comment":
            comps[owner]["comment"] = r.get("TEXT", "")

    # Pins: keep only the pins of the part and display mode actually placed
    pins = []
    for r in body:
        if r.get("RECORD") != "2":
            continue
        owner = int(r.get("OWNERINDEX", "-1") or -1)
        if owner not in comps or r.get("OWNERPARTID", "1") != comps[owner]["part"]:
            continue
        if (r.get("OWNERPARTDISPLAYMODE") or "0") != comps[owner]["mode"]:
            continue  # pin belongs to an alternate graphical mode that isn't displayed
        base = pt(r)
        length = coord(r, "PINLENGTH")
        orient = int(r.get("PINCONGLOMERATE", "0") or 0) & 3
        dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][orient]
        tip = (round(base[0] + dx * length, 3), round(base[1] + dy * length, 3))
        pins.append({"owner": owner, "pin": r.get("DESIGNATOR", "?"), "name": r.get("NAME", ""),
                     "ends": (base, tip)})

    wires = []
    for r in body:
        if r.get("RECORD") == "27":
            n = int(r.get("LOCATIONCOUNT", "0") or 0)
            wires.append([pt(r, f"X{k}", f"Y{k}") for k in range(1, n + 1)])

    labels = [(r.get("TEXT", ""), pt(r)) for r in body if r.get("RECORD") == "25"]
    power = [(r.get("TEXT", ""), pt(r)) for r in body if r.get("RECORD") == "17"]
    sheet_ports = [(r.get("NAME", ""), pt(r)) for r in body if r.get("RECORD") == "18"]
    junctions = [pt(r) for r in body if r.get("RECORD") == "29"]
    noerc = [pt(r) for r in body if r.get("RECORD") == "22"]

    dsu = DSU()
    segs = []
    for wi, w in enumerate(wires):
        for a, b in zip(w, w[1:]):
            segs.append((wi, a, b))
        for v in w:
            dsu.union(("w", wi), ("w", wi))

    def wires_at(p):
        return {wi for wi, a, b in segs if on_segment(p, a, b)}

    # wire-to-wire: a vertex of one wire touching another wire, or a junction on both
    for wi, w in enumerate(wires):
        for v in (w[0], w[-1]):
            for wj in wires_at(v):
                dsu.union(("w", wi), ("w", wj))
    for j in junctions:
        hit = list(wires_at(j))
        for wj in hit[1:]:
            dsu.union(("w", hit[0]), ("w", wj))

    # pins: whichever end touches a wire is the electrical end
    for k, p in enumerate(pins):
        touched = False
        for end in p["ends"]:
            for wj in wires_at(end):
                dsu.union(("p", k), ("w", wj))
                touched = True
        p["wired"] = touched
    # pin-to-pin direct contact
    for a in range(len(pins)):
        for b in range(a + 1, len(pins)):
            if set(pins[a]["ends"]) & set(pins[b]["ends"]):
                dsu.union(("p", a), ("p", b))

    names = defaultdict(set)
    for kind, items in (("label", labels), ("power", power), ("port", sheet_ports)):
        for text, p in items:
            node = (kind, text, p)
            hit = wires_at(p)
            for wj in hit:
                dsu.union(node, ("w", wj))
            for k, pin in enumerate(pins):
                if p in pin["ends"]:
                    dsu.union(node, ("p", k))
            names[text].add(node)
    # same name = same net (global scope)
    for text, nodes in names.items():
        nodes = list(nodes)
        for n in nodes[1:]:
            dsu.union(nodes[0], n)

    # No-ERC markers apply to whatever they touch: a pin end or any point on a wire
    noerc_nodes = []
    for p in noerc:
        node = ("noerc", p)
        for wj in wires_at(p):
            dsu.union(node, ("w", wj))
        for k, pin in enumerate(pins):
            if p in pin["ends"]:
                dsu.union(node, ("p", k))
        noerc_nodes.append(node)

    nets = defaultdict(lambda: {"names": set(), "pins": [], "noerc": False})
    for k, p in enumerate(pins):
        c = comps[p["owner"]]
        ref = f'{c["designator"]}#{p["owner"]}'
        nets[dsu.find(("p", k))]["pins"].append(
            {"ref": ref, "comment": c["comment"], "pin": p["pin"], "name": p["name"]})
    for text, nodes in names.items():
        for n in nodes:
            nets[dsu.find(n)]["names"].add(text)

    for node in noerc_nodes:
        root = dsu.find(node)
        if root in nets:
            nets[root]["noerc"] = True

    near_noerc = {k for k, p in enumerate(pins) if any(e in noerc for e in p["ends"])}
    result = []
    for key, net in nets.items():
        result.append({"names": sorted(net["names"]), "pins": net["pins"], "noerc": net["noerc"]})
    return {"nets": result, "components": comps, "pins": pins, "noerc_pins": near_noerc,
            "sheet_ports": sheet_ports}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    res = extract(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(res["nets"], indent=1))
        return
    for net in sorted(res["nets"], key=lambda n: (",".join(n["names"]) or "~", len(n["pins"]))):
        label = ",".join(net["names"]) or "(unnamed)"
        members = ", ".join(f'{m["ref"]}[{m["comment"]}].{m["pin"]}({m["name"]})' for m in net["pins"])
        print(f"{label:<14} {members}")


if __name__ == "__main__":
    main()
