# Design Notes

The locked decisions and the engineering data taken from the reference documents. Section references point to the documents listed in [SOURCES.md](SOURCES.md).

## 1. Locked decisions

| Decision | Value | Reason |
|---|---|---|
| Memory generation | DDR4 | DDR5 modules need an on-module PMIC and an SPD hub, and neither is sold through authorized distributors. DDR4 takes all its power from the motherboard. |
| Module type | 288-pin UDIMM, gold fingers | Standard desktop memory |
| Capacity | 16 GB | — |
| Speed | DDR4-3200 | Highest standard DDR4 UDIMM speed in JESD21-C 4.20.26 |
| Reference design | Raw Card **A3** (1 rank, x8, planar, non-ECC) | The only single-rank card that reaches 16 GB (8 × 16 Gb). A3 supports DRAM outlines up to 10.2 × 11.0 mm, and ours is 7.5 × 11.0 mm. |
| Rejected: Raw Card C | — | 1 rank x16, 4 DRAMs: **8 GB maximum** |
| DRAM | **Micron MT40A2G8SA-062E:F** (16 Gb, x8, DDR4-3200 CL22, 78-ball SA package 7.5 × 11 mm) | Active at Digi-Key. Has an official Altium model (Ultra Librarian, same-package IT:F variant). JEDEC-standard x8 ballout. |
| Rejected: Alliance AS4C2G8D4A-62BCN | — | No official CAD model exists (replaced 17 Sep 2026) |
| Passive size | 0402 minimum (0603 for bulk) | The main spec does not allow 0201 on UDIMM reference designs |

## 2. Mechanical (MO-309 Issue F, main spec §6.8)

| Parameter | Value |
|---|---|
| Finger pitch | 0.85 mm |
| Pins | 288 (1–144 front, 145–288 back) |
| PCB thickness across fingers | **1.40 ± 0.10 mm** (without solder mask) |
| Component area | Starts ≥ 4.00 mm above the finger edge |
| Edge chamfer (optional, Detail X) | 0.05–0.20 mm |
| Max total module thickness (single-sided) | 2.7 mm (Micron CT8G4DFS8 drawing), so parts must be ≤ 1.2 mm tall |
| Contact finish | Hard gold 0.76 µm min over nickel 2.00 µm min (MO-309 plating code xxAx) |
| Board | 133.35 × 31.25 mm; top corners 1.25 × 45° |
| Fingers | 0.60 wide; tops at 2.60 above datum B; 0.25 bare strip above the edge; edge at 0.50 in the end zones, 0 in the centre, ramps over pins 35–47 and 105–117 |
| Key notch | 1.50 wide, 3.85 deep, full radius; centre x = 72.25 from the left end (4.30 from pin 77, 1.65 from pin 78) |
| Latch notches | Both ends, y 8.00–11.00 and 14.60–17.60, 2.10 deep, R0.65 inner corners |

Full dimensioned drawings and the Altium build steps: [FOOTPRINT_EDGE.md](FOOTPRINT_EDGE.md).

## 3. PCB stackup — Annex A "PCB Fabrication Table of A2 and A3"

| Layer | Use | Cu (oz) | Dielectric below (µm) |
|---|---|---|---|
| L1 | DQ, Address/CK | ½ + plating | 70 |
| L2 | VDD, GND | ½ | 80 |
| L3 | DQ, Address | ½ | 420 |
| L4 | VDD | ½ | 80 |
| L5 | Address | ½ | 420 |
| L6 | Address/CK | ½ | 80 |
| L7 | VDD, GND | ½ | 70 |
| L8 | DQ, Address/CK | ½ + plating | — |

**Impedance targets**

| Trace | Width (mm) | Impedance |
|---|---|---|
| Single-ended | 0.10 | 50 Ω ± 10 % |
| Single-ended | 0.075 | 55 Ω ± 10 % |
| Single-ended | 0.15 | 40 Ω ± 10 % |
| Differential | 0.10 / 0.10 space | 83 Ω ± 15 % |
| Differential | 0.075 / 0.10 space | 93 Ω ± 15 % |
| Differential | 0.15 / 0.10 space | 70 Ω ± 15 % |

