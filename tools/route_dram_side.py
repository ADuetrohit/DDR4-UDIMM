"""Route the DRAM side of chosen data lines (15 ohm resistor pad 1 -> DRAM fan-out via) and write an
Altium script that draws them.

Reads every track, via and pad from the saved PcbDoc, then routes each requested net with a small
grid router (0.025 mm grid, 0/45/90 degree moves only): top layer L1 from the resistor's pad 1, one
through via, then the chosen layer (L8 bottom by default) into the net's existing fan-out via at the
DRAM. Every new track keeps at least CLEAR mm (edge to edge) from other nets on its layer, and every
new via keeps CLEAR from everything on all layers. Existing routing is never changed.

Usage:
    py -3.11 tools/route_dram_side.py <board.PcbDoc> <script name> NET[:LAYER] ...
    e.g. py -3.11 tools/route_dram_side.py board.PcbDoc U1_Finish NetR2_1:L8 NetR6_1:L8
Writes hardware/scripts/<script name>.pas (+ .PrjScr).
"""
import heapq
import math
import os
import struct
import sys

import olefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcblib                                     # noqa: E402

UNIT = 0.0254 / 10000
GRID = 0.025
CLEAR = 0.15                  # mm edge-to-edge (rules: 0.10 general, 0.125 track-pad) - extra margin
WIDTH = 0.10
VIA_D, VIA_HOLE = 0.40, 0.20
LAYER_ID = {"L1": 1, "L3": 3, "L8": 32}
PAS_LAYER = {"L1": "eTopLayer", "L3": "eMidLayer2", "L8": "eBottomLayer"}


def streams(path):
    ole = olefile.OleFileIO(path)

    def text_records(name):
        data, out, pos = ole.openstream(name).read(), [], 0
        while pos + 4 <= len(data):
            n = int.from_bytes(data[pos:pos + 4], "little")
            body = data[pos + 4:pos + 4 + n].decode("latin-1")
            pos += 4 + n
            out.append(dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p))
        return out

    nets = [r.get("NAME") for r in text_records("Nets6/Data")]
    comps = [r.get("SOURCEDESIGNATOR") for r in text_records("Components6/Data")]

    tracks, vias, pads = [], [], []
    for stream in ("Tracks6/Data", "Vias6/Data"):
        data, pos = ole.openstream(stream).read(), 0
        while pos < len(data):
            pos += 1
            n = struct.unpack_from("<I", data, pos)[0]
            r = data[pos + 4:pos + 4 + n]
            pos += 4 + n
            ni = struct.unpack_from("<H", r, 3)[0]
            net = nets[ni] if ni < len(nets) else None
            if stream.startswith("Tracks"):
                x1, y1, x2, y2, w = (v * UNIT for v in struct.unpack_from("<5i", r, 13))
                tracks.append((net, r[0], (x1, y1), (x2, y2), w))
            else:
                x, y, d = (v * UNIT for v in struct.unpack_from("<3i", r, 13))
                vias.append((net, (x, y), d))
    data, pos = ole.openstream("Pads6/Data").read(), 0
    while pos < len(data):
        t = data[pos]
        pos += 1
        subs = []
        for _ in range(pcblib.SUBRECORDS.get(t, 1)):
            n = struct.unpack_from("<I", data, pos)[0]
            subs.append(data[pos + 4:pos + 4 + n])
            pos += 4 + n
        p = pcblib._decode(t, subs)
        ni, ci = struct.unpack_from("<H", subs[4], 3)[0], struct.unpack_from("<H", subs[4], 7)[0]
        w, h = p["w"], p["h"]
        if round(p["rot"]) % 180 == 90:
            w, h = h, w
        pads.append((nets[ni] if ni < len(nets) else None, comps[ci] if ci < len(comps) else None,
                     p["name"], subs[4][0], (p["x"], p["y"]), w, h))
    return tracks, vias, pads


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def rect_dist(p, c, w, h):
    dx = max(abs(p[0] - c[0]) - w / 2, 0.0)
    dy = max(abs(p[1] - c[1]) - h / 2, 0.0)
    return math.hypot(dx, dy)


