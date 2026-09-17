# Official CAD Models

Where each BOM part's official symbol, footprint and 3D model comes from. Checked 17 Sep 2026. Several providers require a free login, so every download is done manually in a browser.

Save each download, unzipped, to `hardware/libraries/vendor/<MPN>/`.

## Status

| # | MPN | Official model | Where | Format | Login |
|---|---|---|---|---|---|
| 1 | **MT40A2G8SA-062E:F** (Micron DRAM) | **Yes**, via the model for **MT40A2G8SA-062E IT:F** (Ultra Librarian built & verified; package `FBGA78_SA_MRN`) | [Ultra Librarian](https://app.ultralibrarian.com/details/59d8b735-a85f-11ed-b159-0a34d6323d74/Micron/MT40A2G8SA-062E-IT-F) | Altium, STEP | Free UL account |
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

## DRAM model

The DRAM was changed from the Alliance AS4C2G8D4A-62BCN to the **Micron MT40A2G8SA-062E:F**, because no official CAD model exists for the Alliance part.

- The Ultra Librarian model is published for **MT40A2G8SA-062E IT:F**. That part is identical except for its industrial temperature rating, and its Digi-Key listing is obsolete.
- The commercial **:F** is Active on Digi-Key. Both use Micron package code **SA**, so the symbol and footprint are the same.

Check the model against Micron datasheet Rev H, **Figure 9: 78-Ball FBGA – x4, x8 (SA)**:

| Parameter | Value |
|---|---|
| Body | 7.5 ± 0.1 × 11 ± 0.1 mm |
| Ball pitch | 0.8 mm × 0.8 mm (6.4 × 9.6 mm ball-centre span) |
| Matrix | Columns 1–3 and 7–9 × rows A–N = 78 balls |
| Ball diameter | Ø 0.47 ± 0.05 mm post-reflow |
| Datasheet pad | **Ø 0.42 mm, solder-mask defined** |
| Height | 1.1 ± 0.1 mm (ball height 0.34 ± 0.05) |

## Custom footprint (no vendor model possible)

| Footprint | Source |
|---|---|
| 288-pin DDR4 DIMM gold-finger edge connector, board outline, key notch | JEDEC MO-309 Issue F |