Minimum trace width is 0.075 mm (Annex A). The fab's capability still needs to be confirmed.

**As built in the PcbDoc (Layer Stack Manager, 2026-09-22).** Copper names: L1 `Top Layer 1`, L2 `L2_PWR_GND`, L3 `L3_DQ_ADDR`, L4 `L4_VDD`, L5 `L5_ADDR`, L6 `L6_ADDR_CK`, L7 `L7_PWR_GND`, L8 `Bottom Layer 1`. Outer copper 1.4 mil (½ oz + plating), inner 0.7 mil, all dielectrics **Dk 4.2** (PP-006 prepreg, FR-4 core between L4 and L5), solder resist 0.4 mil Dk 3.5. Thickness without mask **1.398 mm**. Checked by `tools/check_stackup.py`.

Why Dk 4.2: the Annex A table gives 0.10 mm = 50 Ω, 0.075 mm = 55 Ω and 0.15 mm = 40 Ω on L3. With Dk 4.8 Altium needed 0.084 / 0.066 / 0.138 mm, which only fits the Annex A numbers at Dk ≈ 4.2–4.3 (typical FR-4 prepreg at DDR4 frequencies). The fab's material sets the real value; send them the Annex A impedance table for controlled-impedance tuning.

Widths Altium solves for each profile (mm; diff pairs at 0.10 mm gap), enabled on the layers Annex A uses:

| Profile | L1 / L8 | L3 | L5 | L6 | Annex A width |
|---|---|---|---|---|---|
| SE_50 (DQ) | 0.112 | 0.099 | 0.101 | 0.101 | 0.10 |
| SE_55 (Address/CK) | 0.091 | 0.078 | 0.080 | 0.080 | 0.075 |
| SE_40 | 0.171 | 0.157 | 0.160 | 0.160 | 0.15 |
| DIFF_83 (DQS) | 0.116 | 0.098 | — | 0.098 | 0.10 / 0.10 |
| DIFF_93 (CK) | 0.088 | — | — | 0.072* | 0.075 / 0.10 |
| DIFF_70 (CK) | 0.166 | 0.147 | — | 0.147 | 0.15 / 0.10 |

\* Below 0.075 mm, so it is routed at the Annex A width 0.075 / 0.10 (≈ 91 Ω, inside 93 Ω ± 15 %). The width rules (not the profiles) set the routed widths, using the Annex A column.

References: L1 → L2; L3 → L2 + L4; L5 and L6 → L4 + L7 (L5 and L6 never reference each other); L8 → L7. In the Impedance tab each row's Top/Bottom Ref names the layers *around* that row, not the row itself.

Notes:
- Picking a material from the library (e.g. `CF-004`) resets the copper weight to 1 oz. After changing a layer's material, retype 1/2 oz (0.01778 mm) on inner layers.
- Stackup edits live in the `[Stackup]` document: save that tab, then the PcbDoc (or File → Save All).
- L5 and L6 are adjacent signal layers (420 µm apart). Route them roughly orthogonal where they overlap to limit broadside coupling.

## 4. Resistor values — Annex A, Raw Card A3

| Net group | Component | Value | Qty |
|---|---|---|---|
| DQ[63:0], DQS[7:0]_t/_c, DM[7:0] | Series R1 | 15 Ω ± 5 % | **88** (64 DQ + 16 DQS + 8 DM) |
| A[16:0], BA[1:0], BG[1:0], ACT_n, PARITY | Termination to VTT | 39 Ω ± 5 % | 23 |
| CS0_n, CKE0, ODT0 | Termination to VTT | 39 Ω ± 5 % | 3 |
| CK0_t / CK0_c | R1, R2 + C2 to VDD (C1 = 0) | 39 Ω ± 5 %, 0.01 µF | 2 R + 1 C |
| CK1_t / CK1_c (unused) | R1 across the pair | 75 Ω ± 5 % | 1 |
| ALERT_n | R1, **pull-up to VDD** at the start of the chain, 2.5 mm before the first DRAM (U1); the net then runs U1 → U8 and back to the connector (Annex A p.12, main spec 6.3.7) | 47 Ω ± 5 % | 1 |
| ZQ (per DRAM) | RZQ to VSSQ | 240 Ω ± 1 % | 8 |

