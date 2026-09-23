"""Build docs/ROUTING_GUIDE.pdf: which signal goes on which layer, by component designator.

Everything in the tables is read from the saved PcbDoc (components, pads, nets, classes,
differential pairs, routing-layer rules and how much copper each net already has), so the guide
cannot drift from the board. The fixed engineering text comes from JESD21-C 4.20.26 (main spec
Tables 10-14 and Annex A, Raw Card A3) and is cited section by section.

Usage:
    py -3.11 tools/gen_routing_guide.py <board.PcbDoc> [out.pdf]
"""
import collections
import html
import os
import re
import sys

import olefile
import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import byte_status as BS                          # noqa: E402
import check_lengths as CL                        # noqa: E402
import route_dram_side as R                       # noqa: E402

ROUTED = 1.0                  # mm of copper before a net counts as started


# ----------------------------------------------------------------- board facts

def records(ole, stream):
    data, out, pos = ole.openstream(stream).read(), [], 0
    while pos + 4 <= len(data):
        n = int.from_bytes(data[pos:pos + 4], "little")
        body = data[pos + 4:pos + 4 + n].decode("latin-1")
        pos += 4 + n
        out.append(dict(p.split("=", 1) for p in body.strip("\x00").split("|") if "=" in p))
    return out


def facts(path):
    ole = olefile.OleFileIO(path)
    _tracks, _vias, pads = R.streams(path)
    f = {"pads": pads}
    f["pins"] = collections.defaultdict(dict)
    f["pos"] = {}
    for net, des, pin, _lay, xy, _w, _h in pads:
        if des:
            f["pins"][des][pin] = net
            f["pos"].setdefault(des, xy)
    f["len"] = collections.Counter()
    names = CL.nets(ole)
    for net, _lay, ln, _w in CL.segments(ole, names):
        f["len"][net] += ln
    f["classes"] = {r.get("NAME"): [v for k, v in r.items() if re.fullmatch(r"M\d+", k)]
                    for r in records(ole, "Classes6/Data") if r.get("KIND") == "0"}
    f["pairs"] = {r.get("NAME"): (r.get("POSITIVENETNAME"), r.get("NEGATIVENETNAME"))
                  for r in records(ole, "DifferentialPairs6/Data") if r.get("NAME")}
    f["rules"] = {r.get("NAME"): r for r in records(ole, "Rules6/Data") if r.get("NAME")}
    f["bytes"] = {k: BS.byte_rows(path, k) for k in range(8)}
    f["net_pins"] = collections.defaultdict(list)
    for net, des, pin, _lay, _xy, _w, _h in pads:
        if net and des:
            f["net_pins"][net].append((des, pin))
    for net in f["net_pins"]:
        f["net_pins"][net].sort()
    return f


def role_groups(f):
    """Resistors grouped by what they do, from the nets on their pads."""
    g = collections.defaultdict(list)
    for des, pins in f["pins"].items():
        if not des.startswith("R"):
            continue
        nets = set(pins.values())
        if any(n and n.startswith("NetR") for n in nets) and "GND" in nets:
            g["ZQ"].append(des)
        elif any(n and n.startswith("NetR") for n in nets):
            g["DATA"].append(des)
        elif "VTT" in nets:
            g["TERM"].append(des)
        elif "VDD" in nets:
            g["ALERT"].append(des)
        else:
            g["CK"].append(des)
    return {k: sorted(v, key=lambda d: int(d[1:])) for k, v in g.items()}


def span(desigs):
    """Compact designator list: R97-R126 style where they run on."""
    nums = sorted(int(d[1:]) for d in desigs)
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append("R%d" % nums[i] if i == j else "R%d-R%d" % (nums[i], nums[j]))
        i = j + 1
    return ", ".join(out)


# ----------------------------------------------------------------- html pieces

