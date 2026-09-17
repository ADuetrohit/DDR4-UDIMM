# DDR4-UDIMM — 16 GB DDR4-3200 Desktop Memory Module

A custom 288-pin DDR4 unbuffered DIMM with hard-gold edge fingers, designed in Altium Designer. It follows the JEDEC reference design **Raw Card A3**.

## Specification

| Item | Value |
|---|---|
| Form factor | 288-pin UDIMM, 0.85 mm finger pitch (JEDEC MO-309) |
| Standard | JESD21-C 4.20.26 (Rev 1.22) + Annex A, Raw Card **A3** (Rev 3.01) |
| Capacity / organization | 16 GB, 1 rank, x8, non-ECC |
| Speed | DDR4-3200 (PC4-3200) |
| Memory ICs | 8 × Alliance Memory **AS4C2G8D4A-62BCN** (16 Gb, 78-ball FBGA 7.5 × 11 mm) |
| SPD | Microchip **34AA04T-I/MUY** (EE1004, no thermal sensor) |
| PCB | 8 layers, **1.40 ± 0.10 mm** across the fingers, hard-gold contacts |
| Supplies (from motherboard) | VDD 1.2 V · VPP 2.5 V · VTT 0.6 V · VREFCA · VDDSPD 2.2–3.6 V |
| Component height limit | ≤ 1.2 mm (single-sided module) |

Full details: [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) · Parts: [bom/BOM_v1.csv](bom/BOM_v1.csv) · CAD sources: [docs/CAD_MODELS.md](docs/CAD_MODELS.md)

## Progress

- [x] Architecture locked (DDR4-3200 UDIMM, 16 GB, Raw Card A3)
- [x] Reference documents collected ([docs/SOURCES.md](docs/SOURCES.md))
- [x] BOM v1 with Digi-Key part numbers
- [ ] Official CAD models collected for every part *(sources identified: [docs/CAD_MODELS.md](docs/CAD_MODELS.md); downloads pending)*
- [ ] Libraries: 288-pin gold-finger footprint, DRAM, SPD, passives
- [ ] Schematic
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
tools/      Helper scripts
```

Reference PDFs (JEDEC standards and vendor datasheets) are copyrighted, so they are **not committed**. [docs/SOURCES.md](docs/SOURCES.md) lists each one and where to get it. Place them in `docs/jedec/` and `docs/datasheets/` locally.

## Changelog

| Date | Change |
|---|---|
| 2026-09-17 | Repository created: locked specification, BOM v1, design notes, source list, PDF render helper |
| 2026-09-17 | Official CAD model sources identified for all parts; DRAM has no vendor model (IPC footprint plan added); vendor library folder created |

---
Maintained by **ADuetrohit**