Annex A notes that these resistor values are recommendations, and changing any of them requires simulation.

## 5. Decoupling — main spec Table 9

| Rail | Minimum |
|---|---|
| VDD | 2 per SDRAM (at the VDD balls), plus 4 bulk per module |
| VTT | 1 per 2 termination resistors, plus 1 near the VTT finger |
| VPP | 1 per DRAM VPP ball (78-ball SA: B1 and M9, so 2 per DRAM), plus 1 near the VPP finger |
| VREFCA | 1 per DRAM (ball J1), plus 1 near the VREFCA finger |

Recommended values: 0.01 µF, 0.1 µF and 1.0 µF, with 4.7 µF for bulk.

## 6. Routing data — Annex A, Raw Card A3 (mm)

| Net | Key lengths |
|---|---|
| CK0 | TL0 4.4, TL1 120.5, TL2 0.6, connector to first SDRAM 125.0, TL3 12.8 / 12.8, TL4 46.3, connector to last SDRAM 253.0, TL5 13.0 |
| Address/command | Connector to first SDRAM 129.4–130.0, connector to last 253.0, TL5 13.0 |
| Control | Connector to first SDRAM 129.7–129.8, connector to last 253.0, TL5 12.9–13.1 |
| ALERT_n | TL0 2.5, TL1 46.3, TL2 0.6, TL3 12.8, TL5 30.0 |
| RESET_n | Total net length 258.2 ± 10 %, routed alongside the address bus |
| Unused CK1 | TL0 3.7 ± 0.8 |

The per-byte DQ lengths are in Annex A's data net table and will be turned into design rules later.

DRAM ball notes (Micron Rev H, Figure 5, verified from the rendered figure):

| Ball | Function | Connection |
|---|---|---|
| B1, M9 | VPP | 2.5 V, one decoupling cap each |
| J1 | VREFCA | From the connector's VREFCA pin, one decoupling cap |
| B9 | ZQ | 240 Ω 1 % to VSSQ |
| G9 | TEN/NF | Tie low (there is no TEN pin on the UDIMM connector) |
| N7 | A17 (x4 only); NF/NC on x8 | Not connected |
| N8 | A13 | Address bus |
| F2, G2, G8 | ODT1, CKE1, CS1_n (x8 SDP: NC) | Leave unconnected |

## 7. DRAM electrical rules (Micron Rev H)

| Rule | Value | Source |
|---|---|---|
| VDD, VDDQ | 1.14 / 1.2 / 1.26 V | p254 Table 79 |
| VPP | 2.375 / 2.5 / 2.75 V, and **VPP ≥ VDD at all times**; VPP ramps with or before VDD | p254, p37, p253 note 3 |
| VREFCA | = VDD/2, reference input only (draws no bias current), ±1 % VDD AC noise limit | p255 |
| **TEN (G9)** | Must be **LOW** in normal operation, and held below 0.2 × VDD for ≥ 700 µs at power-up → **tie to VSS** | p26, p37 |
| RESET_n | Low ≥ 200 µs at power-up (tPW_RESET_L); comes from the connector | p37, p364 |
| ZQ (B9) | 240 Ω ±1 % to **VSSQ**; max external load on ZQ is **5 pF**, so keep the trace short | p27, p301 note 12 |
| NF vs NC | NF = internally connected but unused; NC = no internal connection. Both are left open. | p27 |
| A17 (N7) | x8 uses A[16:0], so A17 is NF/NC → leave open | p2 Table 2, p23 |
| C0/C1/C2 (G2, G8, F2) | Stack-address inputs, NC on this single-die package → leave open | p25 |
| TDQS_c (A3) | x8 with TDQS disabled → not used | p27 |
| DM_n/DBI_n (A7) | Used: goes to the module's DM pin through a 15 Ω series resistor | p27, Annex A |