def table(headers, rows, cls=""):
    h = "".join("<th>%s</th>" % html.escape(str(x)) for x in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(c)) for c in r) for r in rows)
    return '<table class="%s"><tr>%s</tr>%s</table>' % (cls, h, body)


STACK = [
    ("L1", "Top Layer 1", "signal, microstrip", "L2 (plane, 70 um)",
     "DQ / DQS / DM escapes, finger stubs, short address hops"),
    ("L2", "L2_PWR_GND", "plane", "-", "reference for L1 and L3; GND under the data groups"),
    ("L3", "L3_DQ_ADDR", "signal, stripline", "L2 (plane, 80 um)",
     "DQ / DQS / DM DRAM side; address permitted"),
    ("L4", "L4_VDD", "plane", "-", "reference for L5; VDD"),
    ("L5", "L5_ADDR", "signal, stripline", "L4 (VDD, 80 um)", "address and command only"),
    ("L6", "L6_ADDR_CK", "signal, stripline", "L7 (plane, 80 um)", "address, command and the clock pairs"),
    ("L7", "L7_PWR_GND", "plane", "-", "reference for L6 and L8"),
    ("L8", "Bottom Layer 1", "signal, microstrip", "L7 (plane, 70 um)",
     "DQ / DQS / DM DRAM side, clocks"),
]

LAYER_SECTIONS = [
    ("L1 - Top Layer 1", "signal (microstrip, references L2)", [
        ("Data, all 8 bytes", "R2-R12, R14-R24, ... R86-R96 (88 resistors)",
         "J1 finger to resistor pad 2, and resistor pad 1 to the DRAM fan-out via", "0.10 mm, 50 ohm"),
        ("Address and command", "R97-R126 to J1 and the DRAMs", "finger stubs and short hops", "0.075 mm, 55 ohm"),
        ("ZQ", "R1, R13, R25, R37, R49, R61, R73, R85", "DRAM ZQ ball to 240 ohm to GND", "0.10 mm"),
        ("ALERT_n", "R102", "47 ohm pull-up to VDD, before the first DRAM (U1)", "0.075 mm"),
    ]),
    ("L3 - L3_DQ_ADDR", "signal (stripline, references L2 = GND)", [
        ("Data, DRAM side", "NetR2_1 ... NetR96_1", "resistor pad 1 to the DRAM ball, via L1", "0.10 mm, 50 ohm"),
        ("Address and command", "any of A0-A16, BA, BG, ACT, CKE, CS, ODT, PAR, WE",
         "permitted but keep it clear of the byte lanes", "0.075 mm, 55 ohm"),
    ]),
    ("L5 - L5_ADDR", "signal (stripline, references L4 = VDD)", [
        ("Address", "A0-A13, A10_AP, A12_BC, A15_CAS, A16_RAS", "J1 to U1 -> U2 -> ... -> U8 fly-by",
         "0.075 mm, 55 ohm"),
        ("Bank / command", "BA0, BA1, BG0, BG1, ACT, WE, PAR", "same fly-by", "0.075 mm, 55 ohm"),
        ("Control", "CKE, CS, ODT, RESET_n", "same fly-by", "0.075 mm, 55 ohm"),
    ]),
    ("L6 - L6_ADDR_CK", "signal (stripline, references L7)", [
        ("Clock pair", "CK0_T / CK0_C", "J1 to every DRAM, fly-by, terminated at R115 / R117 and C56",
         "0.075 / 0.10 mm gap, 93 ohm differential"),
        ("Address and command overflow", "whatever does not fit on L5", "same fly-by", "0.075 mm, 55 ohm"),
    ]),
    ("L8 - Bottom Layer 1", "signal (microstrip, references L7)", [
        ("Data, DRAM side", "NetR2_1 ... NetR96_1", "second choice when L3 is congested", "0.10 mm, 50 ohm"),
        ("Clocks", "CK0_T / CK0_C", "permitted", "93 ohm differential"),
    ]),
]

