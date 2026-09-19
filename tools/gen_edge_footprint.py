"""Gold-finger footprint and board outline for the 288-pin DDR4 UDIMM (JEDEC MO-309 Issue F).

Single source of truth for the footprint geometry. It writes:
  hardware/libraries/edge_connector/DDR4_UDIMM_288_footprint_pads.csv   pad table
  hardware/scripts/DDR4_Edge_Footprint.pas                              Altium DelphiScript that builds it

Coordinates in mm, front view (component side = Altium Top layer), pin 1 on the left.
Origin: x = 0 at the left board end, y = 0 at datum B (the lowest part of the finger edge).

Usage:
    py -3.11 tools/gen_edge_footprint.py
"""
import csv
import os

FOOTPRINT = "DDR4_UDIMM_288_MO309"

# --- MO-309F dimensions -------------------------------------------------------------------
BOARD_W = 133.35            # D
BOARD_H = 31.25             # A
PITCH = 0.85
PIN1_X = 3.35               # 2X 3.35 from each board end to the outer pin centres
PIN78_X = PIN1_X + 76 * PITCH + 5.95   # 64.60 (pins 1-77) + 5.95 gap across the key = 73.90
KEY_X = PIN1_X + 76 * PITCH + 4.30     # datum A, D2 = 4.30 from pin 77 = 72.25
KEY_W = 1.50                # 1.50 +/- 0.05, full radius at the top
KEY_DEPTH = 3.85            # 3.85 +/- 0.10 from datum B
KEY_CHAMFER = 0.20          # 2X 0.20 +/- 0.15 at the notch mouth (option 1)
PAD_W = 0.60                # 0.60 +/- 0.03
PAD_TOP = 2.60              # contact top above datum B, same for every pin
A2 = 0.25                   # non-metallised strip between the board edge and the contact (0.10-0.40)
STEP = 0.50                 # edge height in the end (step) zones
RAMPS = ((35, 47, STEP, 0.0), (105, 117, 0.0, STEP))   # pin-centre to pin-centre linear ramps
LATCH = ((8.00, 11.00), (14.60, 17.60))  # end notches, both ends
LATCH_DEPTH = 2.10
LATCH_R = 0.65
TOP_CHAMFER = 1.25          # 1.00-1.50 x 45 deg (option 1); bottom corners square
MASK_MARGIN = 0.20          # solder-mask opening beyond the first/last pad of each group
MASK_TOP = PAD_TOP + 0.15
PASTE_EXPANSION = -1.50     # removes paste from every finger
OUTLINE_WIDTH = 0.10


def pin_x(n):
    """Centre x of front pin n (1..144); back pin n+144 sits directly behind it."""
    return PIN1_X + (n - 1) * PITCH if n <= 77 else PIN78_X + (n - 78) * PITCH


def edge_y(n):
    """Height of the board edge under front pin n, measured at the pad centre line."""
    for a, b, ya, yb in RAMPS:
        if a <= n <= b:
            return ya + (yb - ya) * (n - a) / (b - a)
    return STEP if (n < 35 or n > 117) else 0.0


def pads():
    rows = []
    for side, first, layer in (("front", 1, "Top"), ("back", 145, "Bottom")):
        for n in range(1, 145):
            bottom = edge_y(n) + A2
            rows.append({"pad": first + n - 1, "side": side, "layer": layer, "front_pin": n,
                         "x": round(pin_x(n), 4), "y": round((bottom + PAD_TOP) / 2, 4),
                         "w": PAD_W, "h": round(PAD_TOP - bottom, 4),
                         "edge_y": round(edge_y(n), 4), "pad_bottom": round(bottom, 4), "pad_top": PAD_TOP})
    return rows


