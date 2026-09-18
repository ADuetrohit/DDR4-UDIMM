# Vendor CAD models

Official symbols, footprints and 3D models, downloaded as-is from the sources in [docs/CAD_MODELS.md](../../../docs/CAD_MODELS.md).

Put each download (unzipped) in a folder named after the exact MPN. Replace `/` in an MPN with `-`:

```
vendor/
  MT40A2G8SA-062E-IT-F/     (DRAM model; same SA package as the MT40A2G8SA-062E:F used on the board)
  34AA04T-I-MUY/
  RC0402FR-07240RL/
  RC0402FR-0715RL/
  RC0402FR-0739RL/
  RC0402FR-0747RL/
  RC0402FR-0775RL/
  GRM155R71H103KA88D/
  GRM155R71C104KA88D/
  CL05A105KP5NNNC/
  CL10A475KO8NNNC/
```

These files are not edited. The project library (`hardware/libraries/DDR4_UDIMM.SchLib` / `.PcbLib`) is built from them.

## Already in use

| MPN | Location | Notes |
|---|---|---|
| 34AA04T-I/MUY | `hardware/libraries/Altium/34AA04T-IMUY.*` (SchLib, PcbLib, LibPkg, STEP) | Ultra Librarian export, linked from the project by path. Footprint `UDFN8_2x3MC_MCH` has 8 pads and no center pad; Microchip's land pattern (C04-2136A) marks the center pad "Optional" and the datasheet allows it floating. |
| MT40A2G8SA-062E:F | Altium Content Vault (Manufacturer Part Search), footprint `SA_MFG` | Placed from the vault; pin D8 name "NF" to be corrected in the project library. |