class Board:
    def __init__(self, tracks, vias, pads):
        self.tracks, self.vias, self.pads = tracks, vias, pads

    def clear_on(self, p, layer, net, radius):
        """Distance-based check: a disc of `radius` at p on `layer` stays CLEAR from other nets."""
        lid = LAYER_ID[layer]
        for n, lay, a, b, w in self.tracks:
            if n != net and lay == lid and seg_dist(p, a, b) < radius + w / 2 + CLEAR:
                return False
        for n, c, d in self.vias:
            if n != net and math.dist(p, c) < radius + d / 2 + CLEAR:
                return False
        for n, _, _, lay, c, w, h in self.pads:
            on = lay == 74 or (lay == 1 and lid == 1) or (lay == 32 and lid == 32)
            if on and n != net and rect_dist(p, c, w, h) < radius + CLEAR:
                return False
        return True

    def via_ok(self, p, net):
        """A through via touches every layer: check tracks on all layers, all vias and all pads."""
        r = VIA_D / 2
        for n, _, a, b, w in self.tracks:
            if n != net and seg_dist(p, a, b) < r + w / 2 + CLEAR:
                return False
        for n, c, d in self.vias:
            if n != net and math.dist(p, c) < r + d / 2 + CLEAR:
                return False
        for n, _, _, lay, c, w, h in self.pads:
            if n != net and rect_dist(p, c, w, h) < r + CLEAR:
                return False
        return p[1] > 6.0                          # keep vias out of the finger area


def route(board, net, start, goal, layer2, box):
    """A* from start (on L1) to goal (on layer2) with one via; returns [(layer, [points]), ...], vias."""
    x0, y0, x1, y1 = box
    to_g = lambda v: int(round(v / GRID))
    s, g = (to_g(start[0]), to_g(start[1]), "L1"), (to_g(goal[0]), to_g(goal[1]), layer2)
    cache = {}

    def free(ix, iy, lay):
        key = (ix, iy, lay)
        if key not in cache:
            p = (ix * GRID, iy * GRID)
            cache[key] = (x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and board.clear_on(p, lay, net, WIDTH / 2))
        return cache[key]

    vcache = {}

    def via_here(ix, iy):
        if (ix, iy) not in vcache:
            vcache[(ix, iy)] = board.via_ok((ix * GRID, iy * GRID), net)
        return vcache[(ix, iy)]

    moves = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    h = lambda n: math.hypot(n[0] - g[0], n[1] - g[1]) + (0 if n[2] == layer2 else 16)
    tick = 0                                        # tie-breaker so heap entries never compare directions
    openq = [(h(s), 0.0, tick, s, None)]
    came, best = {}, {(s, None): 0.0}
    while openq:
        f, cost, _, node, d = heapq.heappop(openq)
        if (node, d) in came and best.get((node, d), 1e9) < cost - 1e-9:
            continue
        if node == g:
            path, key = [node], (node, d)
            while key in came:
                key = came[key]
                path.append(key[0])
            return path[::-1]
        ix, iy, lay = node
        nxt = []
        for mv in moves:
            n2 = (ix + mv[0], iy + mv[1], lay)
            if n2[:2] == g[:2] and lay == layer2 or free(*n2) or (n2[:2] == s[:2] and lay == "L1"):
                step = math.hypot(*mv) + (0.4 if d is not None and mv != d else 0.0)
                nxt.append((n2, mv, step))
        if lay == "L1" and via_here(ix, iy):
            nxt.append(((ix, iy, layer2), None, 16.0))
        for n2, mv, step in nxt:
            c2 = cost + step
            if c2 < best.get((n2, mv), 1e9):
                best[(n2, mv)] = c2
                came[(n2, mv)] = (node, d)
                tick += 1
                heapq.heappush(openq, (c2 + h(n2), c2, tick, n2, mv))
    return None