def outline():
    """Closed board contour: ('line', x1, y1, x2, y2) and ('arc', cx, cy, r, a0, a1) (CCW, degrees)."""
    W, H, c = BOARD_W, BOARD_H, TOP_CHAMFER
    x35, x47, x105, x117 = pin_x(35), pin_x(47), pin_x(105), pin_x(117)
    kl, kr = KEY_X - KEY_W / 2, KEY_X + KEY_W / 2
    r = KEY_W / 2
    s = [("line", 0, STEP, x35, STEP), ("line", x35, STEP, x47, 0),
         ("line", x47, 0, kl - KEY_CHAMFER, 0),
         ("line", kl - KEY_CHAMFER, 0, kl, KEY_CHAMFER), ("line", kl, KEY_CHAMFER, kl, KEY_DEPTH - r),
         ("arc", KEY_X, KEY_DEPTH - r, r, 0, 180),
         ("line", kr, KEY_DEPTH - r, kr, KEY_CHAMFER), ("line", kr, KEY_CHAMFER, kr + KEY_CHAMFER, 0),
         ("line", kr + KEY_CHAMFER, 0, x105, 0), ("line", x105, 0, x117, STEP), ("line", x117, STEP, W, STEP)]
    # right end, bottom to top
    y = STEP
    for y0, y1 in LATCH:
        xi, xc = W - LATCH_DEPTH, W - LATCH_DEPTH + LATCH_R
        s += [("line", W, y, W, y0), ("line", W, y0, xc, y0), ("arc", xc, y0 + LATCH_R, LATCH_R, 180, 270),
              ("line", xi, y0 + LATCH_R, xi, y1 - LATCH_R), ("arc", xc, y1 - LATCH_R, LATCH_R, 90, 180),
              ("line", xc, y1, W, y1)]
        y = y1
    s += [("line", W, y, W, H - c), ("line", W, H - c, W - c, H), ("line", W - c, H, c, H),
          ("line", c, H, 0, H - c)]
    # left end, top to bottom
    y = H - c
    for y0, y1 in reversed(LATCH):
        xi, xc = LATCH_DEPTH, LATCH_DEPTH - LATCH_R
        s += [("line", 0, y, 0, y1), ("line", 0, y1, xc, y1), ("arc", xc, y1 - LATCH_R, LATCH_R, 0, 90),
              ("line", xi, y1 - LATCH_R, xi, y0 + LATCH_R), ("arc", xc, y0 + LATCH_R, LATCH_R, 270, 360),
              ("line", xc, y0, 0, y0)]
        y = y0
    s.append(("line", 0, y, 0, STEP))
    return [tuple(round(v, 4) if isinstance(v, float) else v for v in seg) for seg in s]


def mask_openings():
    """Solder-mask windows (x1, y1, x2, y2), one per finger group, on both sides."""
    y1 = -0.30
    return [(round(pin_x(1) - PAD_W / 2 - MASK_MARGIN, 4), y1, round(pin_x(77) + PAD_W / 2 + MASK_MARGIN, 4), MASK_TOP),
            (round(pin_x(78) - PAD_W / 2 - MASK_MARGIN, 4), y1, round(pin_x(144) + PAD_W / 2 + MASK_MARGIN, 4), MASK_TOP)]


def _endpoints(seg):
    import math
    if seg[0] == "line":
        return (seg[1], seg[2]), (seg[3], seg[4])
    _, cx, cy, r, a0, a1 = seg
    p = lambda a: (round(cx + r * math.cos(math.radians(a)), 4), round(cy + r * math.sin(math.radians(a)), 4))
    return p(a0), p(a1)


def check_closed(segs):
    """Every endpoint must be shared by exactly two segments."""
    from collections import Counter
    ends = Counter()
    for seg in segs:
        for pt in _endpoints(seg):
            ends[(round(pt[0], 3), round(pt[1], 3))] += 1
    return [pt for pt, k in ends.items() if k != 2]


