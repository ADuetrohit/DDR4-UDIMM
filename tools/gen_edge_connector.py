"""Generate the 288-pin DDR4 UDIMM edge-connector pin data.

Source: JESD21-C 4.20.26 Rev 1.22, Table 5 "DDR4 288 Pin UDIMM Pin Wiring
Assignments" (UDIMM functions only; the light-coloured functions that the
note marks as not applicable to UDIMMs are dropped).

Writes, into hardware/libraries/edge_connector/:
  DDR4_UDIMM_288_pinout.csv   pin, side, JEDEC name, net, how it connects, symbol part
  symbol_wizard_part_<X>.tsv  paste-ready rows for Altium's Symbol Wizard
                              (Group, Display Name, Designator, Electrical Type, Description, Side)

Usage:
    py -3.11 tools/gen_edge_connector.py [--check-micron <micron_udimm.txt>]
"""
import csv
import os
import re
import sys
from collections import Counter

# ---- JEDEC Table 5, UDIMM wiring --------------------------------------------------------
FRONT = {  # pins 1-144 (key between 77 and 78)
    1: "NC", 2: "VSS", 3: "DQ4", 4: "VSS", 5: "DQ0", 6: "VSS", 7: "DM0_n/DBI0_n", 8: "NC",
    9: "VSS", 10: "DQ6", 11: "VSS", 12: "DQ2", 13: "VSS", 14: "DQ12", 15: "VSS", 16: "DQ8",
    17: "VSS", 18: "DM1_n/DBI1_n", 19: "NC", 20: "VSS", 21: "DQ14", 22: "VSS", 23: "DQ10",
    24: "VSS", 25: "DQ20", 26: "VSS", 27: "DQ16", 28: "VSS", 29: "DM2_n/DBI2_n", 30: "NC",
    31: "VSS", 32: "DQ22", 33: "VSS", 34: "DQ18", 35: "VSS", 36: "DQ28", 37: "VSS", 38: "DQ24",
    39: "VSS", 40: "DM3_n/DBI3_n", 41: "NC", 42: "VSS", 43: "DQ30", 44: "VSS", 45: "DQ26",
    46: "VSS", 47: "CB4/NC", 48: "VSS", 49: "CB0/NC", 50: "VSS", 51: "DM8_n/DBI8_n/NC", 52: "NC",
    53: "VSS", 54: "CB6/NC", 55: "VSS", 56: "CB2/NC", 57: "VSS", 58: "RESET_n", 59: "VDD",
    60: "CKE0", 61: "VDD", 62: "ACT_n", 63: "BG0", 64: "VDD", 65: "A12/BC_n", 66: "A9",
    67: "VDD", 68: "A8", 69: "A6", 70: "VDD", 71: "A3", 72: "A1", 73: "VDD", 74: "CK0_t",
    75: "CK0_c", 76: "VDD", 77: "VTT",
    78: "EVENT_n", 79: "A0", 80: "VDD", 81: "BA0", 82: "RAS_n/A16", 83: "VDD", 84: "CS0_n",
    85: "VDD", 86: "CAS_n/A15", 87: "ODT0", 88: "VDD", 89: "CS1_n", 90: "VDD", 91: "ODT1",
    92: "VDD", 93: "NC", 94: "VSS", 95: "DQ36", 96: "VSS", 97: "DQ32", 98: "VSS",
    99: "DM4_n/DBI4_n", 100: "NC", 101: "VSS", 102: "DQ38", 103: "VSS", 104: "DQ34", 105: "VSS",
    106: "DQ44", 107: "VSS", 108: "DQ40", 109: "VSS", 110: "DM5_n/DBI5_n", 111: "NC",
    112: "VSS", 113: "DQ46", 114: "VSS", 115: "DQ42", 116: "VSS", 117: "DQ52", 118: "VSS",
    119: "DQ48", 120: "VSS", 121: "DM6_n/DBI6_n", 122: "NC", 123: "VSS", 124: "DQ54",
    125: "VSS", 126: "DQ50", 127: "VSS", 128: "DQ60", 129: "VSS", 130: "DQ56", 131: "VSS",
    132: "DM7_n/DBI7_n", 133: "NC", 134: "VSS", 135: "DQ62", 136: "VSS", 137: "DQ58",
    138: "VSS", 139: "SA0", 140: "SA1", 141: "SCL", 142: "VPP", 143: "VPP", 144: "RFU",
}
BACK = {  # pins 145-288 (key between 221 and 222)
    145: "NC", 146: "VREFCA", 147: "VSS", 148: "DQ5", 149: "VSS", 150: "DQ1", 151: "VSS",
    152: "DQS0_c", 153: "DQS0_t", 154: "VSS", 155: "DQ7", 156: "VSS", 157: "DQ3", 158: "VSS",
    159: "DQ13", 160: "VSS", 161: "DQ9", 162: "VSS", 163: "DQS1_c", 164: "DQS1_t", 165: "VSS",
    166: "DQ15", 167: "VSS", 168: "DQ11", 169: "VSS", 170: "DQ21", 171: "VSS", 172: "DQ17",
    173: "VSS", 174: "DQS2_c", 175: "DQS2_t", 176: "VSS", 177: "DQ23", 178: "VSS", 179: "DQ19",
    180: "VSS", 181: "DQ29", 182: "VSS", 183: "DQ25", 184: "VSS", 185: "DQS3_c", 186: "DQS3_t",
    187: "VSS", 188: "DQ31", 189: "VSS", 190: "DQ27", 191: "VSS", 192: "CB5/NC", 193: "VSS",
    194: "CB1/NC", 195: "VSS", 196: "DQS8_c", 197: "DQS8_t", 198: "VSS", 199: "CB7/NC",
    200: "VSS", 201: "CB3/NC", 202: "VSS", 203: "CKE1", 204: "VDD", 205: "RFU", 206: "VDD",
    207: "BG1", 208: "ALERT_n", 209: "VDD", 210: "A11", 211: "A7", 212: "VDD", 213: "A5",
    214: "A4", 215: "VDD", 216: "A2", 217: "VDD", 218: "CK1_t", 219: "CK1_c", 220: "VDD",
    221: "VTT",
    222: "PARITY", 223: "VDD", 224: "BA1", 225: "A10/AP", 226: "VDD", 227: "RFU",
    228: "WE_n/A14", 229: "VDD", 230: "NC", 231: "VDD", 232: "A13", 233: "VDD", 234: "NC",
    235: "NC", 236: "VDD", 237: "NC", 238: "SA2", 239: "VSS", 240: "DQ37", 241: "VSS",
    242: "DQ33", 243: "VSS", 244: "DQS4_c", 245: "DQS4_t", 246: "VSS", 247: "DQ39", 248: "VSS",
    249: "DQ35", 250: "VSS", 251: "DQ45", 252: "VSS", 253: "DQ41", 254: "VSS", 255: "DQS5_c",
    256: "DQS5_t", 257: "VSS", 258: "DQ47", 259: "VSS", 260: "DQ43", 261: "VSS", 262: "DQ53",
    263: "VSS", 264: "DQ49", 265: "VSS", 266: "DQS6_c", 267: "DQS6_t", 268: "VSS", 269: "DQ55",
    270: "VSS", 271: "DQ51", 272: "VSS", 273: "DQ61", 274: "VSS", 275: "DQ57", 276: "VSS",
    277: "DQS7_c", 278: "DQS7_t", 279: "VSS", 280: "DQ63", 281: "VSS", 282: "DQ59", 283: "VSS",
    284: "VDDSPD", 285: "SDA", 286: "VPP", 287: "VPP", 288: "VPP",
}
PINS = {**FRONT, **BACK}

