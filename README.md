# DDR4-UDIMM — 16 GB DDR4-3200 Desktop Memory Module

A custom 288-pin DDR4 unbuffered DIMM with hard-gold edge fingers, designed in Altium Designer. It follows the JEDEC reference design **Raw Card A3**.

## Specification

| Item | Value |
|---|---|
| Form factor | 288-pin UDIMM, 0.85 mm finger pitch (JEDEC MO-309) |
| Standard | JESD21-C 4.20.26 (Rev 1.22) + Annex A, Raw Card **A3** (Rev 3.01) |
| Capacity / organization | 16 GB, 1 rank, x8, non-ECC |
| Speed | DDR4-3200 (PC4-3200) |
| Memory ICs | 8 × Micron **MT40A2G8SA-062E:F** (16 Gb x8, DDR4-3200 CL22, 78-ball FBGA 7.5 × 11 mm) |
| SPD | Microchip **34AA04T-I/MUY** (EE1004, no thermal sensor) |
| PCB | 8 layers, **1.40 ± 0.10 mm** across the fingers, hard-gold contacts |
| Supplies (from motherboard) | VDD 1.2 V · VPP 2.5 V · VTT 0.6 V · VREFCA · VDDSPD 2.2–3.6 V |
| Component height limit | ≤ 1.2 mm (single-sided module) |

Full details: [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) · Placement: [docs/PLACEMENT.md](docs/PLACEMENT.md) · Parts: [bom/BOM_v4.csv](bom/BOM_v4.csv) · DRAM wiring: [docs/SCHEMATIC_DRAM.md](docs/SCHEMATIC_DRAM.md) · Gold fingers + outline: [docs/FOOTPRINT_EDGE.md](docs/FOOTPRINT_EDGE.md) · CAD sources: [docs/CAD_MODELS.md](docs/CAD_MODELS.md)

## Progress

- [x] Architecture locked (DDR4-3200 UDIMM, 16 GB, Raw Card A3)
- [x] Reference documents collected ([docs/SOURCES.md](docs/SOURCES.md))
- [x] BOM with Digi-Key part numbers (current: v4, exact quantities + approved alternates)
- [ ] Official CAD models collected for every part *(sources identified: [docs/CAD_MODELS.md](docs/CAD_MODELS.md); downloads pending)*
- [ ] Libraries
  - [x] 288-pin gold-finger footprint `DDR4_UDIMM_288_MO309` in `hardware/libraries/DDR4_UDIMM.PcbLib`: built from MO-309F, verified by `tools/check_edge_footprint.py` (288 pads, 40-segment outline, mask windows, no paste) ([spec](docs/FOOTPRINT_EDGE.md))
  - [x] Attach the footprint to the connector symbol; J1A–J1E share one physical `DDR4_UDIMM_288_MO309` footprint
  - [x] SPD footprint (vendor model, UDFN-8)
  - [ ] DRAM footprint check vs Micron drawing *(pad grid verified: 78 × 0.34 mm pads, 0.8 mm pitch, 13 rows × 3+3 columns; body outline still to check)*; passives
