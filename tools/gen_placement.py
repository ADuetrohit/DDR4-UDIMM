"""Generate the component placement for the DDR4 UDIMM (JEDEC Raw Card A3) and an Altium script.

Every coordinate below comes from a JEDEC number (JESD21-C 4.20.26 Annex A, Raw Card A3, and the
main spec's Table 9); see docs/PLACEMENT.md for the derivation.

Writes:
  hardware/placement.csv                         designator, x, y, rotation, reason
  hardware/scripts/DDR4_Placement.pas (+ .PrjScr) Altium DelphiScript that places every part
  hardware/scripts/DDR4_DataResistors.pas (+ .PrjScr) the same for the 88 data resistors only

Run the script in Altium: open the PcbDoc > File > Run Script > Browse to DDR4_Placement.PrjScr
> PlaceComponents > OK. It only moves and rotates existing parts, so it can be re-run safely.

Usage:
    py -3.11 tools/gen_placement.py
"""
import csv
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ---- JEDEC-derived constants (mm, board origin = bottom-left, fingers along y = 0) -------------
LANE_X = [9.3, 18.7, 28.0, 37.3, 92.6, 102.0, 111.3, 120.7]   # centre of each byte's 11 data fingers
DRAM_PITCH = 10.93        # <= TL3 12.8 mm (Annex A p.10) between neighbouring DRAMs
DRAM_Y = 15.3             # puts ball row A (data side) at y 10.5: finger-to-ball 11-14 mm (Annex A p.9)
DRAM_ROT = 180            # ball A1 toward the fingers: data rows A-E face the connector
RES_Y = (5.0, 7.5)        # 15 ohm rows: front-finger nets low, back-finger nets high (via in between)
RES_PITCH = 1.3
RES_ROT = 270             # pad 2 (connector-side net) toward the fingers, pad 1 (DRAM side) toward the DRAM
CAP_DX = 4.6              # side decoupling: 0.85 mm outside the 7.5 mm DRAM body
BALL = 0.8                # DRAM ball pitch

# DRAM centres: bytes 0 and 7 sit on their lanes; the others step inward at DRAM_PITCH so the
# U4-U5 hop stays under TL4 = 46.3 mm (Annex A p.10). This gives the Annex A pattern of longer
# data nets for the middle bytes (11.1 mm for byte 0 rising to 13.7 mm for byte 3).
DRAM_X = [round(LANE_X[0] + i * DRAM_PITCH, 2) for i in range(4)] + \
         [round(LANE_X[7] - (3 - i) * DRAM_PITCH, 2) for i in range(4)]


# On every DRAM sheet the data resistors R(base+1..base+11) carry these connector-side nets
# (base = 12k+1): DQ0, DQ1, DQ2, DQ3, DQ4, DQ6, DQ7, DQS_t, DQS_c, DM, DQ5 of byte k.
RES_ROLE = ["DQ0", "DQ1", "DQ2", "DQ3", "DQ4", "DQ6", "DQ7", "DQS_T", "DQS_C", "DM", "DQ5"]


def finger_positions():
    """{net: (x, side)} of every data finger, from the edge-connector tables."""
    lib = os.path.join(ROOT, "hardware", "libraries", "edge_connector")
    pads = {r["pad"]: (float(r["x"]), r["side"])
            for r in csv.DictReader(open(os.path.join(lib, "DDR4_UDIMM_288_footprint_pads.csv"), encoding="utf-8"))}
    return {r["Net on this design"]: pads[r["Pin"]]
            for r in csv.DictReader(open(os.path.join(lib, "DDR4_UDIMM_288_pinout.csv"), encoding="utf-8"))}


def role_net(k, role):
    if role.startswith("DQS"):
        return f"DQS{k}{role[3:]}"
    if role == "DM":
        return f"DM{k}"
    return f"DQ{8 * k + int(role[2:])}"


def data_resistors(k, fingers):
    """Byte k's 11 series resistors, each above its own finger and in finger order, so no finger-side
    trace crosses another: front-finger nets in the low row at the finger x; back-finger nets in the
    high row at the finger x (they sit in the gaps between front fingers), with the DQS pair, whose
    back fingers are only 0.85 mm apart, spread to 1.3 mm."""
    base = 12 * k + 1
    nets = [(fingers[role_net(k, role)], f"R{base + 1 + i}", role_net(k, role)) for i, role in enumerate(RES_ROLE)]
    out = []
    back = sorted((x, r, n) for (x, side), r, n in nets if side == "back")
    for (x, side), r, n in nets:
        if side == "front":
            out.append((r, x, RES_Y[0], n))
    dqs = [x for x, r, n in back if "DQS" in n]
    mid = sum(dqs) / len(dqs)
    for x, r, n in back:
        if "DQS" in n:                              # keep finger order, 1.3 mm apart
            x = mid + (RES_PITCH / 2 if x == max(dqs) else -RES_PITCH / 2)
        out.append((r, x, RES_Y[1], n))
    return out