# ---- JEDEC name -> net used on this design's schematic ----------------------------------
POWER_NETS = {"VSS": "GND", "VDD": "VDD", "VPP": "VPP", "VTT": "VTT", "VREFCA": "VREFCA",
              "VDDSPD": "VDDSPD"}
RENAME = {"A10/AP": "A10_AP", "A12/BC_n": "A12_BC", "RAS_n/A16": "A16_RAS",
          "CAS_n/A15": "A15_CAS", "WE_n/A14": "WE", "ACT_n": "ACT", "PARITY": "PAR",
          "CS0_n": "CS", "CKE0": "CKE", "ODT0": "ODT", "RESET_n": "RESET_N",
          "CK0_t": "CK0_T", "CK0_c": "CK0_C", "CK1_t": "CK1_T", "CK1_c": "CK1_C",
          "ALERT_n": "ALERT_n"}
# single rank, non-ECC, no thermal sensor: these connector pins are not wired on the module
UNUSED = {"NC", "RFU", "CS1_n", "CKE1", "ODT1", "EVENT_n", "DQS8_t", "DQS8_c",
          "DM8_n/DBI8_n/NC"} | {f"CB{i}/NC" for i in range(8)}


def net_of(name):
    """Return (net, kind) where kind is 'power', 'label' or 'nc'."""
    if name in UNUSED:
        return "", "nc"
    if name in POWER_NETS:
        return POWER_NETS[name], "power"
    if name in RENAME:
        return RENAME[name], "label"
    m = re.fullmatch(r"DM(\d)_n/DBI\d_n", name)
    if m:
        return f"DM{m.group(1)}", "label"
    m = re.fullmatch(r"DQS(\d)_([tc])", name)
    if m:
        return f"DQS{m.group(1)}_{m.group(2).upper()}", "label"
    if re.fullmatch(r"(DQ\d+|A\d+|BA\d|BG\d|SA\d|SCL|SDA)", name):
        return name, "label"
    raise ValueError(f"no mapping for {name}")