**Current budget (x8, DDR4-3200, die rev F, p324–325):** worst case per chip is IDD7 = 167 mA (burst read IDD4R = 140 mA, write 112 mA), so 8 chips ≈ **1.34 A on VDD**. IPP is ~3–6 mA per chip, ≈ 50 mA on VPP. This sets the VDD plane and bulk capacitor sizing.

## 8. SPD timing values (for Annex L programming)

Page size for 16 Gb x8 is **1 KB** (p2 Table 2), which selects the 1KB rows below.

| Parameter | Value | Source |
|---|---|---|
| Speed bin | DDR4-3200, -062E, **CL22-22-22** | p341 Table 158 |
| tCK (AVG) | 0.625 ns min, 1.9 ns max | p357 Table 161 |
| tAA / tRCD / tRP | 13.75 ns each | p341 |
| tRAS | 32 ns min | p341 |
| tRC | tRAS + tRP = 45.75 ns | p341 |
| tRFC1 / tRFC2 / tRFC4 (16 Gb) | 350 / 260 / 160 ns | p343, p365 |
| tREFI | 7.8 µs (0–85 °C) | p343 |
| tWR | 15 ns | p361 |
| tRTP | max(4CK, 7.5 ns) | p362 |
| tRRD_S / tRRD_L (1KB) | max(4CK, 2.5 ns) / max(4CK, 4.9 ns) | p361 |
| tFAW (1KB) | max(20CK, 21 ns) | p361 |
| tCCD_L | max(4CK, 5 ns) | p362 |

## 9. Schematic ERC status

Altium Designer 26.10.1 project validation completed on 2026-09-20 with **0 errors**. The saved schematics also pass the repository checks: 636/636 DRAM checks, 288/288 connector-pin checks, termination checks, BOM/project checks, edge-symbol checks, and edge-footprint/link checks.

The eight active Micron `ALERT_n` pins (ball L9) are typed `Open Collector`, matching the shared pull-down alert topology. Eight off-grid VPP power ports—one on each DRAM sheet—were moved to the 100 mil schematic grid while preserving their wiring.

The remaining 32 Altium warnings are reviewed board-boundary exceptions, not missing on-module drivers. The motherboard drives these nets through the passive DIMM edge connector J1, so the external source is outside this schematic project:

`A0–A13`, `A15_CAS`, `A16_RAS`, `ACT`, `BA0–BA1`, `BG0–BG1`, `CK0_C`, `CK0_T`, `CKE`, `CS`, `ODT`, `PAR`, `RESET_N`, `SA0–SA2`, and `WE`.

These warnings remain visible rather than weakening the project-wide ERC rule or applying generic No-ERC suppression.

## 10. PCB design rules

Set in Altium block by block; `tools/check_rules.py` checks every value, scope and priority below.

**Clearance (Block 1)**

| Rule | Scope | Clearance (mm) |
|---|---|---|
| Clearance_LineToShape | anything ↔ InPolygon | 0.20 |
| Clearance_GoldFingers | J1 ↔ J1 | 0.20 |
| Clearance_ViaToBGA | via ↔ DRAM (SA_MFG) pad | 0.175 |
| Clearance_ViaToOtherPad | via ↔ pad | 0.15 |
| Clearance_ViaToVia | via ↔ via | 0.20 |
| Clearance_LineToPad | track ↔ pad | 0.125 |
| Clearance_PadToPad | pad ↔ pad, ignored inside a footprint | 0.25 |
| Clearance (default) | all | 0.10 |
| ComponentClearance_Physical | parts, J1 excluded | 0.25 |

The default ComponentClearance (All ↔ All) is disabled: J1's footprint carries the whole board outline, so every part would collide with it. Altium's query for polygon copper is `InPolygon`; `IsPoly` is not valid and Altium deletes the rule when asked to "correct" it.

**Width (Block 2)** — from the Annex A fabrication table (section 3)