def ball(cx, col, row):
    """Ball position after the 180 degree rotation: column 1 on the right, row A at the bottom."""
    idx = "ABCDEFGHJKLMN".index(row)
    return round(cx - (col - 5) * BALL, 3), round(DRAM_Y - 4.8 + idx * BALL, 3)


def placement():
    rows = []

    def put(des, x, y, rot, why):
        rows.append((des, round(x, 3), round(y, 3), rot, why))

    put("J1", 0.0, 0.0, 0, "gold fingers, board origin")
    fingers = finger_positions()
    for k in range(8):
        cx, lane = DRAM_X[k], LANE_X[k]
        base = 12 * k + 1                           # R(base) = ZQ, R(base+1..base+11) = data
        put(f"U{k + 1}", cx, DRAM_Y, DRAM_ROT, f"byte {k} DRAM, lane {lane}, TL3/TL4 fly-by spacing")
        for r, x, y, net in data_resistors(k, fingers):
            put(r, x, y, RES_ROT, f"byte {k} 15 ohm series for {net}, above its finger (TL0)")
        bx, by = ball(cx, 9, "B")
        put(f"R{base}", cx - CAP_DX, by, 90, f"U{k + 1} ZQ 240 ohm at ball B9 (5 pF max load)")
        c = 6 * k                                   # C(c+1) VREFCA, C(c+2..3) VDD, C(c+4) 1 uF, C(c+5..6) VPP
        put(f"C{c + 1}", cx + CAP_DX, ball(cx, 1, "J")[1], 90, f"U{k + 1} VREFCA at ball J1 (Table 9)")
        put(f"C{c + 2}", cx + CAP_DX, 14.1, 90, f"U{k + 1} VDD/VDDQ, right-hand VDD balls (Table 9)")
        put(f"C{c + 3}", cx - CAP_DX, DRAM_Y, 90, f"U{k + 1} VDD/VDDQ, left-hand VDD balls (Table 9)")
        put(f"C{c + 4}", cx, DRAM_Y + 6.4, 0, f"U{k + 1} 1.0 uF VDD, above the DRAM (Table 9 note 2)")
        put(f"C{c + 5}", cx + CAP_DX, ball(cx, 1, "B")[1], 90, f"U{k + 1} VPP at ball B1 (Table 9)")
        put(f"C{c + 6}", cx - CAP_DX, ball(cx, 9, "M")[1], 90, f"U{k + 1} VPP at ball M9 (Table 9)")

    # SPD: kept where the Annex A general-layout drawing shows it (top centre)
    put("U9", 66.675, 24.0, 90, "SPD, top centre as in the Annex A layout drawing")
    put("C49", 69.2, 24.0, 90, "SPD VDDSPD decoupling")

    # Finger-side parts
    put("R106", 65.825, 5.2, 0, "CK1 75 ohm across CK1_t/c, TL0 3.7 +/- 0.8 mm (Annex A p.7)")
    put("C70", 68.2, 5.2, 90, "VTT cap next to the VTT finger (Table 9)")
    put("C53", 129.2, 5.2, 90, "VPP cap next to the VPP fingers (Table 9)")
    put("C54", 4.2, 5.2, 90, "VREFCA cap next to the VREFCA finger (Table 9)")

    # Fly-by end (after U8): terminations within TL5 = 13.0 mm of the last DRAM
    term = [97, 98, 99, 100, 101, 103, 104, 105, 107, 108, 109, 110, 111,
            112, 113, 114, 116, 118, 119, 120, 121, 122, 123, 124, 125, 126]
    for i, r in enumerate(term):
        put(f"R{r}", 113.0 + (i % 13) * RES_PITCH, 23.2 if i < 13 else 25.6, 90,
            "39 ohm VTT termination after U8, TL5 13.0 mm (Annex A p.10-11)")
    for i, cnum in enumerate(range(57, 70)):
        put(f"C{cnum}", 113.0 + i * RES_PITCH, 28.0, 90, "VTT decoupling, 1 per 2 terminations (Table 9)")
    put("R115", 126.0, 20.5, 90, "CK0_t 39 ohm after U8, TL5 13.0 mm (Annex A p.6)")
    put("R117", 127.3, 20.5, 90, "CK0_c 39 ohm after U8, TL5 13.0 mm (Annex A p.6)")
    put("C56", 128.6, 20.5, 90, "CK0 0.01 uF to VDD (Annex A p.6)")
    put("R102", 4.4, 21.2, 90, "ALERT_n 47 ohm pull-up to VDD before the first DRAM U1, TL0 2.5 mm (Annex A p.12, main spec 6.3.7)")

    # Bulk VDD (Table 9: 4 per module), spread along the module
    put("C50", 48.8, DRAM_Y, 90, "4.7 uF bulk VDD (Table 9)")
    put("C51", 81.2, DRAM_Y, 90, "4.7 uF bulk VDD (Table 9)")
    put("C52", 25.0, 25.5, 0, "4.7 uF bulk VDD (Table 9)")
    put("C55", 100.0, 25.5, 0, "4.7 uF bulk VDD (Table 9)")
    return rows


