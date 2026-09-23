"""Length-tune a whole byte lane by script: fold meander into the DRAM-side wires until every line
in the byte reaches the byte's longest line (main spec Table 11, DQ/DM within DQS +/- 1.0 mm).

For each net that is short, the tool walks its straight pieces (longest first), and on each piece
places 45-degree chamfered teeth on whichever side has room. A tooth of height h adds 2h - 0.1875 mm
and occupies 0.56 mm along the wire, teeth repeating every 0.76 mm; the last tooth's height is solved
so the net lands on its target rather than past it. Every point of every new shape is checked against
all other copper on that layer (tracks, arcs, vias, pads) at the board clearance, and against the
net's own other copper, so nothing is added where it does not fit. Existing routing is never moved.

Usage:
    py -3.11 tools/tune_byte.py <board.PcbDoc> <byte> [script name]
    e.g. py -3.11 tools/tune_byte.py board.PcbDoc 0 Byte0_Tune
"""
import math
import os
import struct
import sys

import olefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import byte_status as BS                          # noqa: E402
import check_lengths as CL                        # noqa: E402
import route_dram_side as R                       # noqa: E402

CLEAR = 0.0999                # board clearance; the coupled pairs already run at exactly 0.10
SELF_CLEAR = 0.15             # keep new meander off the rest of its own net
BASE, PITCH = 0.56, 0.76      # one tooth's footprint along the wire, and tooth spacing
HEIGHTS = (1.2, 1.0, 0.85, 0.7, 0.55, 0.42, 0.32, 0.24)
MIN_H, MARGIN = 0.20, 0.10    # smallest usable tooth, and clear space kept at each end of a piece
LAYER_NAME = {1: "L1", 3: "L3", 32: "L8"}
LAYER_ID = {v: k for k, v in LAYER_NAME.items()}


def gain(h):
    return 2.0 * h - 0.1875


def height_for(g):
    return (g + 0.1875) / 2.0


def tooth(h):
    return [(-0.28, 0.0), (-0.20, 0.08), (-0.20, h - 0.08), (-0.12, h),
            (0.12, h), (0.20, h - 0.08), (0.20, 0.08), (0.28, 0.0)]


def shape(a, b, teeth, side):
    """Polyline from a to b with teeth given as (centre distance along the piece, height)."""
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    vx, vy = -uy * side, ux * side
    pts = [a]
    for c, h in teeth:
        for du, dv in tooth(h):
            pts.append((a[0] + ux * (c + du) + vx * dv, a[1] + uy * (c + du) + vy * dv))
    pts.append(b)
    return pts


def arcs_as_tracks(path, names):
    """Existing arcs (rounded serpentines) as short chords, so new copper keeps clear of them."""
    ole = olefile.OleFileIO(path)
    out, data, pos = [], ole.openstream("Arcs6/Data").read(), 0
    while pos < len(data):
        pos += 1
        n = struct.unpack_from("<I", data, pos)[0]
        r = data[pos + 4:pos + 4 + n]
        pos += 4 + n
        ni = struct.unpack_from("<H", r, 3)[0]
        net = names[ni] if ni < len(names) else None
        cx, cy, rad = (v * R.UNIT for v in struct.unpack_from("<3i", r, 13))
        sa, ea = struct.unpack_from("<2d", r, 25)
        w = struct.unpack_from("<i", r, 41)[0] * R.UNIT
        steps = max(2, int(abs(ea - sa) / 10) + 1)
        pts = [(cx + rad * math.cos(math.radians(sa + (ea - sa) * i / steps)),
                cy + rad * math.sin(math.radians(sa + (ea - sa) * i / steps))) for i in range(steps + 1)]
        for p, q in zip(pts, pts[1:]):
            out.append((net, r[0], p, q, w))
    return out


def fits(board, net, pts, lay, own, base):
    """Check the new shape against other nets, and its excursions against its own net's copper.

    Points that still lie on the original straight piece are skipped in the own-net check: the piece
    meets the rest of its net at both ends, so those points are touching their own neighbours by
    definition.
    """
    layer = LAYER_NAME[lay]
    a, b = base
    for p, q in zip(pts, pts[1:]):
        steps = max(1, int(math.dist(p, q) / 0.02))
        for i in range(steps + 1):
            x = (p[0] + (q[0] - p[0]) * i / steps, p[1] + (q[1] - p[1]) * i / steps)
            if not board.clear_on(x, layer, net, R.WIDTH / 2):
                return False
            if R.seg_dist(x, a, b) < 0.03:        # still on the original line
                continue
            for l2, a2, b2 in own:                # its own net's other copper
                if l2 == lay and R.seg_dist(x, a2, b2) < R.WIDTH + SELF_CLEAR:
                    return False
    return True