# ---- symbol parts ------------------------------------------------------------------------
def dq_byte(net):
    m = re.fullmatch(r"(?:DQ(\d+)|DQS(\d)_[TC]|DM(\d))", net)
    if not m:
        return None
    return int(m.group(1)) // 8 if m.group(1) else int(m.group(2) or m.group(3))


def byte_order(net):
    if net.startswith("DQS"):
        return 8 + (net.endswith("_C"))
    if net.startswith("DM"):
        return 10
    return int(net[2:]) % 8


ADDR_ORDER = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10_AP", "A11",
              "A12_BC", "A13", "WE", "A15_CAS", "A16_RAS", "BA0", "BA1", "BG0", "BG1", "ACT", "PAR"]
CTRL_ORDER = ["CK0_T", "CK0_C", "CK1_T", "CK1_C", "CKE", "CS", "ODT", "RESET_N", "ALERT_n",
              "SA0", "SA1", "SA2", "SCL", "SDA", "CKE1", "CS1_n", "ODT1", "EVENT_n"]


def build_rows():
    rows = []
    for pin in range(1, 289):
        name = PINS[pin]
        net, kind = net_of(name)
        side = "front" if pin <= 144 else "back"
        rows.append({"pin": pin, "board_side": side, "jedec_name": name, "net": net, "connect": kind})

    parts = {"A": [], "B": [], "C": [], "D": [], "E": []}
    for r in rows:
        b = dq_byte(r["net"]) if r["connect"] == "label" else None
        if b is not None:
            part = "A" if b < 4 else "B"
            r["part"], r["sym_side"] = part, "Left" if b % 4 < 2 else "Right"
            r["sort"] = (b, byte_order(r["net"]))
        elif r["net"] in ADDR_ORDER:
            r["part"], r["sym_side"], r["sort"] = "C", "Left", (ADDR_ORDER.index(r["net"]),)
        elif r["net"] in CTRL_ORDER or r["jedec_name"] in CTRL_ORDER:
            key = r["net"] or r["jedec_name"]
            r["part"], r["sym_side"], r["sort"] = "C", "Right", (CTRL_ORDER.index(key),)
        elif r["net"] == "GND":
            r["part"], r["sort"] = "D", (r["pin"],)
        elif r["connect"] == "power":
            order = ["VDD", "VPP", "VTT", "VREFCA", "VDDSPD"].index(r["net"])
            r["part"], r["sym_side"], r["sort"] = "E", "Left", (order, r["pin"])
        else:
            r["part"], r["sym_side"], r["sort"] = "E", "Right", (r["pin"],)
        parts[r["part"]].append(r)

    gnd = sorted(parts["D"], key=lambda r: r["sort"])
    for i, r in enumerate(gnd):
        r["sym_side"] = "Left" if i < (len(gnd) + 1) // 2 else "Right"
    for p in parts:
        parts[p].sort(key=lambda r: (r["sym_side"] != "Left", r["sort"]))
    return rows, parts


