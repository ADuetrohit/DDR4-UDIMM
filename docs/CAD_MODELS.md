# Official CAD Models

Where each BOM part's official symbol, footprint and 3D model comes from. Checked 17 Sep 2026. Several providers require a free login, so every download is done manually in a browser.

Save each download, unzipped, to `hardware/libraries/vendor/<MPN>/`.

## Status

| # | MPN | Official model | Where | Format | Login |
|---|---|---|---|---|---|
| 1 | AS4C2G8D4A-62BCN (DRAM) | **None exists** | Alliance publishes only the datasheet, reliability data, MDS and IBIS. Digi-Key and SnapMagic have no model. | — | — |
| 1a | MT40A2G8SA-062E IT:F (Micron, same 78-ball 7.5×11 package), reference only | Yes (Ultra Librarian built & verified) | [Ultra Librarian](https://app.ultralibrarian.com/details/59d8b735-a85f-11ed-b159-0a34d6323d74/Micron/MT40A2G8SA-062E-IT-F) | Altium | Free UL account |
| 2 | 34AA04T-I/MUY (SPD) | Likely (Microchip uses Ultra Librarian) | [Digi-Key page → EDA/CAD Models](https://www.digikey.com/en/products/detail/microchip-technology/34AA04T-I-MUY/4860085) | To confirm | To confirm |
| 3 | RC0402FR-07240RL | Likely; 3D model confirmed | [YAGEO spec sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-07240RL) (3D link); Digi-Key → EDA/CAD Models | STEP; symbol/footprint to confirm | No (STEP) |
| 4 | RC0402FR-0715RL | Likely; 3D model confirmed | [YAGEO spec sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-0715RL); Digi-Key → EDA/CAD Models | Same | No (STEP) |
| 5 | RC0402FR-0739RL | Likely; 3D model confirmed | [YAGEO spec sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-0739RL); Digi-Key → EDA/CAD Models | Same | No (STEP) |
| 6 | RC0402FR-0747RL | Likely; 3D model confirmed | [YAGEO spec sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-0747RL); Digi-Key → EDA/CAD Models | Same | No (STEP) |
| 7 | RC0402FR-0775RL | Likely; 3D model confirmed | [YAGEO spec sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-0775RL); Digi-Key → EDA/CAD Models | Same | No (STEP) |
| 8 | GRM155R71H103KA88D | Unclear | [Murata CAD data](https://www.murata.com/en-us/tool/data/caddata) (download button on the product page); Digi-Key → EDA/CAD Models | To confirm | To confirm |
| 9 | GRM155R71C104KA88D | **Yes** (Ultra Librarian built & verified) | [Ultra Librarian](https://app.ultralibrarian.com/details/e6bd3c4a-1072-11e9-ab3a-0a3560a4cccc/Murata/GRM155R71C104KA88D) | Altium | Free UL account |
| 10 | CL05A105KP5NNNC | **Yes** (linked from Samsung) | [Samsung page](https://product.samsungsem.com/mlcc/CL05A105KP5NNN.do) → [SnapMagic](https://www.snapeda.com/parts/CL05A105KP5NNN/Samsung/view-part/?ref=samsung) | Altium | Free SnapMagic account |
| 11 | CL10A475KO8NNNC | **Yes** (linked from Samsung) | [Samsung page](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do) → [SnapMagic](https://www.snapeda.com/parts/CL10A475KO8NNN/Samsung/view-part/?ref=samsung) | Altium | Free SnapMagic account |

"Likely" means a Digi-Key "EDA/CAD Models" link exists but its contents couldn't be checked without a login. Update the row once the file has been downloaded.

## DRAM footprint plan

There is no official model for the AS4C2G8D4A-62BCN. The footprint will be built with Altium's **IPC Compliant Footprint Wizard (BGA)**, using the official package drawing in the Alliance datasheet (Figure 6, 78-ball FBGA x8):

| Parameter | Value |
|---|---|
| Body | 7.5 ± 0.1 × 11.0 ± 0.1 mm |
| Ball pitch | 0.8 mm × 0.8 mm |
| Matrix | 9 columns (columns 4–6 empty) × 13 rows (A–N), 78 balls |
| Ball diameter | 0.525 ± 0.05 mm (post-reflow) |
| Datasheet pad | Ø 0.47 mm, solder-mask defined |
| Height | 1.1 ± 0.1 mm |

The Ultra Librarian Micron MT40A2G8SA-062E IT:F model (same JEDEC 78-ball package) is used only as a cross-check.

## Custom footprint (no vendor model possible)

| Footprint | Source |
|---|---|
| 288-pin DDR4 DIMM gold-finger edge connector, board outline, key notch | JEDEC MO-309 Issue F |