def plan_piece(board, net, lay, a, b, need, own):
    """Best (teeth, side, gain) for one straight piece, or None."""
    L = math.dist(a, b)
    best = None
    for h in HEIGHTS:
        for side in (1, -1):
            teeth, got, u = [], 0.0, MARGIN + BASE / 2
            while u + BASE / 2 + MARGIN <= L and got < need - 1e-9:
                hh = h
                if gain(h) > need - got:          # last tooth: solve its height exactly
                    hh = height_for(need - got)
                    if hh < MIN_H:
                        break
                trial = teeth + [(u, hh)]
                if fits(board, net, shape(a, b, trial, side), lay, own, (a, b)):
                    teeth, got = trial, got + gain(hh)
                u += PITCH
            if teeth and (best is None or abs(need - got) < abs(need - best[2]) - 1e-9):
                best = (teeth, side, got)
            if best and abs(need - best[2]) < 0.01:
                return best
    return best


def plan(path, k):
    R.CLEAR = CLEAR
    ole = olefile.OleFileIO(path)
    names = CL.nets(ole)
    tracks, vias, pads = R.streams(path)
    board = R.Board(tracks + arcs_as_tracks(path, names), vias, pads)
    _dram, rows = BS.byte_rows(path, k)
    if not rows:
        sys.exit("byte %d: nothing found" % k)
    target = max(r["total"] for r in rows)
    print("byte %d: target %.2f mm (longest line)" % (k, target))
    fixes = []
    for row in sorted(rows, key=lambda r: r["total"]):
        need = target - row["total"]
        net = "NetR%s_1" % row["res"][1:]
        if need <= 1.0:
            print("  %-4s %-8s %6.2f - inside the window" % (row["res"], row["signal"], row["total"]))
            continue
        # both halves of the line carry length equally: the DRAM-side net and the finger-side net
        halves = (net, row["signal"])
        pieces = sorted(((n, lay, a, b) for n, lay, a, b, _w in tracks
                         if n in halves and lay in LAYER_NAME),
                        key=lambda s: -math.dist(s[2], s[3]))
        got, used = 0.0, []
        for pnet, lay, a, b in pieces:
            if got >= need - 0.05:
                break
            rest = [(l2, a2, b2) for n2, l2, a2, b2, _w in board.tracks
                    if n2 == pnet and not (l2 == lay and a2 == a and b2 == b)]
            res = plan_piece(board, pnet, lay, a, b, need - got, rest)
            if not res:
                continue
            teeth, side, g = res
            pts = shape(a, b, teeth, side)
            used.append((pnet, lay, a, b, pts, len(teeth)))
            got += g
            for p, q in zip(pts, pts[1:]):        # new copper blocks later teeth
                board.tracks.append((pnet, lay, p, q, R.WIDTH))
        if used:
            fixes.append((row, net, used, got))
        state = "reaches target" if got >= need - 0.05 else "short by %.2f mm" % (need - got)
        print("  %-4s %-8s %6.2f needs %+6.2f -> %d teeth on %d piece(s), %+.2f mm, %s"
              % (row["res"], row["signal"], row["total"], need,
                 sum(u[5] for u in used), len(used), got, state))
    return fixes


