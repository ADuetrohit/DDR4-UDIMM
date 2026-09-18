# SPD and Termination Sheets

These two small sheets finish the schematic. They use the nets the EDGE sheet brings in but the DRAM sheets don't: `SA0–SA2, SCL, SDA, VDDSPD` (SPD) and `VTT, CK1_T, CK1_C` (termination). They also carry the shared end-of-bus resistors and the module-level capacitors.

Sources: Microchip 34AA04 datasheet (DS20005271B) pin table; JESD21-C 4.20.26 Annex A (Raw Card A3 net structures) and main spec Table 9 (decoupling).

## Sheet `SPD.SchDoc`

| Ref | Part | MPN | Value |
|---|---|---|---|
| U9 | SPD EEPROM (EE1004) | Microchip **34AA04T-I/MUY** | 4 Kbit, UDFN-8 2×3 |
| C49 | Capacitor | Murata **GRM155R71C104KA88D** | 0.1 µF, VDDSPD → GND |

```
                 U9  34AA04T-I/MUY
               ┌──────────────────┐
  SA0 ─────────┤1  A0        VCC 8├───────┬──── VDDSPD (power port)
  SA1 ─────────┤2  A1         NC 7├── ✕   │
  SA2 ─────────┤3  A2        SCL 6├───────┼──── SCL
  GND ▽────────┤4  VSS       SDA 5├───────┼──── SDA
               │     EP (pad)     ├── GND ▽
               └──────────────────┘       │
                                        C49 0.1 µF
                                          │
                                         GND ▽
```

- The SCL/SDA pull-up resistors are on the **motherboard**, not the module.
- SA0–SA2 are set by each motherboard slot, so several sticks get different I²C addresses.
- The exposed pad may go to VSS or be left floating (datasheet); tie it to GND.
- A0 also accepts a high voltage for setting write protection, which matters later when programming the SPD.

## Sheet `TERM.SchDoc`

All values from Annex A, Raw Card A3.

| What | Parts | MPN | Qty |
|---|---|---|---|
| Address/command/control termination to **VTT** | 39 Ω | YAGEO **RC0402FR-0739RL** | 26 |
| VTT decoupling, to **VDD** (1 per 2 resistors + 1 at the VTT finger) | 0.1 µF | Murata **GRM155R71C104KA88D** | 14 |
| CK0 termination | 39 Ω ×2 + 0.01 µF to VDD | RC0402FR-0739RL, Murata **GRM155R71H103KA88D** | 2 + 1 |
| Unused CK1 pair | 75 Ω across the pair | YAGEO **RC0402FR-0775RL** | 1 |
| ALERT_n pull-up | 47 Ω to **VDD** | YAGEO **RC0402FR-0747RL** | 1 |
| VPP cap at the card edge | 0.1 µF to GND | GRM155R71C104KA88D | 1 |
| VREFCA cap at the card edge | 0.1 µF to **VDD** | GRM155R71C104KA88D | 1 |
| VDD bulk | 4.7 µF to GND | Samsung **CL10A475KO8NNNC** | 4 |

### Address, command and control termination (26 × 39 Ω)

Each resistor goes between one net label and a **VTT** power port:

```
 A0      ──/\/\/── VTT        A10_AP  ──/\/\/── VTT        WE      ──/\/\/── VTT
 A1      ──/\/\/── VTT        A11     ──/\/\/── VTT        A15_CAS ──/\/\/── VTT
 A2      ──/\/\/── VTT        A12_BC  ──/\/\/── VTT        A16_RAS ──/\/\/── VTT
 A3      ──/\/\/── VTT        A13     ──/\/\/── VTT        BA0     ──/\/\/── VTT
 A4      ──/\/\/── VTT                                     BA1     ──/\/\/── VTT
 A5      ──/\/\/── VTT        ACT     ──/\/\/── VTT        BG0     ──/\/\/── VTT
 A6      ──/\/\/── VTT        PAR     ──/\/\/── VTT        BG1     ──/\/\/── VTT
 A7      ──/\/\/── VTT        CS      ──/\/\/── VTT
 A8      ──/\/\/── VTT        CKE     ──/\/\/── VTT
 A9      ──/\/\/── VTT        ODT     ──/\/\/── VTT
                  39 Ω each (26)
```

### VTT decoupling (14 × 0.1 µF, to VDD, not GND)

```
 VTT ──┬──────┬──────┬── … ──┬──────┐
      C      C      C       C      C        14 caps
      │      │      │       │      │
 VDD ──┴──────┴──────┴── … ──┴──────┘
```

On the PCB, one sits beside every pair of termination resistors and one at the card-edge VTT pins (77, 221).

### Clocks, ALERT_n, and card-edge caps

```
 CK0_T ──/\/\/──┐
        39 Ω    ├──┤├── VDD        (0.01 µF, GRM155R71H103KA88D)
 CK0_C ──/\/\/──┘
        39 Ω

 CK1_T ──/\/\/── CK1_C             (75 Ω across the unused clock pair)

 ALERT_n ──/\/\/── VDD             (47 Ω pull-up, at the far end of the chain)

 VPP    ──┤├── GND                 (0.1 µF, near the VPP fingers)
 VREFCA ──┤├── VDD                 (0.1 µF, near finger 146; returns to VDD)
 VDD    ──┤├── GND  ×4             (4.7 µF bulk)
```

The node joining the two CK0 resistors and the capacitor can be a plain wire; it needs no net label.

## Check against the BOM

| Part | TERM + SPD | DRAM sheets | Total | BOM v3 |
|---|---|---|---|---|
| 39 Ω | 28 | 0 | 28 | 28 ✓ |
| 75 Ω | 1 | 0 | 1 | 1 ✓ |
| 47 Ω | 1 | 0 | 1 | 1 ✓ |
| 0.1 µF | 14 + 1 + 1 + 1 (SPD) = 17 | 40 | 57 | 57 ✓ |
| 0.01 µF | 1 | 0 | 1 | 1 ✓ |
| 4.7 µF | 4 | 0 | 4 | 4 ✓ |
