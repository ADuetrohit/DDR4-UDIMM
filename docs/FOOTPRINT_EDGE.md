# Gold-Finger Footprint and Board Outline

Footprint **`DDR4_UDIMM_288_MO309`** in `hardware/libraries/DDR4_UDIMM.PcbLib`: 288 contact pads, the board outline on Mechanical 1, and solder-mask windows over the fingers.

- Source: JEDEC **MO-309 Issue F** (288-pin DDR4 DIMM, 0.85 mm pitch), sheets 2–8, cross-checked against JESD21-C 4.20.26 §6.8.
- Generator (single source of truth): `tools/gen_edge_footprint.py`. It writes:
  - the pad table `hardware/libraries/edge_connector/DDR4_UDIMM_288_footprint_pads.csv`;
  - the Altium script `hardware/scripts/DDR4_Edge_Footprint.pas`, which builds the footprint;
  - the script project `DDR4_Edge_Footprint.PrjScr` that Run Script opens.
- Checker: `tools/check_edge_footprint.py` reads the saved PcbLib and compares every pad, outline segment and mask window with the generator.

**Coordinates:** mm, front view (component side = Altium **Top**), pin 1 on the left. The origin is at **x = 0 on the left board end** and **y = 0 at datum B**, the lowest part of the finger edge.

## 1. Whole board (front view)

```
 x=0                                                                                   x=133.35
  ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾╲  y=31.25
  │                                                                                         │  1.25 x 45° corners
  │                                                                                         │
  ├─┐ 17.60                          COMPONENT AREA                                  17.60 ┌─┤
  ├─┘ 14.60                    (front = Top layer, all 8 DRAMs)                      14.60 └─┤  latch notches,
  ├─┐ 11.00                                                                          11.00 ┌─┤  2.10 deep,
  ├─┘  8.00                                                                           8.00 └─┤  both ends
  │                                                                                         │
  │ · · · · · · · · · · · · · · no components below y = 4.00 · · · · · · · · · · · · · · · │  y=4.00
  │  ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮     ╭╮ ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮  │  pad tops y=2.60
  └──────────────────╲______________________________│|_______________________╱──────────────┘
   y=0.50  pins 1-35  ramp   pins 47-77  (y=0)    key   pins 78-105 (y=0)  ramp  117-144 y=0.50
                     35→47                       x=72.25               105→117
```

| Item | Value | MO-309F |
|---|---|---|
| Board length D | **133.35** (133.20–133.50) | sheet 2 |
| Board height A | **31.25** (31.10–31.40) | sheet 2 |
| Thickness across the fingers | **1.40 ± 0.10** | View A-A, sheet 3 |
| Top corners | **1.25 × 45°** chamfer (allowed 1.00–1.50, or R1.00–1.50) | Detail W |
| Bottom corners | square (0.80 max chamfer allowed) | Detail W |
| Component area | y ≥ **4.00**, and ≥ 2.50 from each board end | sheets 3, 8 |
| Default tolerance | ±0.15 | |

## 2. Finger rows

```
        pin 1                pin 35      pin 47            pin 77   KEY   pin 78         pin 105     pin 117          pin 144
 front  ▮ ▮ ▮ ▮ ... ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ... ▮ ▮ ▮ ▮   ╭╮   ▮ ▮ ▮ ... ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ... ▮ ▮ ▮
 x      3.35                 32.25       42.45             67.95  72.25  73.90          96.85       107.05          130.00
 back   145 ..................179 ........191 ..............221          222 ............249 .........261 .............288
        (each back pad sits directly behind the front pad: pad 145 behind pad 1)

        |<---- 28.90 ----->|<-10.20->|<----- 25.50 ----->|<-4.30->|<1.65>|<---- 22.95 ---->|<-10.20->|<---- 22.95 ---->|
                                                          |<----- 5.95 ----->|
```

| Pads | x of pad centre |
|---|---|
| 1–77 (front, Top) · 145–221 (back, Bottom) | 3.35 + (n − 1) × 0.85 (n = front pin) |
| 78–144 (front, Top) · 222–288 (back, Bottom) | 73.90 + (n − 78) × 0.85 |

The key is **not** centred between pins 77 and 78: it is 4.30 from pin 77 and 1.65 from pin 78, and 5.575 to the right of the board centre (D1). Sheets 2 and 4 both show this.

## 3. Pad shape and length

```
        ┌──────┐  y = 2.60   ← every pad top is at the same height
        │      │
        │ gold │  0.60 wide (± 0.03), 0.85 pitch
        │      │  rectangular SMD, no solder paste
        └──────┘  y = edge + 0.25
         ░░░░░░   0.25 non-metallised strip (A2, 0.10–0.40)
   ─────────────── board edge (height depends on the zone)
```

| Front pins | Back pins | Board edge y | Pad bottom y | Pad length | Pad centre y |
|---|---|---|---|---|---|
| 1–35 | 145–179 | 0.50 | 0.75 | **1.85** | 1.675 |
| 36–46 | 180–190 | ramp 0.458 → 0.042 | edge + 0.25 | 1.892 → 2.308 | per CSV |
| 47–105 | 191–249 | 0 | 0.25 | **2.35** | 1.425 |
| 106–116 | 250–260 | ramp 0.042 → 0.458 | edge + 0.25 | 2.308 → 1.892 | per CSV |
| 117–144 | 261–288 | 0.50 | 0.75 | **1.85** | 1.675 |

