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
| Contact finish | Gold plated (Annex A, "Cross Section Recommendations") |

Finger, notch and outline dimensions will be taken from MO-309 sheets 2–13 in the library step.

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

## 4. Resistor values — Annex A, Raw Card A3

| Net group | Component | Value | Qty |
|---|---|---|---|
| DQ[63:0], DQS[7:0]_t/_c | Series R1 | 15 Ω ± 5 % | 80 |
| A[16:0], BA[1:0], BG[1:0], ACT_n, PARITY | Termination to VTT | 39 Ω ± 5 % | 23 |
| CS0_n, CKE0, ODT0 | Termination to VTT | 39 Ω ± 5 % | 3 |
| CK0_t / CK0_c | R1, R2 + C2 to VDD (C1 = 0) | 39 Ω ± 5 %, 0.01 µF | 2 R + 1 C |
| CK1_t / CK1_c (unused) | R1 across the pair | 75 Ω ± 5 % | 1 |
| ALERT_n | R1 | 47 Ω ± 5 % | 1 |
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

## 7. Open items

- [ ] Download official CAD models for every BOM part (see [CAD_MODELS.md](CAD_MODELS.md))
- [ ] Check the Ultra Librarian DRAM footprint against Micron Figure 9 (SA package)
- [ ] Final decoupling-capacitor counts (schematic step)
- [ ] Confirm the fab supports 0.075 mm traces, 8 layers, 1.40 mm thickness and hard gold with bevel
- [ ] SPD contents per Annex L (UDIMM), and the programming method
