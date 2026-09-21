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

**As built in the PcbDoc (Layer Stack Manager, 2026-09-21).** Copper names: L1 `Top Layer 1`, L2 `L2_PWR_GND`, L3 `L3_DQ_ADDR`, L4 `L4_VDD`, L5 `L5_ADDR`, L6 `L6_ADDR_CK`, L7 `L7_PWR_GND`, L8 `Bottom Layer 1`. Outer copper 1.4 mil (½ oz + plating), inner 0.7 mil, all dielectrics Dk 4.8 (PP-006 prepreg, FR-4 core between L4 and L5), solder resist 0.4 mil Dk 3.5. Thickness without mask **1.398 mm**. Checked by `tools/check_stackup.py`.

Widths Altium solved for each profile (mm; diff pairs at 0.10 mm gap):

| Profile | L1 / L8 | L3 | L5 | L6 |
|---|---|---|---|---|
| SE_50 (50 Ω ±10 %) | 0.100 | 0.084 | 0.086 | 0.084* |
| SE_55 (55 Ω ±10 %) | 0.080 | 0.066 | 0.067 | 0.066* |
| SE_40 (40 Ω ±10 %) | 0.155 | 0.138 | 0.141 | 0.138* |
| DIFF_83 (83 Ω ±15 %) | 0.104 | 0.082 | — | 0.083 |
| DIFF_93 (93 Ω ±15 %) | 0.078 | 0.059 | — | 0.059 |
| DIFF_70 (70 Ω ±15 %) | 0.150 | 0.126 | — | 0.127 |

\* L6 single-ended rows still reference L5 (a signal layer); the reference must be L4, which widens them slightly (to about the L5 values). Pending fix.

Notes:
- SE_55 and DIFF_93 on the inner layers come out **below the 0.075 mm Annex A minimum**. Use those two profiles on L1/L8 only, or confirm the fab can etch 0.06 mm.
- L5 and L6 are adjacent signal layers (420 µm apart). Route them roughly orthogonal where they overlap to limit broadside coupling.

## 4. Resistor values — Annex A, Raw Card A3

| Net group | Component | Value | Qty |
|---|---|---|---|
| DQ[63:0], DQS[7:0]_t/_c, DM[7:0] | Series R1 | 15 Ω ± 5 % | **88** (64 DQ + 16 DQS + 8 DM) |
| A[16:0], BA[1:0], BG[1:0], ACT_n, PARITY | Termination to VTT | 39 Ω ± 5 % | 23 |
| CS0_n, CKE0, ODT0 | Termination to VTT | 39 Ω ± 5 % | 3 |
| CK0_t / CK0_c | R1, R2 + C2 to VDD (C1 = 0) | 39 Ω ± 5 %, 0.01 µF | 2 R + 1 C |
| CK1_t / CK1_c (unused) | R1 across the pair | 75 Ω ± 5 % | 1 |
| ALERT_n | R1, **pull-up to VDD** at the far end of the fly-by chain (not in series) | 47 Ω ± 5 % | 1 |
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

## 10. Open items

- [ ] Download official CAD models for every BOM part (see [CAD_MODELS.md](CAD_MODELS.md))
- [ ] Check the Ultra Librarian DRAM footprint against Micron Figure 9 (SA package)
- [ ] Final decoupling-capacitor counts (schematic step)
- [ ] Confirm the fab supports 0.075 mm traces, 8 layers, 1.40 mm thickness and hard gold with bevel
- [ ] SPD contents per Annex L (UDIMM), and the programming method
- [ ] Stackup: set the L6 single-ended impedance reference to L4 (section 3)
- [ ] Component placement: all 206 parts are imported to the PCB but still outside the board (only J1 placed)
