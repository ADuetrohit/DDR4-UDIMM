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

Full details: [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) · Parts: [bom/BOM_v3.csv](bom/BOM_v3.csv) · DRAM wiring: [docs/SCHEMATIC_DRAM.md](docs/SCHEMATIC_DRAM.md) · CAD sources: [docs/CAD_MODELS.md](docs/CAD_MODELS.md)

## Progress

- [x] Architecture locked (DDR4-3200 UDIMM, 16 GB, Raw Card A3)
- [x] Reference documents collected ([docs/SOURCES.md](docs/SOURCES.md))
- [x] BOM with Digi-Key part numbers (current: v3, exact quantities)
- [ ] Official CAD models collected for every part *(sources identified: [docs/CAD_MODELS.md](docs/CAD_MODELS.md); downloads pending)*
- [ ] Libraries: 288-pin gold-finger footprint, DRAM, SPD, passives
- [ ] Schematic
  - [x] DRAM sheets U1–U8 wired, verified 636/636 by `tools/check_dram.py` ([spec](docs/SCHEMATIC_DRAM.md))
  - [x] 288-pin edge-connector symbol (`hardware/libraries/DDR4_UDIMM.SchLib`, 5 parts) — 288/288 pins verified vs JEDEC Table 5 ([guide](docs/SCHEMATIC_CONNECTOR.md))
  - [x] EDGE sheet: J1A–J1E wired, 288/288 pins verified by `tools/check_connector.py`; net names match all 8 DRAM sheets
  - [ ] Termination sheet ([spec](docs/SCHEMATIC_SUPPORT.md#sheet-termschdoc))
  - [ ] SPD sheet ([spec](docs/SCHEMATIC_SUPPORT.md#sheet-spdschdoc))
- [ ] Stackup and impedance profiles
- [ ] Board outline, key notch, bevel (MO-309)
- [ ] Component placement
- [ ] Design rules (impedance, length matching, clearances)
- [ ] Routing
- [ ] Fabrication and assembly outputs
- [ ] Assembly, SPD programming, bring-up

## Repository layout

```
bom/        Bill of materials (versioned CSV)
docs/       Design notes and reference-source list
hardware/   Altium Designer project and libraries
  libraries/vendor/   Official vendor CAD models, unmodified
tools/      Helper scripts (PDF render, SchDoc netlist extractor, DRAM wiring checker, edge-connector generator)
```

Reference PDFs (JEDEC standards and vendor datasheets) are copyrighted, so they are **not committed**. [docs/SOURCES.md](docs/SOURCES.md) lists each one and where to get it. Place them in `docs/jedec/` and `docs/datasheets/` locally.

## Checking the schematic

```
py -3.11 tools/check_dram.py <sheet>.SchDoc      # every DRAM pin, resistor and capacitor vs the spec
py -3.11 tools/schdoc_nets.py <sheet>.SchDoc     # full netlist straight from the Altium file
py -3.11 tools/check_edge_symbol.py hardware/libraries/DDR4_UDIMM.SchLib   # 288 connector pins vs JEDEC
py -3.11 tools/check_connector.py edge.SchDoc     # every EDGE-sheet pin's net, shorts, default labels, No-ERC
```

Needs `py -3.11 -m pip install --user olefile`.

## Changelog

| Date | Change |
|---|---|
| 2026-09-17 | Repository created: locked specification, BOM v1, design notes, source list, PDF render helper |
| 2026-09-17 | Official CAD model sources identified for all parts; vendor library folder created |
| 2026-09-19 | EDGE sheet wired: 288/288 connector pins correct, 0 warnings; cross-sheet net names consistent |
| 2026-09-19 | Edge-connector symbol built in DDR4_UDIMM.SchLib (5 parts); 288/288 pins verified; SchLib checker added |
| 2026-09-19 | Edge connector: 288-pin table from JEDEC Table 5 (cross-checked vs Micron), 5-part Symbol Wizard files; ALERT_n corrected to a 47 Ω pull-up to VDD (not series) |
| 2026-09-19 | All 8 DRAM sheets (U1–U8) wired and annotated; 636/636 checks pass; net identifier scope set to Global |
| 2026-09-19 | U1 schematic wired; netlist extractor + DRAM rule checker added; U1 passes 83/83 checks |
| 2026-09-18 | DRAM sheet spec (per-chip parts, pin-by-pin wiring, termination, unused pins); BOM v3 with exact quantities (~205 parts) |
| 2026-09-17 | BOM v2: DRAM changed from Alliance AS4C2G8D4A-62BCN (no official CAD model) to Micron MT40A2G8SA-062E:F (Ultra Librarian model, SA package); DRAM ball notes verified |

---
Maintained by **ADuetrohit**