The ramps are straight lines between pin centres 35 → 47 and 105 → 117 (10.20 mm each, Details U and T). On the ramp, the pad and its non-metallised strip are measured on the pad centre line (Detail P). MO-309 also allows a neck at the bottom of each pad (0.45 min wide, Detail R). A full-width 0.60 pad meets that.

## 4. Key notch (Detail Z)

```
                 R0.75 full radius
                   ╭────╮          y = 3.85 ± 0.10  (top of the notch)
                   │    │
     pin 77        │    │        pin 78
     ▮ 67.95       │    │     ▮ 73.90
                   │    │
  ─────────────────╯    ╰──────────────   y = 0 (datum B)
                 71.50  73.00
          0.20 x 45° chamfer at both mouth corners (0.20 ± 0.15; or R0.35 max)
          width 1.50 ± 0.05, centred on x = 72.25 (datum A)
```

## 5. Latch notches (Detail W, both ends, same shape)

```
   right end (the left end is the mirror image)

        131.25  131.90        133.35 = board end
            │      │              │
   17.60 ─ ─│─ ─ ─ ╭──────────────┤
            │ R0.65                 1.45 flat (min)
            │                     ← 2.10 deep
            │
   14.60 ─ ─│─ ─ ─ ╰──────────────┤
                                  │
   11.00 ─ ─ ─ ─ ─ ╭──────────────┤
            │ R0.65
            │
    8.00 ─ ─ ─ ─ ─ ╰──────────────┤
                                  │
                                  │   square corner
    0.50 ─────────────────────────┘   (bottom of the end zone)
```

Notches at **y 8.00–11.00** and **14.60–17.60**. They are **2.10** deep from each end, with **R0.65** inner corners and square outer corners.

## 6. Solder mask

A single mask window on **Top Solder** and **Bottom Solder** covers each finger group. It runs from x = 2.85 to 68.45 and from 73.40 to 130.50, and from y = −0.30 to 2.75, so no mask slivers are left between fingers. The window's outer edges stay ≥ 2.80 from the board ends (Detail W). Paste is removed on every finger (Paste Mask Expansion: Manual, −1.5 mm).

## 7. Build it in Altium

1. **Create the library.**
   1. In the Projects panel, right-click the project, then **Add New to Project → PCB Library**.
   2. **File → Save As** `D:\Projects\DDR4-UDIMM\hardware\libraries\DDR4_UDIMM.PcbLib`.
2. **Run the script.**
   1. With the PcbLib open and clicked into, choose **File → Run Script… → Browse**. This dialog only opens script projects.
   2. Open `hardware\scripts\DDR4_Edge_Footprint.PrjScr`.
   3. Expand `DDR4_Edge_Footprint.pas`, select **CreateEdgeFootprint**, then **OK**.
   4. A message confirms 288 pads. Run the script only once.
3. **Delete the empty `PCBCOMPONENT_1`.** In the PCB Library panel, right-click it and choose Delete.
4. **Remove paste from the fingers.**
   1. Click any finger, then right-click → **Find Similar Objects** → *Object Kind: Same* → OK. All 288 pads are now selected.
   2. In the Properties panel, set **Paste Mask Expansion → Manual, −1.5 mm**.
5. **Save (Ctrl+S)**, then run the checker:
   ```
   py -3.11 tools/check_edge_footprint.py hardware/libraries/DDR4_UDIMM.PcbLib
   ```
6. **Attach the footprint to the connector symbol.**
   1. In `DDR4_UDIMM.SchLib`, select the component, then Properties → **Footprint → Add**.
   2. Browse to **DDR4_UDIMM_288_MO309** and click OK. Pins map 1:1 by designator.
   3. Save, then run **Tools → Update Schematics** so J1A–J1E in `edge.SchDoc` get the footprint.
   4. Check it:
   ```
   py -3.11 tools/check_edge_footprint.py hardware/libraries/DDR4_UDIMM.PcbLib --sch hardware/libraries/DDR4_UDIMM.SchLib
   ```

The outline in the footprint is a reference. When the PcbDoc is created, it also becomes the board shape: copy it to Mechanical 1 of the PcbDoc and use **Design → Board Shape → Define from selected objects**.

## 8. Fabrication notes (for the output step)

| Item | Requirement | Source |
|---|---|---|
| Contact plating | Hard gold **0.76 µm (30 µin) min** over nickel **2.00 µm min** | MO-309 plating code xxAx |
| Edge bevel | Optional. If used, **0.05–0.20 × 0.05–0.20 mm** only, so it stays inside the 0.25 mm bare strip | Detail X |
| Plating tie bars | Allowed: 0.20 wide, running to the module edge | sheet 6 |
| Thickness | 1.40 ± 0.10 over the fingers, without solder mask | View A-A |
| Mask | Open over all fingers (section 6) | |

Ask the fab whether it adds its own plating bus for hard gold or needs the fingers extended to the edge.