PART_TITLES = {"A": "DATA bytes 0-3", "B": "DATA bytes 4-7", "C": "ADDRESS / COMMAND / CLOCK / SPD",
               "D": "GROUND (VSS)", "E": "POWER + unused pins"}


def check_against_micron(path):
    """Compare with the Micron CT8G4DFS8 288-pin table (independent source)."""
    text = open(path, encoding="utf-8", errors="replace").read()
    start = text.find("Table 4: Pin Assignments")
    end = text.find("Pin Descriptions", start)
    chunk = text[start:end]
    found = {}
    for m in re.finditer(r"(?<![\w/])(\d{1,3})\s+([A-Z][A-Za-z0-9_/]*)", chunk):
        n, sym = int(m.group(1)), m.group(2)
        if 1 <= n <= 288 and n not in found:
            found[n] = sym
    mismatches = []
    for n, sym in sorted(found.items()):
        ours = PINS[n]
        a = re.split(r"[/,]", ours)[0].upper()
        b = re.split(r"[/,]", sym)[0].upper()
        if a != b and not (a in ("NC", "RFU") and b in ("NC", "RFU", "NF")) and not (a == "DM0_N" and b.startswith("DM")):
            if not (ours.startswith("DM") and sym.startswith("DM")):
                mismatches.append((n, ours, sym))
    return len(found), mismatches


def main():
    rows, parts = build_rows()

    # structural self-checks
    counts = Counter(r["jedec_name"] for r in rows)
    nets = Counter(r["net"] for r in rows if r["connect"] == "label")
    assert len(rows) == 288
    assert all(nets[f"DQ{i}"] == 1 for i in range(64)), "every DQ exactly once"
    assert all(nets[f"DQS{i}_{s}"] == 1 for i in range(8) for s in "TC"), "every DQS exactly once"
    assert all(nets[f"DM{i}"] == 1 for i in range(8)), "every DM exactly once"
    assert all(nets[n] == 1 for n in ADDR_ORDER + CTRL_ORDER[:14]), "every CA/CTRL/SPD net once"
    assert sum(len(v) for v in parts.values()) == 288

    if "--check-micron" in sys.argv:
        n_found, mism = check_against_micron(sys.argv[sys.argv.index("--check-micron") + 1])
        print(f"Micron cross-check: {n_found} pins parsed, {len(mism)} mismatches")
        for m in mism:
            print("   ", m)

    out = os.path.join(os.path.dirname(__file__), "..", "hardware", "libraries", "edge_connector")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "DDR4_UDIMM_288_pinout.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Pin", "Board side", "JEDEC name", "Net on this design", "Connect with", "Symbol part"])
        for r in rows:
            how = {"power": "power port", "label": "net label", "nc": "No-ERC (not connected)"}[r["connect"]]
            w.writerow([r["pin"], r["board_side"], r["jedec_name"], r["net"], how, r["part"]])
    for p, prow in parts.items():
        # CRLF line ends: Altium's Smart Paste splits rows on Windows line breaks
        with open(os.path.join(out, f"symbol_wizard_part_{p}.tsv"), "w", newline="\r\n", encoding="utf-8") as f:
            for r in prow:
                desc = f"net {r['net']}" if r["net"] else "not connected"
                f.write("\t".join([PART_TITLES[p], r["jedec_name"], str(r["pin"]), "Passive", desc,
                                   r["sym_side"]]) + "\n")

    print("JEDEC names:", ", ".join(f"{k} x{v}" for k, v in counts.most_common(6)))
    for p, prow in parts.items():
        left = sum(r["sym_side"] == "Left" for r in prow)
        print(f"Part {p} ({PART_TITLES[p]}): {len(prow)} pins  (left {left}, right {len(prow) - left})")
    kinds = Counter(r["connect"] for r in rows)
    print("Connect with:", dict(kinds))
    print("Written to", os.path.abspath(out))


if __name__ == "__main__":
    main()
