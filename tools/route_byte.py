"""Route the DRAM side of a whole byte lane: every 15 ohm resistor's pad 1 to its DRAM ball.

For each line in the byte that is not routed yet, the grid router in route_dram_side is run twice,
once escaping onto L8 and once onto L3, and the shorter result is kept (L1 from the resistor, one
through via, then the chosen layer into the ball's existing fan-out via). Each accepted route is
added to the obstacle set before the next net is planned, so the lines do not collide. Existing
copper is never moved.

Lines are routed longest-first: the awkward ones that cross the chip get the free space while it is
still there.

Usage:
    py -3.11 tools/route_byte.py <board.PcbDoc> <byte> [script name]
    e.g. py -3.11 tools/route_byte.py board.PcbDoc 1 U2_Route
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import byte_status as BS                          # noqa: E402
import route_dram_side as R                       # noqa: E402

CLEAR = 0.11                  # generic rule 0.10 mm plus a margin; pads and vias use their own rules
ROUTED = 1.0                  # mm of copper before a line counts as already routed
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
    name = sys.argv[3] if len(sys.argv) == 4 else "U%d_Route" % (k + 1)
    R.CLEAR = CLEAR

    tracks, vias, pads = R.streams(path)
    board = R.Board(tracks, vias, pads)
    dram, rows = BS.byte_rows(path, k)

    jobs = []
    for row in rows:
        net = "NetR%s_1" % row["res"][1:]
        if row["dram"] >= ROUTED:
            print("%-4s %-8s -> %s-%s  already routed (%.2f mm)"
                  % (row["res"], row["signal"], dram, row["ball"], row["dram"]))
            continue
        res = [p for p in pads if p[0] == net and p[1] == row["res"] and p[2] == "1"]
        ball = [p for p in pads if p[0] == net and p[1] == dram]
        if not res or not ball:
            print("%-4s %-8s  no pads found" % (row["res"], row["signal"]))
            continue
        near = [v for v in vias if v[0] == net]
        goal = min(near, key=lambda v: math.dist(v[1], ball[0][4]))[1] if near else ball[0][4]
        jobs.append((row, net, res[0][4], goal, ball[0][2]))

    jobs.sort(key=lambda j: -math.dist(j[2], j[3]))    # hardest first
    routes = []
    for row, net, start, goal, ball in jobs:
        best = None
        for layer2 in ("L8", "L3"):
            box = (min(start[0], goal[0]) - 3.0, min(start[1], goal[1]) - 1.0,
                   max(start[0], goal[0]) + 3.0, max(start[1], goal[1]) + 2.0)
            path_found = R.route(board, net, start, goal, layer2, box)
            if not path_found:
                print("  %-4s %-8s %s: no path" % (row["res"], row["signal"], layer2), flush=True)
                continue
            segs, nv = R.to_segments(path_found)
            length = sum(math.dist(a, b) for _lay, a, b in segs)
            print("  %-4s %-8s %s: %.2f mm, %d segments" % (row["res"], row["signal"], layer2,
                                                            length, len(segs)), flush=True)
            if best is None or length < best[0]:
                best = (length, layer2, segs, nv)
        if best is None:
            print("%-4s %-8s -> %s-%s  NO ROUTE" % (row["res"], row["signal"], dram, ball), flush=True)
            continue
        length, layer2, segs, nv = best
        label = "%s %s (%s pad 1 -> %s-%s) L1 + %s, %.2f mm" % (row["res"], row["signal"], row["res"],
                                                                dram, ball, layer2, length)
        print("CHOSEN %s" % label, flush=True)
        routes.append((net, label, segs, nv, length))
        for lay, a, b in segs:                     # block the space for the nets that follow
            board.tracks.append((net, R.LAYER_ID[lay], a, b, R.WIDTH))
        for p in nv:
            board.vias.append((net, p, R.VIA_D))

    if not routes:
        print("\nnothing to route")
        return
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hardware", "scripts")
    with open(os.path.join(out, name + ".pas"), "w", newline="", encoding="ascii") as fh:
        fh.write(R.pas(name, routes))
    with open(os.path.join(out, name + ".PrjScr"), "w", newline="", encoding="ascii") as fh:
        fh.write("\r\n".join(line % name if "%s" in line else line for line in PRJSCR))
    print("\nwrote hardware/scripts/%s.pas and .PrjScr (%d nets, %.1f mm of new copper)"
          % (name, len(routes), sum(r[4] for r in routes)))


if __name__ == "__main__":
    main()