def to_segments(path):
    """Grid path -> [(layer, (x1,y1), (x2,y2))] merged into straight runs, plus via points."""
    segs, vias = [], []
    run = [path[0]]
    for a, b in zip(path, path[1:]):
        if a[2] != b[2]:
            vias.append((a[0] * GRID, a[1] * GRID))
            if len(run) > 1:
                segs.append(run)
            run = [b]
            continue
        if len(run) >= 2:
            d1 = (run[-1][0] - run[-2][0], run[-1][1] - run[-2][1])
            d2 = (b[0] - a[0], b[1] - a[1])
            if d1 != d2:
                segs.append(run)
                run = [a]
        run.append(b)
    if len(run) > 1:
        segs.append(run)
    out = [(r[0][2], (r[0][0] * GRID, r[0][1] * GRID), (r[-1][0] * GRID, r[-1][1] * GRID)) for r in segs]
    return out, vias


def pas(name, routes):
    L = [f"{{ {name}.pas - generated by tools/route_dram_side.py; do not edit by hand.",
         "  Adds the DRAM-side routing listed below (tracks and vias). Existing copper is not changed.",
         f"  Run: open the PcbDoc > File > Run Script > Browse to {name}.PrjScr > AddRoutes > OK. Run once. }}",
         "", "Var", "    Board : IPCB_Board;", "",
         "Function FindNet(Name : String) : IPCB_Net;",
         "Var", "    Iter : IPCB_BoardIterator;", "    N : IPCB_Net;",
         "Begin", "    Result := Nil;", "    Iter := Board.BoardIterator_Create;",
         "    Iter.AddFilter_ObjectSet(MkSet(eNetObject));", "    Iter.AddFilter_LayerSet(AllLayers);",
         "    Iter.AddFilter_Method(eProcessAll);", "    N := Iter.FirstPCBObject;",
         "    While (N <> Nil) And (Result = Nil) Do", "    Begin",
         "        If N.Name = Name Then Result := N;", "        N := Iter.NextPCBObject;", "    End;",
         "    Board.BoardIterator_Destroy(Iter);", "End;", "",
         "Procedure AddTrack(Net : IPCB_Net; Layer : TLayer; X1, Y1, X2, Y2 : Double);",
         "Var", "    T : IPCB_Track;", "Begin",
         "    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);",
         "    T.Layer := Layer;", f"    T.Width := MMsToCoord({WIDTH});",
         "    T.X1 := Board.XOrigin + MMsToCoord(X1);", "    T.Y1 := Board.YOrigin + MMsToCoord(Y1);",
         "    T.X2 := Board.XOrigin + MMsToCoord(X2);", "    T.Y2 := Board.YOrigin + MMsToCoord(Y2);",
         "    T.Net := Net;", "    Board.AddPCBObject(T);",
         "    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);",
         "End;", "",
         "Procedure AddVia(Net : IPCB_Net; X, Y : Double);",
         "Var", "    V : IPCB_Via;", "Begin",
         "    V := PCBServer.PCBObjectFactory(eViaObject, eNoDimension, eCreate_Default);",
         "    V.X := Board.XOrigin + MMsToCoord(X);", "    V.Y := Board.YOrigin + MMsToCoord(Y);",
         f"    V.Size := MMsToCoord({VIA_D});", f"    V.HoleSize := MMsToCoord({VIA_HOLE});",
         "    V.LowLayer := eTopLayer;", "    V.HighLayer := eBottomLayer;",
         "    V.Net := Net;", "    Board.AddPCBObject(V);",
         "    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, V.I_ObjectAddress);",
         "End;", "",
         "Procedure AddRoutes;", "Var", "    N : IPCB_Net;", "Begin",
         "    Board := PCBServer.GetCurrentPCBBoard;",
         "    If Board = Nil Then", "    Begin", "        ShowMessage('Open the DDR4 UDIMM PcbDoc first.');",
         "        Exit;", "    End;", "    PCBServer.PreProcess;"]
    total = 0
    for net, label, segs, vias, length in routes:
        L += [f"    {{ {label}: {length:.2f} mm }}", f"    N := FindNet('{net}');",
              f"    If N = Nil Then ShowMessage('Net {net} not found.') Else", "    Begin"]
        for lay, a, b in segs:
            L.append(f"        AddTrack(N, {PAS_LAYER[lay]}, {a[0]:.3f}, {a[1]:.3f}, {b[0]:.3f}, {b[1]:.3f});")
        for x, y in vias:
            L.append(f"        AddVia(N, {x:.3f}, {y:.3f});")
        L.append("    End;")
        total += 1
    L += ["    PCBServer.PostProcess;", "    Board.ViewManager_FullUpdate;",
          f"    ShowMessage('Added the DRAM-side routing of {total} nets. Save the PcbDoc.');", "End;", ""]
    return "\r\n".join(L)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    path, name = sys.argv[1], sys.argv[2]
    tracks, vias, pads = streams(path)
    board = Board(tracks, vias, pads)
    routes = []
    for arg in sys.argv[3:]:
        net, _, layer2 = arg.partition(":")
        layer2 = layer2 or "L8"
        res = [p for p in pads if p[0] == net and p[1] and p[1].startswith("R") and p[2] == "1"]
        dram = [p for p in pads if p[0] == net and p[1] and p[1].startswith("U")]
        fan = [v for v in vias if v[0] == net]
        if not (res and dram and fan):
            print(f"{net}: missing resistor pad, DRAM ball or fan-out via - skipped")
            continue
        start = res[0][4]
        ball = dram[0][4]
        goal = min(fan, key=lambda v: math.dist(v[1], ball))[1]
        box = (min(start[0], goal[0]) - 2.5, 5.0, max(start[0], goal[0]) + 2.5, max(goal[1], start[1]) + 2.0)
        grid_path = route(board, net, start, goal, layer2, box)
        if not grid_path:
            print(f"{net}: no path found on L1 + {layer2}")
            continue
        segs, new_vias = to_segments(grid_path)
        length = sum(math.dist(a, b) for _, a, b in segs)
        label = f"{net} ({res[0][1]} pad 1 -> {dram[0][1]}-{dram[0][2]}) L1 + {layer2}"
        print(f"{label}: {len(segs)} segments, via(s) {[(round(x, 3), round(y, 3)) for x, y in new_vias]}, "
              f"{length:.2f} mm")
        routes.append((net, label, segs, new_vias, length))
        # later nets must avoid what was just added
        for lay, a, b in segs:
            board.tracks.append((net, LAYER_ID[lay], a, b, WIDTH))
        for p in new_vias:
            board.vias.append((net, p, VIA_D))
    if not routes:
        return
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    out = os.path.join(root, "hardware", "scripts")
    with open(os.path.join(out, name + ".pas"), "w", newline="", encoding="ascii") as fh:
        fh.write(pas(name, routes))
    with open(os.path.join(out, name + ".PrjScr"), "w", newline="", encoding="ascii") as fh:
        fh.write("\r\n".join(["[Design]", "Version=1.0", "HierarchyMode=0", "OpenOutputs=1", "ArchiveProject=0",
                              "TimestampOutput=0", "SeparateFolders=0", "", "[Preferences]", "PrefsVaultGUID=",
                              "PrefsRevisionGUID=", "", "[Document1]", f"DocumentPath={name}.pas",
                              "AnnotationEnabled=1", "AnnotateStartValue=1", "AnnotationIndexControlEnabled=0",
                              "AnnotateSuffix=", "AnnotateScope=All", "AnnotateOrder=-1", "DoLibraryUpdate=1",
                              "DoDatabaseUpdate=1", "DItemRevisionGUID=", "GenerateClassCluster=0",
                              "DocumentUniqueId=", ""]))
    print(f"wrote hardware/scripts/{name}.pas and .PrjScr")


if __name__ == "__main__":
    main()