FORBIDDEN = [
    ("DQ / DQS / DM", "L1, L3, L8 only", "RoutingLayers_DATA",
     "L5 and L6 reference VDD; data return current needs GND (Table 12)"),
    ("CK0_T / CK0_C", "L1, L6, L8 only", "RoutingLayers_CK", "clock references VDD or a plane, per Table 12"),
    ("Address, control, RESET_n, ALERT_n", "L1, L3, L5, L6, L8", "RoutingLayers_ADDR", "address references VDD"),
    ("Everything else", "L1, L3, L5, L6, L8", "RoutingLayers", "L2, L4 and L7 are planes - never route on them"),
]

SPECIAL = [
    ("Differential pairs", "18 pairs: CK0, CK1 and DQS0-DQS7 on the connector side, plus DQS0_DRAM-DQS7_DRAM "
     "between the 15 ohm resistors and the DRAMs. Route with Route > Interactive Differential Pair Routing "
     "(U, P) so both wires are drawn together and stay phase matched. Gap 0.10 mm, halves matched within "
     "0.1 mm (main spec Table 11, rule MatchedLengths_DDR_CLOCKS_STROBES)."),
    ("Byte-lane length matching", "Each DQ and DM must sit within DQS +/- 1.0 mm over the whole finger-to-ball "
     "path, and the byte total must be 12.0-32.0 mm compensated (Table 11). The longest line in the byte is the "
     "reference: adding length to it lengthens every other line in that byte, so never tune the longest one."),
    ("xSignals", "Once a byte is routed, Design > xSignals > Create xSignals with source J1 and destination Un "
     "traces the finger -> 15 ohm -> ball path as one object (4 nodes). Put the 11 into an xSignal class "
     "BYTEn_FULL and point a Matched Lengths rule at it with tolerance 1 mm. It fails on unrouted nets, so "
     "route first, then create."),
    ("Address fly-by", "J1 -> U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8, then the 39 ohm termination to VTT. "
     "Address and control within 1.0 mm of each other and within CK +/- 0.5 mm; CK first-to-last DRAM at most "
     "153 mm; the stub from the fly-by to each DRAM ball (TL2) at most 3.0 mm (Annex A)."),
    ("Velocity compensation", "All length rules are on stripline-equivalent lengths: divide any microstrip "
     "(L1 or L8) length by 1.1 before comparing (main spec 6.3.4). tools/check_lengths.py reports both."),
    ("Plane referencing", "Table 12: DQ, DQS and DM reference GND; address, command, clock and VREFCA "
     "reference VDD. No signal may cross a plane split - check L2, L4 and L7 under every route."),
    ("Vias and fan-out", "All vias are through-hole, 0.40 mm pad / 0.20 mm drill (0.45 / 0.25 for power). "
     "Routing space per Table 14: via-to-track 0.20 mm, large via 0.25 mm, track-to-pad 0.125 mm, "
     "track-to-shape 0.20 mm. All vias are tented (rule SolderMask_TentedVias)."),
    ("Serpentine style", "Accordion, Rounded, amplitude up to 1.0 mm in the corridor down the middle of a DRAM "
     "and 0.4 mm near the balls, spacing 0.3 mm = 3 x track width. Meander space: the corridor between ball "
     "columns 3 and 7 of each DRAM (about 3.2 x 9.6 mm) and the band just above the resistor rows."),
]

CSS = """
body { font-family: sans-serif; font-size: 9pt; color: #111; }
h1 { font-size: 20pt; margin-bottom: 2pt; }
h2 { font-size: 13pt; margin-top: 14pt; margin-bottom: 3pt; color: #14406b; }
h3 { font-size: 10.5pt; margin-top: 10pt; margin-bottom: 2pt; color: #14406b; }
p  { margin-top: 2pt; margin-bottom: 4pt; }
.sub { color: #555; font-size: 8.5pt; }
table { width: 100%; font-size: 8pt; margin-top: 3pt; margin-bottom: 6pt; }
th { background: #14406b; color: #fff; text-align: left; padding: 2pt; }
td { padding: 2pt; border-bottom: 1px solid #ccc; vertical-align: top; }
"""