- [x] Schematic — **complete and verified**: 11 sheets, 131 nets, every BOM line matches (`tools/check_project.py`)
  - [x] DRAM sheets U1–U8 wired, verified 636/636 by `tools/check_dram.py` ([spec](docs/SCHEMATIC_DRAM.md))
  - [x] 288-pin edge-connector symbol (`hardware/libraries/DDR4_UDIMM.SchLib`, 5 parts) — 288/288 pins verified vs JEDEC Table 5 ([guide](docs/SCHEMATIC_CONNECTOR.md))
  - [x] EDGE sheet: J1A–J1E wired, 288/288 pins verified by `tools/check_connector.py`; net names match all 8 DRAM sheets
  - [x] Termination sheet: 26 VTT terminations, CK0/CK1/ALERT networks, decoupling — verified by `tools/check_term.py` ([spec](docs/SCHEMATIC_SUPPORT.md#sheet-termschdoc))
  - [x] SPD sheet: 34AA04T-I/MUY wired and verified (8/8 pins) ([spec](docs/SCHEMATIC_SUPPORT.md#sheet-spdschdoc))
  - [x] Native Altium ERC: **0 errors**; 32 reviewed `no driving source` warnings are the address/command/clock/reset/SPD-address inputs driven externally through J1 ([record](docs/DESIGN_NOTES.md#9-schematic-erc-status))
- [x] Stackup and impedance profiles — verified by `tools/check_stackup.py` (PASS)
  - [x] 8-layer stack per Annex A: 70/80/420/80/420/80/70 µm, 1.398 mm without mask ([table](docs/DESIGN_NOTES.md#3-pcb-stackup--annex-a-pcb-fabrication-table-of-a2-and-a3))
  - [x] Dielectric Dk 4.2 so Altium's widths match the Annex A table (50 Ω = 0.10 mm, 55 Ω ≈ 0.078 mm, 40 Ω ≈ 0.15 mm on L3)
  - [x] Six impedance profiles on the Annex A layers; every reference is a plane (L2/L4/L7); DIFF_93 on L6 is routed at 0.075 mm (Annex A width)
- [x] Board outline, key notch, latch notches (MO-309) — real PcbDoc Board Shape verified at **133.35 × 31.25 mm**, generated from the connector's 31 tracks + 9 arcs ([spec](docs/FOOTPRINT_EDGE.md))
- [x] Component placement — all 206 parts at JEDEC-derived positions, fine-tuned by hand and recorded in `hardware/placement_final.csv`; verified 206/206 by `tools/check_placement.py` ([placement](docs/PLACEMENT.md))
  - [x] Positions from Annex A (data-net lengths, fly-by TL3/TL4/TL5, CK1 TL0) and Table 9 decoupling: `tools/gen_placement.py` → `hardware/placement.csv` + `hardware/scripts/DDR4_Placement.pas`
  - [x] Placed by script in Altium; DRAMs rotated 180° so the data balls face the fingers
  - [ ] Full DRC pass on the placed board; silkscreen designators tidied before fab outputs
- [x] Design rules — built block by block, verified by `tools/check_rules.py` ([rules](docs/DESIGN_NOTES.md#10-pcb-design-rules))
  - [x] 30 net classes: BYTE0–BYTE7, BYTE0_DRAM–BYTE7_DRAM, DQ, DQS, DM, DATA, ADDR, CTRL, CK, CK_UNUSED, RESET, ALERT, SPD, POWER (connector side of the 15 Ω resistors) and DATA_DRAM (the 88 resistor-to-DRAM nets)
  - [x] Block 1 — clearances: 0.10 mm general, track–pad 0.125, via–BGA pad 0.175, via–via 0.20, pad–pad 0.25 (not inside a footprint), anything–polygon 0.20, gold fingers 0.20; component clearance 0.25 (J1 excluded)
  - [x] Block 2 — widths: DATA 0.10 (min 0.075), ADDR/CTRL/CK 0.075 (max 0.15), POWER 0.3 (min 0.15), SPD 0.15, default 0.10
  - [x] Block 3 — differential pairs: 18 pairs (CK0, CK1, DQS0–7, and DQS0_DRAM–DQS7_DRAM between the 15 Ω resistors and the DRAMs), classes DP_DQS / DP_CK; DQS 0.10/0.10, CK 0.075/0.10 (max 0.15), gap 0.10–0.127, 3 mm max uncoupled
  - [x] Block 4 — routing layers: DATA (+ new class DATA_DRAM, 88 nets) on L1/L3/L8; CK on L1/L6/L8; ADDR/CTRL/RESET/ALERT and default on L1/L3/L5/L6/L8; POWER on all; L2/L4/L7 kept for planes
  - [x] Block 5 — vias: signal 0.40/0.20 mm (max 0.45 to fit between DRAM balls), POWER 0.45/0.25 mm (JEDEC Table 14 large via); BGA fanout centred between pads; holes 0.2–0.3 mm, annular ring ≥ 0.1 mm
  - [x] Block 6 — polygon pours (L2/L4/L7 are signal layers with VDD/GND pours): vias direct-connect, pads 4-spoke thermal relief 0.2/0.2 mm; 0.2 mm clearance from any object to polygon copper
  - [x] Block 7 — placement: height ≤ 1.2 mm, top side only, room `Room_FingerZone` keeps every part except J1 out of the bottom 4.0 mm (MO-309 component area)
  - [x] Block 8 — xSignals + length matching
    - [x] Address/command/clock: xSignal Multi-Chip Wizard (DDR4, fly-by J1 → U1 … U8) → classes ADDR_PP1–ADDR_PP8, 28 xSignals each; matched-length rules 1.0 mm per DRAM, CK pair 0.1 mm
    - [x] Data byte lanes: Altium's xSignal tools do not trace through the 15 Ω resistors on this board, so each half is matched instead — 16 rules ML_BYTEn (finger → resistor) and ML_BYTEn_DRAM (resistor → DRAM), 0.5 mm each, keeping every DQ/DM within DQS ± 1.0 mm; full lengths checked by script after routing
    - [x] DQS pairs matched within 0.1 mm (ML_DQS_PAIRS, Table 11)
- [ ] Power planes (JEDEC Table 12: DQ/DQS over GND; address, command, clock and VREFCA over VDD)
  - [x] L4: solid VDD pour `L4_VDD_POUR`, (0, 1)–(133.35, 31.25), 3948.7 mm², clipped to the notches
  - [ ] L2 / L7: GND under the data band, VDD under the address band — drawn after routing
- [ ] Routing
  - [x] Data lanes, finger → 15 Ω (TL0): **88 / 88** — 40 front-finger nets on L1 (2.95–3.20 mm), 48 back-finger nets L8 → via ≈ y 6.3 → L1 (5.45–5.81 mm); all 0.10 mm; DQS pairs matched within 0.042 mm
  - [ ] Data lanes, 15 Ω → DRAM balls (TL1–TL3): byte 0 complete (11/11): DM0 on L1, DQ1/DQ2/DQ5/DQ6/DQS0 pair on L3, crossing nets DQ0/DQ3/DQ4 on L8 and DQ7 on L3 (script `U1_Crossers.pas`); totals 9.95–17.66 mm, ≈48 mm of length tuning to do; length tuning after each byte is complete
  - [x] 88 × 15 Ω data resistors rotated to 270° so pad 2 (finger-side net) faces the fingers and pad 1 (DRAM side) faces the DRAM; placement script and placement_final.csv updated
  - [x] Vias tented (rule SolderMask_TentedVias) — clears ~2800 solder-mask-sliver warnings between fan-out vias and DRAM balls
  - [x] DRAM BGA fan-out U1–U8: 51 dog-bone vias each (42 signal 0.40/0.20 mm, 9 power 0.45/0.25 mm), vias centred between balls; Fanout_BGA now scoped to footprint SA_MFG
- [ ] Fabrication and assembly outputs
- [ ] Assembly, SPD programming, bring-up

## Repository layout

```
bom/        Bill of materials (versioned CSV)
docs/       Design notes and reference-source list
hardware/   Altium Designer project and libraries
  project/            Versioned PrjPcb, SchDoc and PcbDoc design sources
  libraries/vendor/   Official vendor CAD models, unmodified
  scripts/            Altium DelphiScripts generated by tools/ (run via File > Run Script)
tools/      Generators and checkers (SchDoc/SchLib/PcbLib readers, wiring checkers, stackup checker, edge-connector symbol + footprint generators)
```

Reference PDFs (JEDEC standards and vendor datasheets) are copyrighted, so they are **not committed**. [docs/SOURCES.md](docs/SOURCES.md) lists each one and where to get it. Place them in `docs/jedec/` and `docs/datasheets/` locally.

## Checking the design

```
py -3.11 tools/check_dram.py <sheet>.SchDoc      # every DRAM pin, resistor and capacitor vs the spec
py -3.11 tools/schdoc_nets.py <sheet>.SchDoc     # full netlist straight from the Altium file
py -3.11 tools/check_edge_symbol.py hardware/libraries/DDR4_UDIMM.SchLib   # 288 connector pins vs JEDEC
py -3.11 tools/check_connector.py edge.SchDoc     # every EDGE-sheet pin's net, shorts, default labels, No-ERC
py -3.11 tools/check_term.py TERM.SchDoc          # 26 VTT terminations, CK0/CK1/ALERT networks, decoupling rails
py -3.11 tools/check_project.py *.SchDoc          # whole schematic: dangling nets, shorts, part counts vs latest BOM
py -3.11 tools/gen_edge_footprint.py              # regenerate the gold-finger pad table + Altium build script
py -3.11 tools/check_edge_footprint.py hardware/libraries/DDR4_UDIMM.PcbLib [--sch <SchLib/SchDoc>]   # 288 pads, outline, mask vs MO-309
py -3.11 tools/check_stackup.py "hardware/project/DDR4-UDIMM — 16 GB DDR4.PcbDoc"   # layer stack, thickness, impedance profiles vs Annex A
py -3.11 tools/check_rules.py "hardware/project/DDR4-UDIMM — 16 GB DDR4.PcbDoc"     # design rules: scopes, values, priorities
py -3.11 tools/gen_placement.py                   # regenerate hardware/placement.csv + Altium placement script
py -3.11 tools/check_placement.py "hardware/project/DDR4-UDIMM — 16 GB DDR4.PcbDoc" # every part vs placement_final.csv (--plan: vs JEDEC plan, --export: record)
py -3.11 tools/check_lengths.py "hardware/project/DDR4-UDIMM — 16 GB DDR4.PcbDoc" [nets]  # routed lengths, JEDEC-compensated (outer ÷ 1.1)
```

Needs `py -3.11 -m pip install --user olefile`.

## Changelog

| Date | Change |
|---|---|
| 2026-09-23 | `tools/render_board.py` added: renders the PcbDoc (outline, copper, arcs, vias, pads, silkscreen) to PNG without opening Altium; board and U1 views in [docs/images/](docs/images/) |
| 2026-09-23 | Byte 0 length tuning started: DQ7 tuned to 18.50 mm (inside DQS ± 1.0 mm), serpentine style fixed to Accordion/Rounded, and per-net tuning targets worked out (the gauge measures one net, so the Manual target is 16.66 − finger length) — see [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) |
| 2026-09-23 | Byte 0 fully connected (11/11): the four crossing lines routed by `hardware/scripts/U1_Crossers.pas`; byte target is DQ3 at 17.66 mm and the others need +2.2 to +7.7 mm of tuning (option B: keep the JEDEC bit order, stretch to match) |
| 2026-09-23 | DQS skew fixed by script on DQS1/3/4/5/7 (+0.331 mm each, 45° bumps): six of eight pairs now matched to ~0.001 mm; DQS2 (1.74 mm) and DQS6 (0.33 mm, no room for a bump) still open |
| 2026-09-22 | Router `tools/route_dram_side.py` added; routing U1's four crossing lines the long way gives 12.9–20.5 mm (JEDEC ≈ 11.2–13.2), so a DQ0↔DQ3 / DQ4↔DQ7 nibble bit swap is proposed; half-matching rules ML_BYTEn(_DRAM) found unworkable, to be replaced by total-length checks |
| 2026-09-22 | Byte 0 DRAM side: DQ6 (R7 → U1-E3, 0.30 mm clearance) and DQ2 (R4 → U1-D3) routed on L1 → L3 |
| 2026-09-22 | DQS0_C bump redrawn with 45° chamfers (every corner 135°) by `hardware/scripts/DQS0_C_Bump45.pas`; same +0.331 mm, pair still matched (0.002 mm) |
| 2026-09-22 | DQS0 pair re-routed as a coupled pair on L3 and skew fixed with a 0.331 mm bump on DQS0_C by script `hardware/scripts/DQS0_C_LengthFix.pas`: DRAM-side halves 6.615 / 6.614 mm (limit 0.1 mm) |
| 2026-09-22 | DRAM side started: byte 0 DM0 (L1) and DQ1, DQ2, DQ5, DQS0_T/C (L1 → via → L3 to the fan-out via); full finger-to-ball ≈ 9.1–11.7 mm, to be tuned |
| 2026-09-22 | **Finger side of all 8 byte lanes routed (88/88)** |
| 2026-09-22 | Routing: 47 of 48 back-finger data traces done (5.45–5.81 mm, one via each); all eight DQS pairs matched within 0.042 mm (limit 0.1) |
| 2026-09-22 | Routing: first back-finger data traces (DQ5, DQ1, DQS0_C/T): L8 → via ≈ y 6.3 → L1, straight on a 0.025 mm grid; DQS0 halves equal |
| 2026-09-22 | Routing: all 40 front-finger data traces finger → 15 Ω (5 per byte), L1, 0.10 mm, 2.95–3.20 mm |
| 2026-09-22 | Resistor script run: all 88 data resistors verified at their finger-ordered positions (270°); old DQ0 trace removed; placement_final.csv re-recorded |
| 2026-09-22 | Data resistors re-planned to sit above their own fingers in finger order (front-finger nets low row, back-finger nets high row) so finger-side traces never cross; resistor-only Altium script `DDR4_DataResistors.PrjScr` generated |
| 2026-09-22 | First routed trace DQ0 (3.24 mm, L1, 0.10 mm, inside Annex A TL0 3.2–3.6 mm); `tools/check_lengths.py` added |
| 2026-09-22 | Data resistors flipped 90° → 270° (the plan had the finger-side pad on top); all 88 verified pad-by-pad from the PcbDoc. Fan-out stub widths confirmed: data 0.10, address 0.075, power 0.30 mm |
| 2026-09-22 | First full DRC after fan-out: no shorts, clearance, width or length errors. Vias tented to clear 2809 solder-mask slivers; remaining items are expected while unrouted (un-routed nets, via antennae) or cosmetic silkscreen. L4 pour shelved during routing |
| 2026-09-22 | Routing started: BGA fan-out of all eight DRAMs (408 vias, 51 per chip, identical pattern). Fanout rule re-scoped from IsBGA to HasFootprint('SA_MFG') — the Vault footprint isn't flagged BGA, so the first try used Auto fan-out |
| 2026-09-22 | L4 VDD plane poured (3948.7 mm²); inner copper kept 1 mm off the bevelled finger edge; L2/L7 splits deferred until after routing |
| 2026-09-22 | **Design rules complete** (Blocks 0–8): ML_DQS_PAIRS 0.1 mm added; `check_rules.py` PASS. Next: power/ground pours and routing |
| 2026-09-22 | Block 8: 16 matched-length rules for the byte lanes (ML_BYTE0–7 and ML_BYTE0_DRAM–7_DRAM, 0.5 mm each), checked by `check_rules.py` |
| 2026-09-22 | Block 8: net classes BYTE0_DRAM–BYTE7_DRAM (DRAM side of each byte's 11 × 15 Ω, NetR(12k+2…12k+12)_1) created and checked |
| 2026-09-22 | Block 8: xSignal tools tried for the data lanes (wizard data group, between-components "through 1 series component", pin-pair); none trace through the 15 Ω resistors, test xSignals removed. Plan: split-segment matching (0.5 + 0.5 mm) per byte |
| 2026-09-22 | Block 8 part 1: address/command/clock xSignals J1 → U1…U8 (ADDR_PP1–8, 28 each: A0–A13, A15_CAS, A16_RAS, ACT, BA0/1, BG0/1, CK0_T/C, CKE, CS, ODT, PAR, WE) and their matched-length rules |
| 2026-09-22 | R102 moved beside U1 (ALERT_n pull-up before the first DRAM); power via set to JEDEC's 0.45/0.25 mm large via; final placement re-recorded |
| 2026-09-22 | Correction: ALERT_n pull-up R102 belongs before the first DRAM U1 (Annex A p.12, main spec 6.3.7), not after U8; plan and docs updated. JEDEC length-matching rules (Tables 10–12, §6.4) recorded for Block 8 |
| 2026-09-22 | Placement finalised by hand (caps and terminations nudged ≤ 2 mm, C49 to the other side of U9; DRAMs, SPD and 15 Ω resistors unchanged); recorded as `placement_final.csv` |
| 2026-09-22 | **Placement complete**: placement script run in Altium, all 206 parts verified at their planned positions; rules and stackup still PASS |
| 2026-09-22 | Placement plan from JEDEC numbers: all 206 parts positioned (DRAMs over their byte lanes, rotated 180° so data balls face the fingers; terminations after U8 within TL5), with generator, Altium script and placement checker |
| 2026-09-22 | Design rules Block 7: height ≤ 1.2 mm, top-side-only, finger-zone keep-out room (0–4 mm); rules Blocks 0–7 done, only xSignals/length matching left for after placement |
| 2026-09-22 | Design rules Block 6: polygon connect styles (direct for vias, relief for pads) and 0.2 mm clearance from all objects to pours |
| 2026-09-22 | Design rules Block 5: via styles (signal 0.40/0.20, power 0.50/0.25), BGA fanout, hole size and annular ring; DRAM pad grid measured from the PcbDoc (0.34 mm pads, 0.8 mm pitch) |
| 2026-09-22 | Design rules Block 4: DATA_DRAM net class and five routing-layer rules from the Annex A layer table; Width_DATA covers DATA_DRAM; checker extended (PASS) |
| 2026-09-22 | Design rules Block 3: 18 differential pairs (named and DRAM-side DQS), pair classes and diff-pair routing rules; `check_rules.py` now checks pairs and per-layer widths (PASS) |
| 2026-09-22 | Design rules Blocks 1–2: clearance set finished (track–polygon rule re-created with `InPolygon`) and six width rules from the Annex A table; `tools/check_rules.py` added (PASS) |
| 2026-09-22 | Stackup Block 0: Dk 4.8 → 4.2 so widths match Annex A; SE_55 back on L3/L5/L6 and DIFF_93 on L6 as Annex A specifies. Placement started (8 DRAMs, SPD, 88 series resistors). Net classes (21) and clearance-rule fixes synced |
| 2026-09-21 | Stackup complete and verified (PASS): L6 single-ended references moved from L5 to L4, SE_55/DIFF_93 limited to outer layers; checker now also flags widths under 0.075 mm. PcbDoc synced from the Altium working copy, bringing in 19 net classes and 9 clearance rules |
| 2026-09-21 | Stackup + impedance: 8-layer Annex A stack (1.398 mm) and six impedance profiles set in the PcbDoc; `tools/check_stackup.py` added (L6 reference fix pending); all 206 parts imported to the PCB, placement next |
| 2026-09-20 | First PCB milestone: Altium project sources versioned; MO-309 Board Shape verified at 133.35 × 31.25 mm with center key and four latch notches |
| 2026-09-20 | Final schematic ERC: 0 errors; ALERT_n pins modeled as open-collector, eight off-grid VPP power ports corrected, and 32 external-controller warnings reviewed and documented |
| 2026-09-20 | Connector symbol linked to `DDR4_UDIMM_288_MO309`; all five J1 schematic parts updated and verified against the single physical footprint |
| 2026-09-19 | `DDR4_UDIMM.PcbLib` built in Altium; gold-finger footprint passes all checks |
| 2026-09-19 | Proprietary license added (all rights reserved; use only with written permission) |
| 2026-09-19 | Gold-finger footprint + board outline from MO-309F: generator, Altium build script (288 pads, 40-segment outline, mask windows), PcbLib reader and checker |
| 2026-09-17 | Repository created: locked specification, BOM v1, design notes, source list, PDF render helper |
| 2026-09-17 | Official CAD model sources identified for all parts; vendor library folder created |
| 2026-09-19 | **Schematic complete**: TERM sheet verified; whole-project check passes (11 sheets, 131 nets, 0 dangling, 0 shorts, all 11 BOM lines match) |
| 2026-09-19 | BOM v4: approved alternate for the 4.7 µF bulk cap (TDK C1608X5R1C475K080AC) |
| 2026-09-19 | SPD sheet wired and verified; 34AA04 vendor model committed (official footprint has no center pad, which Microchip marks optional) |
| 2026-09-19 | EDGE sheet wired: 288/288 connector pins correct, 0 warnings; cross-sheet net names consistent |
| 2026-09-19 | Edge-connector symbol built in DDR4_UDIMM.SchLib (5 parts); 288/288 pins verified; SchLib checker added |
| 2026-09-19 | Edge connector: 288-pin table from JEDEC Table 5 (cross-checked vs Micron), 5-part Symbol Wizard files; ALERT_n corrected to a 47 Ω pull-up to VDD (not series) |
| 2026-09-19 | All 8 DRAM sheets (U1–U8) wired and annotated; 636/636 checks pass; net identifier scope set to Global |
| 2026-09-19 | U1 schematic wired; netlist extractor + DRAM rule checker added; U1 passes 83/83 checks |
| 2026-09-18 | DRAM sheet spec (per-chip parts, pin-by-pin wiring, termination, unused pins); BOM v3 with exact quantities (~205 parts) |
| 2026-09-17 | BOM v2: DRAM changed from Alliance AS4C2G8D4A-62BCN (no official CAD model) to Micron MT40A2G8SA-062E:F (Ultra Librarian model, SA package); DRAM ball notes verified |

## License

**All rights reserved. This is not open source.** You may view this repository. Using, copying, modifying, manufacturing or distributing any part of it requires prior written permission from the author. To ask, email rohitnalbuga2@gmail.com. Third-party vendor models and JEDEC-derived data stay under their owners' terms. See [LICENSE](LICENSE).

---
Maintained by **ADuetrohit**
