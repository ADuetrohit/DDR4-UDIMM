# Reference Sources

These documents are **not stored in the repository**: JEDEC standards and vendor datasheets are copyrighted and licensed to the person who downloads them. Download each one and save it under the local path shown.

## JEDEC standards (`docs/jedec/`)

A free JEDEC account is required.

| Document | Revision | Local file | Used for |
|---|---|---|---|
| JESD21-C 4.20.26 — 288-Pin DDR4 SDRAM Unbuffered DIMM Design Specification | Rev 1.22, Release 29 (Aug 2019) | `4_20_26R29.pdf` | Pinout, power, decoupling rules (Table 9), reference stackups (§6.8), keepouts |
| JESD21-C 4.20.26 Annex A — Raw Card A | Rev 3.01, Release 30A | `4_20_26_AnnexAR30A.pdf` | Raw Card A3 net structures, trace lengths, resistor values, PCB fabrication table |
| MO-309 — 288 Pin DDR4 DIMM, 0.85 mm Pitch | Issue F (Mar 2015) | `MO-309F.pdf` | Board outline, key notch, finger geometry, thickness, bevel |
| JESD21-C 4.1.2 Annex L — SPD for DDR4 SDRAM Modules | Release 4 (JESD21-C R27A) | `4_01_02_AnnexL-4R27A.pdf` | SPD EEPROM contents |

Search jedec.org for `MODULE4.20.26`, `MODULE4.20.26.A`, `MO-309` and `Annex L`.

### Not used

| Item | Why |
|---|---|
| JEDEC design file "PC4-3200 Unbuffered DIMM", Raw Card A3 (`PC4_UDIMM_RC_A_V300_20180528`) | Costs $2,000 for non-members. Every value needed is already in Annex A and the main specification. |
| Annex B (Raw Card B) and Annex C (Raw Card C) | Other module configurations. Raw Card C is 8 GB maximum. |

## Vendor datasheets (`docs/datasheets/`)

| Document | Local file | Source |
|---|---|---|
| **Micron 16Gb DDR4 SDRAM (MT40A4G4 / MT40A2G8 / MT40A1G16), Rev H, Aug 2021** (DRAM in use) | `Micron-MT40A4G4-MT40A2G8-MT40A1G16-16Gb-DDR4-RevH.pdf` | [media.digikey.com](https://media.digikey.com/pdf/Data%20Sheets/Micron%20Technology%20Inc%20PDFs/MT40A4G4_2G8_1G16_RevH_Aug2021.pdf) |
| Alliance Memory 16Gb DDR4 (AS4C1G16D4A / AS4C2G8D4A), Rev 1.1, Jul 2025 (superseded: Alliance part dropped) | `Alliance-AS4C1G16D4A-AS4C2G8D4A-16Gb-DDR4-Rev1.1.pdf` | [alliancememory.com](https://www.alliancememory.com/wp-content/uploads/AllianceMemory_AS4C1G16D4A_AS4C2G8D4A_16Gb_DDR4_Datasheet_Rev1.1_July-2025.pdf) |
| Microchip 34AA04 4K SPD EEPROM (DS20005271B) | `Microchip-34AA04-SPD-EEPROM.pdf` | [microchip.com](https://ww1.microchip.com/downloads/en/DeviceDoc/20005271B.pdf) |
| Micron/Crucial 8GB SR x8 288-pin DDR4 UDIMM (CT8G4DFS8) | `Micron-Crucial-CT8G4DFS8-DDR4-UDIMM-8GB-SRx8.pdf` | [rs-online.com](https://docs.rs-online.com/6ecf/0900766b81641250.pdf) |

## Micron 16Gb DDR4 datasheet (Rev H): pages used

PDF page numbers match the printed page numbers.

| Design step | Pages | Content |
|---|---|---|
| Part selection | 1–2 | Features, options, part-number decode (MT40A2G8SA-062E:F), Table 1 key timing, Table 2 addressing |
| Symbol and schematic | 21 | Figure 3: 2 Gig x 8 functional block diagram |
| Symbol and schematic | **23** | **Figure 5: 78-ball x4/x8 ball assignments** (used to verify the symbol) |
| Symbol and schematic | 25–27 | Table 3: ball descriptions (ZQ, TEN, VREFCA, ALERT_n, PAR, NF handling) |
| Footprint | **30** | **Figure 9: 78-ball FBGA, SA package** (used to verify the footprint) |
| Power and decoupling | 37 | Table 5: supply power-up slew rate |
| Power and decoupling | 253–255 | Tables 77–81: absolute maximum ratings, temperature, supply operating conditions (VDD/VDDQ/VPP), VDD slew rate, VREFCA leakage |
| Power and decoupling | 324–325 | Table 150: IDD/IPP current limits, **die rev F** (VDD/VPP current budget) |
| Signal integrity and length matching | 298–301 | Tables 133 and 135: package electrical specs (x8) and pad capacitance |
| Signal integrity and length matching | 292 | Table 127: ALERT_n driver |
| SPD programming | 341 | Table 158: DDR4-3200 speed bins (CL22) |
| SPD programming | 343 | Table 159: refresh parameters |
| SPD programming | 357–369 | Table 161: AC timing parameters, DDR4-2666 to 3200 |

## Reading image-only drawings

MO-309 has no text layer. Render its pages to PNG with:

```
py -3.11 tools/render_pdf.py docs/jedec/MO-309F.pdf <output_dir> 130
```