| Priority | Rule | Nets | Min | Preferred | Max |
|---|---|---|---|---|---|
| 1 | Width_POWER | POWER | 0.15 | 0.30 | 2.00 |
| 2 | Width_CK | CK, CK_UNUSED | 0.075 | 0.075 | 0.15 |
| 3 | Width_ADDR_CTRL | ADDR, CTRL, RESET, ALERT | 0.075 | 0.075 | 0.15 |
| 4 | Width_DATA | DATA (DQ, DQS, DM) and DATA_DRAM | 0.075 | 0.10 | 0.10 |
| 5 | Width_SPD | SPD | 0.10 | 0.15 | 0.30 |
| 6 | Width (default) | everything else (ZQ, termination nodes, …) | 0.075 | 0.10 | 0.30 |

Max 0.15 on address/clock allows the 40 Ω / 70 Ω segments; min 0.075 on DQ allows neck-down between DRAM balls.

**Differential pairs (Block 3)**

| Pair | Positive | Negative |
|---|---|---|
| CK0, CK1 | CKn_T | CKn_C |
| DQS0 … DQS7 (connector ↔ 15 Ω) | DQSn_T | DQSn_C |
| DQS0_DRAM … DQS7_DRAM (15 Ω ↔ DRAM) | NetR(12n+9)_1 | NetR(12n+10)_1 |

On DRAM sheet n (U1 = 0 … U8 = 7) the ZQ resistor is R(12n+1), the data resistors R(12n+2)…R(12n+12), with DQS_t on R(12n+9) and DQS_c on R(12n+10). Classes: DP_DQS (16 pairs), DP_CK (CK0, CK1).

| Priority | Rule | Scope | Width min / pref / max | Gap min / pref / max | Max uncoupled |
|---|---|---|---|---|---|
| 1 | DiffPair_DQS | DP_DQS | 0.075 / 0.10 / 0.10 | 0.10 / 0.10 / 0.127 | 3 mm |
| 2 | DiffPair_CK | DP_CK | 0.075 / 0.075 / 0.15 | 0.10 / 0.10 / 0.127 | 3 mm |
| 3 | DiffPairsRouting | all | 0.075 / 0.10 / 0.15 | 0.10 / 0.10 / 0.127 | 3 mm |

**Routing layers (Block 4)** — Annex A A3 layer use; L2, L4, L7 are kept for VDD/GND planes

Net class **DATA_DRAM** holds the 88 resistor-to-DRAM data nets: `NetRn_1` for n = 2…96 except the ZQ nets n = 12k+1 (1, 13, 25, 37, 49, 61, 73, 85).

| Priority | Rule | Nets | Allowed layers |
|---|---|---|---|
| 1 | RoutingLayers_POWER | POWER | all |
| 2 | RoutingLayers_DATA | DATA, DATA_DRAM | L1, L3, L8 |
| 3 | RoutingLayers_CK | CK, CK_UNUSED | L1, L6, L8 |
| 4 | RoutingLayers_ADDR | ADDR, CTRL, RESET, ALERT | L1, L3, L5, L6, L8 |
| 5 | RoutingLayers (default) | everything else | L1, L3, L5, L6, L8 |

In rules, Altium names the inner copper Mid Layer 1–6 (= L2–L7).

**Vias and fanout (Block 5)**

The DRAM footprint `SA_MFG` (read from the PcbDoc) has 78 round pads of 0.34 mm at 0.8 mm pitch, 13 rows × 3 + 3 columns with the middle three columns empty, matching the Micron 78-ball SA ballout. A via centred between four balls sits 0.566 mm from each ball centre, so with a 0.17 mm pad radius and the 0.175 mm via-to-BGA clearance its pad can be at most 0.44 mm. One 0.075 mm trace between two balls needs 0.075 + 2 × 0.125 = 0.325 mm of the 0.46 mm gap.

| Priority | Rule | Nets | Via Ø min / pref / max | Hole min / pref / max |
|---|---|---|---|---|
| 1 | RoutingVias_POWER | POWER | 0.40 / 0.45 / 0.45 | 0.20 / 0.25 / 0.30 |
| 2 | RoutingVias | all | 0.40 / 0.40 / 0.45 | 0.20 / 0.20 / 0.25 |