def pas(name, k, fixes):
    L = ["{ %s.pas - generated by tools/tune_byte.py; do not edit by hand." % name,
         "  Length-tunes byte %d: replaces the straight pieces listed below with the same pieces plus" % k,
         "  45-degree meander teeth, so every line reaches the byte's longest line. Nothing else changes.",
         "  Run: open the PcbDoc > File > Run Script > Browse to %s.PrjScr > TuneByte > OK. Run once. }" % name,
         "", "Var", "    Board : IPCB_Board;", "    Done  : Integer;", "",
         "Function IsClose(A, B : Double) : Boolean;", "Begin", "    Result := Abs(A - B) < 0.01;", "End;", "",
         "Procedure AddTrack(Net : IPCB_Net; Layer : TLayer; X1, Y1, X2, Y2 : Double);",
         "Var", "    T : IPCB_Track;", "Begin",
         "    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);",
         "    T.Layer := Layer;", "    T.Width := MMsToCoord(%s);" % R.WIDTH,
         "    T.X1 := Board.XOrigin + MMsToCoord(X1);", "    T.Y1 := Board.YOrigin + MMsToCoord(Y1);",
         "    T.X2 := Board.XOrigin + MMsToCoord(X2);", "    T.Y2 := Board.YOrigin + MMsToCoord(Y2);",
         "    T.Net := Net;", "    Board.AddPCBObject(T);",
         "    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, "
         "T.I_ObjectAddress);",
         "End;", "",
         "{ Find the track of NetName on Layer from (X1,Y1) to (X2,Y2) (either direction), remove it and",
         "  return its net; Nil if it is not there }",
         "Function TakeTrack(NetName : String; Layer : TLayer; X1, Y1, X2, Y2 : Double) : IPCB_Net;",
         "Var", "    Iter : IPCB_BoardIterator;", "    T, F : IPCB_Track;", "    AX, AY, BX, BY : Double;", "Begin",
         "    Result := Nil;", "    F := Nil;", "    Iter := Board.BoardIterator_Create;",
         "    Iter.AddFilter_ObjectSet(MkSet(eTrackObject));", "    Iter.AddFilter_LayerSet(MkSet(Layer));",
         "    Iter.AddFilter_Method(eProcessAll);", "    T := Iter.FirstPCBObject;",
         "    While (T <> Nil) And (F = Nil) Do", "    Begin",
         "        If (T.Net <> Nil) And (T.Net.Name = NetName) Then", "        Begin",
         "            AX := CoordToMMs(T.X1 - Board.XOrigin); AY := CoordToMMs(T.Y1 - Board.YOrigin);",
         "            BX := CoordToMMs(T.X2 - Board.XOrigin); BY := CoordToMMs(T.Y2 - Board.YOrigin);",
         "            If (IsClose(AX, X1) And IsClose(AY, Y1) And IsClose(BX, X2) And IsClose(BY, Y2)) Or",
         "               (IsClose(AX, X2) And IsClose(AY, Y2) And IsClose(BX, X1) And IsClose(BY, Y1)) Then F := T;",
         "        End;", "        T := Iter.NextPCBObject;", "    End;", "    Board.BoardIterator_Destroy(Iter);",
         "    If F <> Nil Then", "    Begin", "        Result := F.Net;", "        Board.RemovePCBObject(F);", "    End;",
         "End;", "",
         "Procedure TuneByte;", "Var", "    N : IPCB_Net;", "Begin",
         "    Board := PCBServer.GetCurrentPCBBoard;",
         "    If Board = Nil Then", "    Begin", "        ShowMessage('Open the DDR4 UDIMM PcbDoc first.');",
         "        Exit;", "    End;", "    Done := 0;", "    PCBServer.PreProcess;"]
    for row, net, used, got in fixes:
        L.append("    { %s %s -> %s: %+.2f mm }" % (row["res"], row["signal"], row["ball"], got))
        for pnet, lay, a, b, pts, n in used:
            pl = R.PAS_LAYER[LAYER_NAME[lay]]
            L += ["    N := TakeTrack('%s', %s, %.4f, %.4f, %.4f, %.4f);" % (pnet, pl, a[0], a[1], b[0], b[1]),
                  "    If N <> Nil Then", "    Begin"]
            for p, q in zip(pts, pts[1:]):
                L.append("        AddTrack(N, %s, %.4f, %.4f, %.4f, %.4f);" % (pl, p[0], p[1], q[0], q[1]))
            L += ["        Done := Done + 1;", "    End;"]
    L += ["    PCBServer.PostProcess;", "    Board.ViewManager_FullUpdate;",
          "    ShowMessage('Tuned ' + IntToStr(Done) + ' pieces in byte %d. Save the PcbDoc.');" % k,
          "End;", ""]
    return "\r\n".join(L)


PRJSCR = ["[Design]", "Version=1.0", "HierarchyMode=0", "OpenOutputs=1", "ArchiveProject=0",
          "TimestampOutput=0", "SeparateFolders=0", "", "[Preferences]", "PrefsVaultGUID=",
          "PrefsRevisionGUID=", "", "[Document1]", "DocumentPath=%s.pas", "AnnotationEnabled=1",
          "AnnotateStartValue=1", "AnnotationIndexControlEnabled=0", "AnnotateSuffix=", "AnnotateScope=All",
          "AnnotateOrder=-1", "DoLibraryUpdate=1", "DoDatabaseUpdate=1", "DItemRevisionGUID=",
          "GenerateClassCluster=0", "DocumentUniqueId=", ""]


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    path, k = sys.argv[1], int(sys.argv[2])
    name = sys.argv[3] if len(sys.argv) == 4 else "Byte%d_Tune" % k
    fixes = plan(path, k)
    if not fixes:
        return
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hardware", "scripts")
    with open(os.path.join(out, name + ".pas"), "w", newline="", encoding="ascii") as fh:
        fh.write(pas(name, k, fixes))
    with open(os.path.join(out, name + ".PrjScr"), "w", newline="", encoding="ascii") as fh:
        fh.write("\r\n".join(line % name if "%s" in line else line for line in PRJSCR))
    print("\nwrote hardware/scripts/%s.pas and .PrjScr (%d nets)" % (name, len(fixes)))


if __name__ == "__main__":
    main()
