# DRAM Sheet: one memory chip and everything around it

How **one** Micron MT40A2G8SA-062E:F is wired. All eight chips (U1–U8) are identical except for their data byte.

Sources: Micron Rev H ball map (p23) and ball descriptions (p25–27); JESD21-C 4.20.26 Table 9 (decoupling) and Annex A Raw Card A3 (net structures and resistor values).

## 1. Parts for one chip

| Ref | Part | MPN | Value | Connects |
|---|---|---|---|---|
| U*n* | DRAM | Micron **MT40A2G8SA-062E:F** | 16 Gb x8 | — |
| R_ZQ | Resistor | YAGEO **RC0402FR-07240RL** | 240 Ω 1 % | ZQ (B9) → VSSQ |
| R1–R11 | Resistors | YAGEO **RC0402FR-0715RL** | 15 Ω 5 % | Series in the 8 DQ, 2 DQS and 1 DM lines |
| C1, C2 | Capacitors | Murata **GRM155R71C104KA88D** | 0.1 µF | VDD → VSS |
| C3 | Capacitor | Samsung **CL05A105KP5NNNC** | 1.0 µF | VDD → VSS |
| C4, C5 | Capacitors | Murata **GRM155R71C104KA88D** | 0.1 µF | VPP → VSS (one per VPP ball) |
| C6 | Capacitor | Murata **GRM155R71C104KA88D** | 0.1 µF | VREFCA → **VDD** |

**18 passives per chip → 144 for the eight chips.**

Placement rules: bypass caps sit as close as possible to the DRAM's VDD, VPP and VREFCA balls (spec §5.1, Table 9). The 15 Ω resistors sit near the **card edge**, not near the DRAM (Annex A data net structure), and may double as test points.

## 2. Power and ground

### What the names mean

| Name | It is | Voltage | Balls on this chip |
|---|---|---|---|
| VDD | Main power | +1.2 V | A1, C7, F1, F9, H1, J9, M1, N9 |
| VDDQ | Power for the data pins — **the same 1.2 V net** on a UDIMM | +1.2 V | B2, B8, C1, C9, E2, E8 |
| VSS | Ground | 0 V | A9, C8, E1, E9, G1, H9, K1, K9, N1 |
| VSSQ | Ground for the data pins — **the same ground net** | 0 V | A2, A8, D1, D9 |
| VPP | Wordline supply | +2.5 V | B1, M9 |
| VREFCA | Reference voltage for the address/command pins | VDD/2 ≈ 0.6 V | J1 |

All 14 power balls sit on one 1.2 V net, and all 13 ground balls sit on one 0 V net. Tying pins of the *same* net together is normal, not a short. Two *different* nets (1.2 V, 2.5 V, 0.6 V, 0 V) must never touch through copper.

### The capacitors

A capacitor is not a wire: it blocks DC and only passes fast noise. Each one is a separate part with one leg on the supply and the other on ground.

```
+1.2 V (VDD + VDDQ balls)
   ───────────┬───────────┬───────────┬──────────
              │           │           │
             C1          C2          C3
           0.1 µF      0.1 µF      1.0 µF
              │           │           │
   ───────────┴───────────┴───────────┴──────────
 0 V (VSS + VSSQ balls)


+2.5 V (VPP)
   ──────┬────────────────┬──────
      ball B1          ball M9
         │                │
        C4 0.1 µF        C5 0.1 µF
         │                │
   ──────┴────────────────┴──────
 0 V (VSS)


+1.2 V (VDD)
   ──────────┬──────
             │
            C6 0.1 µF          VREFCA arrives from the card edge;
             │                 the capacitor steadies it against VDD,
   ──────────┴──── ball J1     which is what Table 9 requires.
 VREFCA ≈ 0.6 V
```

## 2b. How this looks on the Altium sheet

Parts to place for one chip: **U1A** (signal part), **U1B** (power part), **C1–C6**, **R_ZQ**, **R1–R11**.

Altium keys: `P` `P` = place part · `P` `W` = wire · `P` `O` = power port · `P` `N` = net label.

Two symbols with the **same power-port name** are the same net, even with no wire drawn between them. That is how VDD, GND, VPP and VREFCA get around the sheet.

### U1B — put a short wire on each pin, then a power port on the wire