**Polygon pours (Block 6)** — L2, L4 and L7 are signal-type layers carrying VDD/GND polygon pours, so Altium's Power Plane rules don't apply; the polygon rules do.

| Priority | Rule | Scope | Connection |
|---|---|---|---|
| 1 | PolygonConnect_Vias | vias | direct (solid) |
| 2 | PolygonConnect | everything else | thermal relief, 4 spokes × 0.20 mm, 0.20 mm air gap, 90° |

Pours so far: **L4_VDD_POUR** — net VDD on L4, rectangle (0, 1)–(133.35, 31.25), solid, pour over all same-net objects, 3948.7 mm². It starts 1 mm above the finger edge so the bevel never exposes inner copper. "Remove Dead Copper" stays **off** until VDD vias exist: with no VDD object on L4 yet, Altium deletes the whole pour as dead copper (area 0). L2/L7 (GND under the data band, VDD under the address band, per Table 12) and the VTT/VPP islands are drawn after routing. A large pour can be shelved (Polygon Manager → Shelving) while routing and repoured at the end; L4_VDD_POUR is currently shelved.

**Solder mask:** all vias are tented (rule SolderMask_TentedVias, IsVia, tented top and bottom). Untented fan-out vias between the 0.8 mm-pitch DRAM balls left mask dams under 0.254 mm (2809 Minimum Solder Mask Sliver warnings), and tenting also stops solder wicking from the balls into the vias.

**Placement (Block 7)**

| Rule | Setting | Why |
|---|---|---|
| Height | ≤ 1.2 mm (preferred 1.0) | single-sided module, 2.7 mm max total thickness (section 2) |
| PermittedLayers_TopOnly | top side only | single-sided module |
| Room_FingerZone | parts except J1 kept outside (0, 0)–(133.35, 4.0), top layer | MO-309: component area starts ≥ 4.00 mm above the finger edge |

Drawing a room with Define: press Shift+Space for 90° corners and place each vertex with J → L (jump to location); in 45° mode Altium cuts the corners.

Fanout_BGA (scope `HasFootprint('SA_MFG')`, because the Vault DRAM footprint is not flagged as a BGA so `IsBGA` matched nothing): BGA style, away from centre, vias centred between pads. Run with Route → Fanout → Component, *Fanout Pads Without Nets* off, *Outer 2 Rows* on, *escape diff pairs first* on: 51 vias per DRAM (42 × 0.40/0.20, 9 × 0.45/0.25 power). Hole size 0.2–0.3 mm, minimum annular ring 0.1 mm, hole-to-hole 0.254 mm. All vias are through-hole (1.40 mm board, 0.2 mm drill = 7:1 aspect ratio).

**Length matching (for Block 8)** — main spec §6.3, Tables 10–12 and §6.4 (DDR4-3200 is a "higher speed" design). All lengths are velocity-compensated stripline equivalents: microstrip length ÷ 1.1.

| Group | Rule |
|---|---|
| CK_t ↔ CK_c, DQS_t ↔ DQS_c | match segment by segment within 0.1 mm |
| CTRL (CS, CKE, ODT) | within 1.0 mm of each other, and within CK ± 0.5 mm, connector → each DRAM |
| ADDR/CMD | within 1.0 mm of each other, and within CK ± 0.5 mm (1-rank), connector → each DRAM |
| TL2 stubs (via → DRAM ball) | ≤ 3.0 mm, matched per signal within ± 1.5 mm |
| CK first → last DRAM | ≤ 153 mm |
| Neck-down (end of TL1 at 0.1 mm) | 5.0–10.0 mm, matched ± 2.0 mm |
| DQ/DM ↔ DQS in a byte | within DQS ± 1.0 mm, connector → DRAM |
| Byte lane length | 12.0–32.0 mm (Annex A A3: 11.1–13.7 mm per byte; DQ lengths may move ± 0.8 mm at ≥ 2666) |
| Higher-speed allowances (§6.4) | address DRAM → DRAM ± 5 mm, first → second DRAM ± 10 mm, U4 → U5 ± 20 mm; CK/CTRL adjusted to keep timing |
| Via compensation | required inside a byte lane when via counts differ (e.g. 2.6 mm for an outer-to-outer via) |