def pas_script(rows, what="every component of the DDR4 UDIMM", prjscr="DDR4_Placement.PrjScr"):
    out = ["{ DDR4_Placement.pas - generated by tools/gen_placement.py; do not edit by hand.",
           f"  Places {what} at the JEDEC-derived position in",
           "  hardware/placement.csv (x, y in mm from the board origin, rotation in degrees).",
           f"  Run: open the PcbDoc > File > Run Script > Browse to {prjscr} > PlaceComponents > OK.",
           "  It only moves and rotates existing parts, so running it again is safe. }",
           "",
           "Var",
           "    Board  : IPCB_Board;",
           "    Placed : Integer;",
           "    Missed : String;",
           "",
           "Procedure Place(Des : String; X, Y, Rot : Double);",
           "Var",
           "    Iter : IPCB_BoardIterator;",
           "    C    : IPCB_Component;",
           "    Done : Boolean;",
           "Begin",
           "    Done := False;",
           "    Iter := Board.BoardIterator_Create;",
           "    Iter.AddFilter_ObjectSet(MkSet(eComponentObject));",
           "    Iter.AddFilter_LayerSet(AllLayers);",
           "    Iter.AddFilter_Method(eProcessAll);",
           "    C := Iter.FirstPCBObject;",
           "    While (C <> Nil) And (Not Done) Do",
           "    Begin",
           "        If C.Name.Text = Des Then",
           "        Begin",
           "            PCBServer.SendMessageToRobots(C.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);",
           "            C.Rotation := Rot;",
           "            C.MoveToXY(Board.XOrigin + MMsToCoord(X), Board.YOrigin + MMsToCoord(Y));",
           "            PCBServer.SendMessageToRobots(C.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);",
           "            Placed := Placed + 1;",
           "            Done := True;",
           "        End;",
           "        C := Iter.NextPCBObject;",
           "    End;",
           "    Board.BoardIterator_Destroy(Iter);",
           "    If Not Done Then Missed := Missed + Des + ' ';",
           "End;",
           "",
           "Procedure PlaceComponents;",
           "Begin",
           "    Board := PCBServer.GetCurrentPCBBoard;",
           "    If Board = Nil Then",
           "    Begin",
           "        ShowMessage('Open the DDR4 UDIMM PcbDoc first.');",
           "        Exit;",
           "    End;",
           "    Placed := 0;",
           "    Missed := '';",
           "    PCBServer.PreProcess;"]
    for des, x, y, rot, _ in rows:
        if des == "J1":
            continue                                # J1 defines the board; never move it
        out.append(f"    Place('{des}', {x:.3f}, {y:.3f}, {rot});")
    out += ["    PCBServer.PostProcess;",
            "    Board.ViewManager_FullUpdate;",
            f"    ShowMessage('Placed ' + IntToStr(Placed) + ' of {sum(1 for r in rows if r[0] != 'J1')} components.' + #13#10 + 'Not found: ' + Missed);",
            "End;", ""]
    return "\r\n".join(out)


def write_script(pas_dir, name, text):
    """Write <name>.pas and the one-document script project Altium's Run Script needs."""
    with open(os.path.join(pas_dir, name + ".pas"), "w", newline="", encoding="ascii") as fh:
        fh.write(text)
    with open(os.path.join(pas_dir, name + ".PrjScr"), "w", newline="", encoding="ascii") as fh:
        fh.write("\r\n".join(["[Design]", "Version=1.0", "HierarchyMode=0", "OpenOutputs=1", "ArchiveProject=0",
                              "TimestampOutput=0", "SeparateFolders=0", "", "[Preferences]", "PrefsVaultGUID=",
                              "PrefsRevisionGUID=", "", "[Document1]", f"DocumentPath={name}.pas",
                              "AnnotationEnabled=1", "AnnotateStartValue=1", "AnnotationIndexControlEnabled=0",
                              "AnnotateSuffix=", "AnnotateScope=All", "AnnotateOrder=-1", "DoLibraryUpdate=1",
                              "DoDatabaseUpdate=1", "DItemRevisionGUID=", "GenerateClassCluster=0",
                              "DocumentUniqueId=", ""]))


def main():
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    rows = placement()
    names = [r[0] for r in rows]
    assert len(names) == len(set(names)) == 206, (len(names), len(set(names)))

    with open(os.path.join(root, "hardware", "placement.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["designator", "x_mm", "y_mm", "rotation", "reason"])
        w.writerows(rows)

    pas_dir = os.path.join(root, "hardware", "scripts")
    write_script(pas_dir, "DDR4_Placement", pas_script(rows))
    data = [r for r in rows if r[4].startswith("byte") and "15 ohm" in r[4]]
    write_script(pas_dir, "DDR4_DataResistors", pas_script(data, "only the 88 x 15 ohm data resistors",
                                                             "DDR4_DataResistors.PrjScr"))
    print(f"wrote hardware/placement.csv ({len(rows)} parts), hardware/scripts/DDR4_Placement.pas and "
          f"DDR4_DataResistors.pas ({len(data)} resistors)")
    print("DRAM X:", DRAM_X, " U4-U5 centre spacing:", round(DRAM_X[4] - DRAM_X[3], 2), "mm")


if __name__ == "__main__":
    main()