def pas_script(rows, segs, windows):
    f = lambda v: f"{v:.4f}"
    out = [f"{{ DDR4_Edge_Footprint.pas - generated by tools/gen_edge_footprint.py; do not edit by hand.",
           f"  Builds footprint {FOOTPRINT} (288 gold fingers + board outline, JEDEC MO-309F)",
           "  in the PCB library that is open and active.",
           "  Run: open DDR4_UDIMM.PcbLib > File > Run Script > Browse to this file > CreateEdgeFootprint > OK.",
           "  Run it once; a second run adds a second copy. }", "",
           "Var", "    Lib  : IPCB_Library;", "    Comp : IPCB_LibComponent;", "    OX, OY : TCoord;", "",
           "Procedure AddObj(Obj : IPCB_Primitive);", "Begin", "    Comp.AddPCBObject(Obj);",
           "    PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Obj.I_ObjectAddress);",
           "End;", "",
           "Procedure AddPad(Name : String; X, Y, W, H : Double; Layer : TLayer);", "Var", "    Pad : IPCB_Pad;", "Begin",
           "    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);",
           "    Pad.Mode     := ePadMode_Simple;", "    Pad.HoleSize := 0;", "    Pad.Layer    := Layer;",
           "    Pad.X        := OX + MMsToCoord(X);", "    Pad.Y        := OY + MMsToCoord(Y);",
           "    Pad.TopShape := eRectangular;", "    Pad.MidShape := eRectangular;", "    Pad.BotShape := eRectangular;",
           "    Pad.TopXSize := MMsToCoord(W);", "    Pad.TopYSize := MMsToCoord(H);",
           "    Pad.MidXSize := MMsToCoord(W);", "    Pad.MidYSize := MMsToCoord(H);",
           "    Pad.BotXSize := MMsToCoord(W);", "    Pad.BotYSize := MMsToCoord(H);",
           "    Pad.Name     := Name;", "    AddObj(Pad);", "End;", "",
           "Procedure AddLine(X1, Y1, X2, Y2 : Double);", "Var", "    T : IPCB_Track;", "Begin",
           "    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);",
           "    T.Layer := eMechanical1;", f"    T.Width := MMsToCoord({f(OUTLINE_WIDTH)});",
           "    T.X1 := OX + MMsToCoord(X1);", "    T.Y1 := OY + MMsToCoord(Y1);",
           "    T.X2 := OX + MMsToCoord(X2);", "    T.Y2 := OY + MMsToCoord(Y2);", "    AddObj(T);", "End;", "",
           "Procedure AddArc(CX, CY, R, A0, A1 : Double);", "Var", "    A : IPCB_Arc;", "Begin",
           "    A := PCBServer.PCBObjectFactory(eArcObject, eNoDimension, eCreate_Default);",
           "    A.Layer := eMechanical1;", f"    A.LineWidth := MMsToCoord({f(OUTLINE_WIDTH)});",
           "    A.XCenter := OX + MMsToCoord(CX);", "    A.YCenter := OY + MMsToCoord(CY);",
           "    A.Radius := MMsToCoord(R);", "    A.StartAngle := A0;", "    A.EndAngle := A1;", "    AddObj(A);", "End;", "",
           "Procedure AddMaskWindow(X1, Y1, X2, Y2 : Double; Layer : TLayer);", "Var", "    F : IPCB_Fill;", "Begin",
           "    F := PCBServer.PCBObjectFactory(eFillObject, eNoDimension, eCreate_Default);",
           "    F.Layer := Layer;", "    F.X1Location := OX + MMsToCoord(X1);", "    F.Y1Location := OY + MMsToCoord(Y1);",
           "    F.X2Location := OX + MMsToCoord(X2);", "    F.Y2Location := OY + MMsToCoord(Y2);",
           "    F.Rotation := 0;", "    AddObj(F);", "End;", "",
           "Procedure CreateEdgeFootprint;", "Begin",
           "    Lib := PCBServer.GetCurrentPCBLibrary;",
           "    If Lib = Nil Then", "    Begin",
           "        ShowMessage('Open DDR4_UDIMM.PcbLib and click inside it first.');", "        Exit;", "    End;",
           "    OX := Lib.Board.XOrigin;", "    OY := Lib.Board.YOrigin;", "",
           "    Comp := PCBServer.CreatePCBLibComp;", f"    Comp.Name := '{FOOTPRINT}';",
           "    Lib.RegisterComponent(Comp);", "    PCBServer.PreProcess;", "",
           "    { 144 front fingers on Top, 144 back fingers on Bottom (pad 145 behind pad 1) }"]
    for r in rows:
        layer = "eTopLayer" if r["layer"] == "Top" else "eBottomLayer"
        out.append(f"    AddPad('{r['pad']}', {f(r['x'])}, {f(r['y'])}, {f(r['w'])}, {f(r['h'])}, {layer});")
    out += ["", "    { board outline on Mechanical 1 }"]
    for s in segs:
        if s[0] == "line":
            out.append(f"    AddLine({', '.join(f(v) for v in s[1:])});")
        else:
            out.append(f"    AddArc({', '.join(f(v) for v in s[1:])});")
    out += ["", "    { solder-mask windows over each finger group, both sides }"]
    for w in windows:
        for layer in ("eTopSolder", "eBottomSolder"):
            out.append(f"    AddMaskWindow({', '.join(f(v) for v in w)}, {layer});")
    out += ["", "    PCBServer.PostProcess;", "    Lib.CurrentComponent := Comp;", "    Lib.Board.ViewManager_FullUpdate;",
            "    Client.SendMessage('PCB:Zoom', 'Action=All', 255, Client.CurrentView);",
            f"    ShowMessage('{FOOTPRINT}: 288 pads, outline and mask windows created. Save the library (Ctrl+S).');",
            "End;", ""]
    return "\r\n".join(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, ".."))
    rows, segs, windows = pads(), outline(), mask_openings()

    assert len(rows) == 288 and len({r["pad"] for r in rows}) == 288
    assert abs(pin_x(144) + PIN1_X - BOARD_W) < 1e-9, "outer pins must be 3.35 from both ends"
    assert abs(PIN78_X - 73.90) < 1e-9 and abs(KEY_X - 72.25) < 1e-9
    assert abs(KEY_X - BOARD_W / 2 - 5.575) < 1e-9, "D1: key 5.575 right of the board centre"
    open_ends = check_closed(segs)
    assert not open_ends, f"outline not closed at {open_ends}"
    # pads next to the key must clear the notch
    assert pin_x(77) + PAD_W / 2 < KEY_X - KEY_W / 2 - KEY_CHAMFER and pin_x(78) - PAD_W / 2 > KEY_X + KEY_W / 2 + KEY_CHAMFER

    csv_path = os.path.join(root, "hardware", "libraries", "edge_connector", "DDR4_UDIMM_288_footprint_pads.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    pas_dir = os.path.join(root, "hardware", "scripts")
    os.makedirs(pas_dir, exist_ok=True)
    with open(os.path.join(pas_dir, "DDR4_Edge_Footprint.pas"), "w", newline="", encoding="ascii") as fh:
        fh.write(pas_script(rows, segs, windows))
    # File > Run Script > Browse only opens script projects, so wrap the .pas in one
    with open(os.path.join(pas_dir, "DDR4_Edge_Footprint.PrjScr"), "w", newline="", encoding="ascii") as fh:
        fh.write("\r\n".join(["[Design]", "Version=1.0", "HierarchyMode=0", "OpenOutputs=1", "ArchiveProject=0",
                              "TimestampOutput=0", "SeparateFolders=0", "", "[Preferences]", "PrefsVaultGUID=",
                              "PrefsRevisionGUID=", "", "[Document1]", "DocumentPath=DDR4_Edge_Footprint.pas",
                              "AnnotationEnabled=1", "AnnotateStartValue=1", "AnnotationIndexControlEnabled=0",
                              "AnnotateSuffix=", "AnnotateScope=All", "AnnotateOrder=-1", "DoLibraryUpdate=1",
                              "DoDatabaseUpdate=1", "DItemRevisionGUID=", "GenerateClassCluster=0",
                              "DocumentUniqueId=", ""]))

    lengths = sorted({r["h"] for r in rows})
    print(f"{FOOTPRINT}: {len(rows)} pads, pad length {lengths[0]}..{lengths[-1]} mm, "
          f"{sum(s[0] == 'line' for s in segs)} lines + {sum(s[0] == 'arc' for s in segs)} arcs (closed), "
          f"{len(windows)} x 2 mask windows")
    print("wrote", os.path.relpath(csv_path, root), "and hardware/scripts/DDR4_Edge_Footprint.pas")


if __name__ == "__main__":
    main()