```
          U1B  (power part)
          ┌───────────────────────────────┐
  VDD ────┤ A1   VDD            VSS   A9  ├──── GND
  VDD ────┤ C7   VDD            VSS   C8  ├──── GND
  VDD ────┤ F1   VDD            VSS   E1  ├──── GND
  VDD ────┤ F9   VDD            VSS   E9  ├──── GND
  VDD ────┤ H1   VDD            VSS   G1  ├──── GND
  VDD ────┤ J9   VDD            VSS   H9  ├──── GND
  VDD ────┤ M1   VDD            VSS   K1  ├──── GND
  VDD ────┤ N9   VDD            VSS   K9  ├──── GND
          │                     VSS   N1  ├──── GND
  VDD ────┤ B2   VDDQ                     │
  VDD ────┤ B8   VDDQ          VSSQ   A2  ├──── GND
  VDD ────┤ C1   VDDQ          VSSQ   A8  ├──── GND
  VDD ────┤ C9   VDDQ          VSSQ   D1  ├──── GND
  VDD ────┤ E2   VDDQ          VSSQ   D9  ├──── GND
  VDD ────┤ E8   VDDQ                     │
  VPP ────┤ B1   VPP                      │
  VPP ────┤ M9   VPP                      │
VREFCA ───┤ J1   VREFCA                   │
          └───────────────────────────────┘
```

VDDQ pins get a **VDD** port, and VSSQ pins get a **GND** port: they are the same nets.

### The six capacitors, drawn next to U1B

```
   VDD      VDD      VDD        VPP      VPP        VDD
    │        │        │          │        │          │
  ┌─┴─┐    ┌─┴─┐    ┌─┴─┐      ┌─┴─┐    ┌─┴─┐      ┌─┴─┐
  │C1 │    │C2 │    │C3 │      │C4 │    │C5 │      │C6 │
  │.1µ│    │.1µ│    │1µ │      │.1µ│    │.1µ│      │.1µ│
  └─┬─┘    └─┬─┘    └─┬─┘      └─┬─┘    └─┬─┘      └─┬─┘
    │        │        │          │        │          │
   GND      GND      GND        GND      GND      VREFCA
```

Each capacitor is one part with two pins: one leg to the upper port, the other to the lower port. C6's lower leg uses a **VREFCA** port, which is the same net as ball J1.

### U1A — signal pins

```
          U1A  (signal part)
          ┌───────────────────────────────┐
  GND ────┤ G9   TEN/NF                   │      ← must be tied to ground
          │                      ZQ   B9  ├───[ R_ZQ 240Ω ]─── GND
          │                                │
   A0 ────┤ L3   A0             DQ0   C2  ├───[ R1  15Ω ]─── DQ0
   A1 ────┤ L7   A1             DQ1   B7  ├───[ R2  15Ω ]─── DQ1
   A2 ────┤ M3   A2             DQ2   D3  ├───[ R3  15Ω ]─── DQ2
    …     │      …              DQ3   D7  ├───[ R4  15Ω ]─── DQ3
  CK_t────┤ F7   CK t       NF/DQ4   D2  ├───[ R5  15Ω ]─── DQ4
  CK_c────┤ F8   CK c       NF/DQ5   D8  ├───[ R6  15Ω ]─── DQ5
   CS ────┤ G7   CS         NF/DQ6   E3  ├───[ R7  15Ω ]─── DQ6
  CKE ────┤ G3   CKE        NF/DQ7   E7  ├───[ R8  15Ω ]─── DQ7
  ODT ────┤ F3   ODT           DQS t  C3  ├───[ R9  15Ω ]─── DQS0_t
RESET ────┤ L1   RESET         DQS c  B3  ├───[ R10 15Ω ]─── DQS0_c
          │                  DM/DBI   A7  ├───[ R11 15Ω ]─── DM0
          │                  ALERT   L9  ├─── ALERT_n
          │       (leave open: N7, G2, G8, F2, A3 — add a No-ERC mark)
          └───────────────────────────────┘
```

The text at the ends (`A0`, `DQ0`, `ALERT_n`, …) are **net labels**, not wires drawn across the schematic. A net label with the same name on the connector sheet joins the two.

## 3. Data byte (example: U1 = byte 0)

Each line gets its own 15 Ω resistor near the card edge:

```
card edge          15 Ω             DRAM ball
DQ0   ────────────/\/\/─────────────  C2
DQ1   ────────────/\/\/─────────────  B7
DQ2   ────────────/\/\/─────────────  D3
DQ3   ────────────/\/\/─────────────  D7
DQ4   ────────────/\/\/─────────────  D2
DQ5   ────────────/\/\/─────────────  D8   ← pin renamed NF → NF/DQ5
DQ6   ────────────/\/\/─────────────  E3
DQ7   ────────────/\/\/─────────────  E7
DQS0_t────────────/\/\/─────────────  C3
DQS0_c────────────/\/\/─────────────  B3
DM0   ────────────/\/\/─────────────  A7   (DM_n/DBI_n)
```