Plane referencing (Table 12): DQ/DQS reference **GND**; address, command, control, clock and VREFCA reference **VDD**.

The routing-space rules (Table 14) match what is set: small via 0.20/0.40 mm (anti-pad 0.60), line–line 0.10, diff line–line 0.10, line–pad 0.125, line–shape 0.20, pad–pad 0.25. Table 14's large via (0.25/0.45 mm) is the power via.

**xSignals (Block 8)** — made with Design → xSignals → Run xSignals Wizard → On-Board DDR3/DDR4, controller = J1, memory = U1–U8, fly-by order U1 → U8.

| Class | xSignals | Rule |
|---|---|---|
| ADDR_PP1 … ADDR_PP8 | 28 each, J1 → that DRAM: A0–A13, A15_CAS, A16_RAS, ACT, BA0/1, BG0/1, CK0_T/C, CKE, CS, ODT, PAR, WE | MatchedLengths_ADDR_PPn, 1.0 mm |
| (CK pair in every ADDR class) | CK0_T / CK0_C | MatchedLengths_DDR_CLOCKS_STROBES, 0.1 mm within the pair |

Data byte lanes: none of Altium's xSignal tools (wizard data group, Create xSignals between Components with "Through 1 series component", pin-pair Create xSignals) found the finger → 15 Ω → DRAM paths on this board. Each byte is therefore matched in two halves: the finger-side nets (class BYTEn) within 0.5 mm and the DRAM-side nets (class BYTEn_DRAM = NetR(12n+2)_1 … NetR(12n+12)_1) within 0.5 mm, so every full DQ/DM path stays within DQS ± 1.0 mm (Table 11). Rules: ML_BYTEn (net class BYTEn) and ML_BYTEn_DRAM (BYTEn_DRAM), Matched Lengths, group matched, length units, 0.5 mm. The full compensated finger-to-ball lengths are checked by script after routing. Selecting a net class in the PCB panel with "Select" ticked selects all its nets; a pin-pair xSignal made then spans all of them (two such test xSignals were deleted).

Wizard notes: the Addresses pattern `A[#]` misses A10_AP and A12_BC, and BG0/BG1, ACT, PAR, CKE are not picked up, so add them with "Modify Nets in xSignal Classes"; RAS/CAS patterns `_RAS` / `_CAS` match A16_RAS / A15_CAS. The data group cannot trace through the 15 Ω series resistors, so the byte lanes are made separately.

**Length tuning style.** Serpentines and skew bumps use 45° mitered corners (Altium length tuning: Accordion, Mitered Lines, miter 50 %, amplitude ≤ 0.4 mm near the DRAMs, spacing 0.3 mm = 3 × width). At DDR4-3200 edge rates a 90° corner on a 0.10 mm trace has no measurable signal effect; mitering is kept for etch quality and consistency. The coupled part of a pair has no room for bumps (0.1 mm to its partner), so pair skew is corrected where the two lines separate.

## 11. Open items

- [ ] Download official CAD models for every BOM part (see [CAD_MODELS.md](CAD_MODELS.md))
- [ ] Check the Ultra Librarian DRAM footprint against Micron Figure 9 (SA package)
- [ ] Final decoupling-capacitor counts (schematic step)
- [ ] Confirm the fab supports 0.075 mm traces, 8 layers, 1.40 mm thickness and hard gold with bevel
- [ ] SPD contents per Annex L (UDIMM), and the programming method
- [ ] Silk To Silk Clearance: disabled during placement is fine; tidy designators and re-enable before fab outputs
- [ ] Schematic part data: DRAM Comment says `MT40A2G8SA-062E IT:F` (BOM: `:F`); no MPN parameter on the 240 Ω, 1.0 µF, 4.7 µF and 0.01 µF parts; 0.1 µF datasheet link points to a 470 pF part
- [ ] Project library paths are absolute (`D:\Projects\...`); make them relative
- [ ] 204 of 206 parts come from the Altium Content Vault; snapshot them into a repo PcbLib/SchLib