def build_html(f, board_name):
    g = role_groups(f)
    H = ["<h1>DDR4-UDIMM routing guide</h1>",
         '<p class="sub">16 GB DDR4-3200 UDIMM, Raw Card A3. Which signal is routed on which layer, '
         'by component designator. Tables generated from %s; rules from JESD21-C 4.20.26 '
         '(main spec Tables 10-14 and Annex A).</p>' % html.escape(board_name)]

    H.append("<h2>1. Layer stack</h2>")
    H.append(table(["Layer", "Name", "Type", "References", "What is routed here"], STACK))
    H.append("<p><b>Never route on L2, L4 or L7.</b> They are solid planes and they are the return path "
             "for everything else; a track on a plane cuts that return path.</p>")

    H.append("<h2>2. Layer assignment rules (enforced by DRC)</h2>")
    H.append(table(["Signal group", "Allowed layers", "Altium rule", "Why"], FORBIDDEN))

    H.append("<h2>3. Layer by layer</h2>")
    for title, sub, rows in LAYER_SECTIONS:
        H.append("<h3>%s</h3>" % html.escape(title))
        H.append('<p class="sub">%s</p>' % html.escape(sub))
        H.append(table(["Signal group", "Components", "From - to", "Width / impedance"], rows))

    H.append("<h2>4. Data byte lanes, by designator</h2>")
    H.append("<p>Every data line is J1 finger -> Rn pad 2 -> Rn pad 1 (15 ohm) -> DRAM ball. "
             "Route pad 1 to the ball on L1 + L3 (or L1 + L8). "
             "The target is the byte's longest line; each line must land within 1.0 mm of it. "
             "<b>Route the whole byte before tuning any of it:</b> the target below is only the longest "
             "line routed <i>so far</i>, so in a byte that is still mostly unrouted it will rise. A DRAM-side "
             "length of about 0.57 mm means nothing is routed yet - that is just the ball-to-via stub.</p>")
    for k in range(8):
        dram, rows = f["bytes"][k]
        if not rows:
            continue
        target = max(r["total"] for r in rows)
        H.append("<h3>Byte %d - %s (target %.2f mm, window %.2f to %.2f)</h3>" %
                 (k, dram, target, target - 1.0, target + 1.0))
        body = []
        for r in sorted(rows, key=lambda r: r["res"] and int(r["res"][1:])):
            add = target - r["total"]
            state = "in window" if abs(add) <= 1.0 else ("route it" if r["dram"] < ROUTED else "+%.2f mm" % add)
            jpin = ", ".join(p for d, p in f["net_pins"].get(r["signal"], []) if d == "J1")
            body.append([r["res"], r["signal"], jpin or "-", "NetR%s_1" % r["res"][1:],
                         "%s-%s" % (dram, r["ball"]), "L1 + L3 or L1 + L8",
                         "%.2f" % r["finger"], "%.2f" % r["dram"], "%.2f" % r["total"], state])
        H.append(table(["Resistor", "Finger net", "J1 pin", "DRAM-side net", "DRAM ball", "Layers",
                        "finger mm", "DRAM mm", "full mm", "to do"], body))

    H.append("<h2>5. Address, command and control</h2>")
    H.append("<p>Fly-by from J1 through U1 to U8 and then into the 39 ohm termination to VTT. "
             "Route on <b>L5</b> and <b>L6</b>, which are empty and reference VDD as Table 12 requires. "
             "Width 0.075 mm (55 ohm). Within 1.0 mm of each other and within CK +/- 0.5 mm.</p>")
    term = g.get("TERM", [])
    rows = []
    for des in term:
        pins = f["pins"][des]
        sig = [n for n in pins.values() if n != "VTT"]
        rows.append([des, sig[0] if sig else "?", "39 ohm to VTT", "L5 / L6",
                     "done" if f["len"].get(sig[0] if sig else "", 0) > ROUTED else "to route"])
    H.append(table(["Resistor", "Signal", "Function", "Layers", "Status"], rows))

    H.append("<h2>6. Clocks, ZQ, ALERT_n and SPD</h2>")
    rows = [["R115", "CK0_T / NetC56_1", "39 ohm, clock termination after the last DRAM", "L1, L6, L8",
             "pairs with R117 and C56"],
            ["R117", "CK0_C / NetC56_1", "39 ohm, clock termination", "L1, L6, L8", "pairs with R115"],
            ["C56", "NetC56_1 / VDD", "0.01 uF from the termination node to VDD", "-",
             "main spec Table 9 note 2"],
            ["R106", "CK1_T / CK1_C", "75 ohm across the unused clock pair", "L1, L6, L8",
             "terminate at the connector end, Annex A"],
            ["R102", "ALERT_n / VDD", "47 ohm pull-up", "L1, L3, L5, L6, L8",
             "must sit BEFORE the first DRAM (Annex A 6.3.7)"]]
    for des in g.get("ZQ", []):
        pins = f["pins"][des]
        net = [n for n in pins.values() if n != "GND"]
        dram = [d for d, _p in f["net_pins"].get(net[0] if net else "", []) if d.startswith("U")]
        ball = [p for d, p in f["net_pins"].get(net[0] if net else "", []) if d.startswith("U")]
        rows.append([des, "%s / GND" % (net[0] if net else "?"), "240 ohm 1%% ZQ for %s" %
                     (dram[0] if dram else "?"), "L1",
                     "straight to ball %s, keep it short" % (ball[0] if ball else "?")])
    spd = sorted(n for n in f["classes"].get("SPD", []))
    rows.append(["U9", ", ".join(spd), "SPD EEPROM 34AA04", "any signal layer",
                 "low speed, no length rules"])
    H.append(table(["Component", "Nets", "Function", "Layers", "Notes"], rows))

    H.append("<h2>7. Differential pairs</h2>")
    rows = []
    for name in sorted(f["pairs"], key=lambda s: (s.startswith("DQS"), s)):
        p, n = f["pairs"][name]
        side = "DRAM side" if (p or "").startswith("NetR") else "connector side"
        lay = "L1, L6, L8" if name.startswith("CK") else "L1, L3, L8"
        rows.append([name, p, n, side, lay])
    H.append(table(["Pair", "Positive", "Negative", "Where", "Layers"], rows))
    H.append("<p>Use <b>Route &gt; Interactive Differential Pair Routing</b> (U, P) for these, never two "
             "single tracks. Halves matched within 0.1 mm; the pair as a whole is matched to its byte.</p>")

    H.append("<h2>8. Special cases and things that catch people out</h2>")
    for title, text in SPECIAL:
        H.append("<h3>%s</h3><p>%s</p>" % (html.escape(title), html.escape(text)))

    H.append("<h2>9. What is left to route</h2>")
    todo = []
    for k in range(8):
        dram, rows = f["bytes"][k]
        left = [r["res"] for r in rows if r["dram"] < ROUTED]
        tune = [r["res"] for r in rows
                if r["dram"] >= ROUTED and abs(max(x["total"] for x in rows) - r["total"]) > 1.0]
        todo.append(["Byte %d (%s)" % (k, dram), span(left) if left else "-",
                     span(tune) if tune else "-"])
    H.append(table(["Byte", "DRAM side still to route", "Routed but needs length tuning"], todo))
    addr = [n for n in f["classes"].get("ADDR", []) + f["classes"].get("CTRL", [])
            if f["len"].get(n, 0) < 4.6]
    H.append("<p>Address and command: the fly-by from the first DRAM onwards is not routed yet - "
             "only the connector stubs exist. Plan it on L5 and L6. Clocks CK1_T / CK1_C are unrouted "
             "(terminate at the connector). SPD nets are unrouted.</p>")

    H.append("<h2>10. Decoupling and bulk capacitors</h2>")
    H.append("<p>Every capacitor sits between a supply and its return, so none of them is routed as a "
             "signal: connect each pad to the nearest plane with its own via, as short as possible.</p>")
    caps = collections.defaultdict(list)
    for des, pins in f["pins"].items():
        if des.startswith("C"):
            caps["/".join(sorted(set(n for n in pins.values() if n)))].append(des)
    H.append(table(["Nets", "Capacitors", "Count"],
                   [[k, span_any(v), len(v)] for k, v in sorted(caps.items(), key=lambda x: -len(x[1]))]))

    H.append("<h2>11. Full signal cross-reference</h2>")
    H.append("<p>Every signal net on the board: where it starts at the connector, which resistor is in "
             "series or terminates it, which DRAM pins it lands on, and the layers it may use.</p>")
    # group a net by the class that decides its routing layers, most specific first
    GROUPS = [("Data", ("DATA", "DATA_DRAM"), "L1, L3, L8"),
              ("Clock", ("CK", "CK_UNUSED"), "L1, L6, L8"),
              ("Address", ("ADDR",), "L1, L3, L5, L6, L8"),
              ("Control", ("CTRL", "RESET"), "L1, L3, L5, L6, L8"),
              ("ALERT", ("ALERT",), "L1, L3, L5, L6, L8"),
              ("SPD", ("SPD",), "any signal layer"),
              ("Power", ("POWER",), "L1-L8")]
    of_class, allowed = {}, {}
    for label, cnames, lay in GROUPS:
        for cname in cnames:
            for n in f["classes"].get(cname, []):
                of_class.setdefault(n, label)
                allowed.setdefault(n, lay)
    rows = []
    for net in sorted(f["net_pins"], key=natural):
        if net in ("GND", "VDD", "VTT", "VPP", "VSS", "VREFCA", "VDDSPD"):
            continue
        pins = f["net_pins"][net]
        j = ", ".join(p for d, p in pins if d == "J1")
        res = ", ".join("%s.%s" % (d, p) for d, p in pins if d.startswith("R"))
        us = ", ".join("%s-%s" % (d, p) for d, p in pins if d.startswith("U"))
        cs = ", ".join(d for d, _p in pins if d.startswith("C"))
        cls = of_class.get(net, "Data" if net.startswith("NetR") else "-")
        rows.append([net, j or "-", res or "-", us or "-", cs or "-", cls,
                     allowed.get(net, "L1, L3, L8" if cls == "Data" else "L1, L3, L5, L6, L8"),
                     "%.2f" % f["len"].get(net, 0.0)])
    H.append(table(["Net", "J1 pin", "Resistor", "DRAM / SPD pin", "Cap", "Class", "Layers", "copper mm"],
                   rows))
    return "".join(H)


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def span_any(desigs):
    """Compact designator list for any prefix, e.g. C1-C9, C11."""
    pre = desigs[0][0]
    nums = sorted(int(d[1:]) for d in desigs)
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append("%s%d" % (pre, nums[i]) if i == j else "%s%d-%s%d" % (pre, nums[i], pre, nums[j]))
        i = j + 1
    return ", ".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "docs", "ROUTING_GUIDE.pdf")
    f = facts(path)
    story = pymupdf.Story(html=build_html(f, os.path.basename(path)), user_css=CSS)
    writer = pymupdf.DocumentWriter(out)
    media = pymupdf.paper_rect("a4")
    where = media + (42, 42, -42, -48)
    more, page = 1, 0
    while more:
        dev = writer.begin_page(media)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        page += 1
    writer.close()
    print("wrote %s (%d pages)" % (out, page))


if __name__ == "__main__":
    main()