Chip-to-byte map: U1 → DQ[7:0]/DQS0/DM0, U2 → DQ[15:8]/DQS1/DM1, U3 → DQ[23:16]/DQS2/DM2, U4 → DQ[31:24]/DQS3/DM3, U5 → DQ[39:32]/DQS4/DM4, U6 → DQ[47:40]/DQS5/DM5, U7 → DQ[55:48]/DQS6/DM6, U8 → DQ[63:56]/DQS7/DM7.

## 4. Shared address, command and control

One bus runs past all eight chips (fly-by) and is terminated **once**, after the last chip:

```
card edge ──┬── U1 ──┬── U2 ── … ── U8 ──/\/\/── VTT
            (each DRAM taps the same net)      39 Ω
```

| Signal | DRAM ball | Terminated |
|---|---|---|
| A0–A13 | L3, L7, M3, K7, K3, L8, L2, M8, M2, M7, J3, N2, J7, N8 | 39 Ω each |
| WE_n/A14, CAS_n/A15, RAS_n/A16 | H2, H7, H8 | 39 Ω each |
| ACT_n, PAR | H3, N3 | 39 Ω each |
| BA0, BA1, BG0, BG1 | K2, K8, J2, J8 | 39 Ω each |
| CS_n, CKE, ODT | G7, G3, F3 | 39 Ω each |
| RESET_n | L1 | none (length-controlled only) |

That's **26 × 39 Ω**, with one 0.1 µF capacitor to **VDD** for every two of them (14 in total, including one at the card-edge VTT pin).

## 5. Clock

```
card edge CK0_t ──┬── U1..U8 ──/\/\/──┐
                                39 Ω  ├── C 0.01 µF ── VDD
card edge CK0_c ──┴── U1..U8 ──/\/\/──┘
                                39 Ω
```

The unused second clock is terminated at the card edge only: **CK1_t —75 Ω— CK1_c** (Annex A, unused-clock net structure).

The clock drawing also shows an optional capacitor C1 across CK_t/CK_c near the connector. It is 0 pF (not fitted) for Raw Card A3.

## 6. ALERT_n

All eight ALERT_n pins (ball L9) join **one net that also goes straight to the card-edge ALERT_n pin (208)**. At the far end of the chain, after the last chip, a **47 Ω pull-up goes from ALERT_n to VDD** (Annex A, ALERT_n net structure: connector → TL5 → TL4 → fly-by past all 8 SDRAMs → TL0 → R1 → VDD).

```
card edge 208 ──┬── U1 ──┬── U2 ── … ── U8 ──/\/\/── VDD
                  (each DRAM's L9 taps the net)   47 Ω
```

## 7. Pins that are not connected

| Ball | Name | What to do |
|---|---|---|
| **G9** | TEN/NF | **Tie to VSS** (required: must be low always) |
| N7 | A17/NF/NC | Leave open (x8 uses A[16:0]) |
| G2, G8, F2 | C0/CKE1, C1/CS1_n, C2/ODT1 | Leave open (stack-address inputs, unused on a single die) |
| A3 | NF/TDQS_c | Leave open (TDQS is disabled) |

In Altium, mark each open pin with a **No ERC** directive so the checker stays clean.

## 8. Totals for the whole module

| Part | MPN | Qty |
|---|---|---|
| DRAM | MT40A2G8SA-062E:F | 8 |
| SPD | 34AA04T-I/MUY | 1 |
| 15 Ω | RC0402FR-0715RL | 88 |
| 39 Ω | RC0402FR-0739RL | 28 (26 bus + 2 clock) |
| 240 Ω | RC0402FR-07240RL | 8 |
| 75 Ω | RC0402FR-0775RL | 1 |
| 47 Ω | RC0402FR-0747RL | 1 (ALERT_n pull-up to VDD) |
| 0.1 µF | GRM155R71C104KA88D | 57 |
| 1.0 µF | CL05A105KP5NNNC | 8 |
| 0.01 µF | GRM155R71H103KA88D | 1 |
| 4.7 µF bulk | CL10A475KO8NNNC | 4 |

**≈ 205 parts.**
