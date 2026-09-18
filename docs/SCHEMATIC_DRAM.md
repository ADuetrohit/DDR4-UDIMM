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

The unused second clock is terminated at the card edge only: **CK1_t —75 Ω— CK1_c**.

## 6. ALERT_n

All eight ALERT_n pins (ball L9) are open-drain and join one net → **47 Ω** → card-edge ALERT_n pin.

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
| 47 Ω | RC0402FR-0747RL | 1 |
| 0.1 µF | GRM155R71C104KA88D | 57 |
| 1.0 µF | CL05A105KP5NNNC | 8 |
| 0.01 µF | GRM155R71H103KA88D | 1 |
| 4.7 µF bulk | CL10A475KO8NNNC | 4 |

**≈ 205 parts.**
