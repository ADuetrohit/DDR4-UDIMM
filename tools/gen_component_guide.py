"""Build docs/COMPONENT_GUIDE.pdf: every component on the board, one row per pin.

Companion to ROUTING_GUIDE.pdf, which is organised by layer. This one is organised by component:
for each designator it lists the pins, the net on each pin, what the net connects to, the layers the
net may use and how much copper it already has. Everything is read from the saved PcbDoc.

Usage:
    py -3.11 tools/gen_component_guide.py <board.PcbDoc> [out.pdf]
"""
import collections
import html
import os
import re
import sys

import olefile
import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_routing_guide as G                     # noqa: E402

POWER = {"GND", "VDD", "VSS", "VSSQ", "VDDQ", "VTT", "VPP", "VREFCA", "VDDSPD", "NC"}
LAYERS = {"Data": "L1, L3, L8", "Clock": "L1, L6, L8", "Address": "L1, L3, L5, L6, L8",
          "Control": "L1, L3, L5, L6, L8", "ALERT": "L1, L3, L5, L6, L8", "SPD": "any signal layer",
          "Power": "plane / L1-L8"}


def descriptions(path):
    ole = olefile.OleFileIO(path)
    out = {}
    for r in G.records(ole, "Components6/Data"):
        d = r.get("SOURCEDESIGNATOR")
        if d:
            out[d] = r.get("SOURCEDESCRIPTION") or ""
    return out


def classify(f):
    """net -> group name, using the net classes on the board."""
    order = [("Data", ("DATA", "DATA_DRAM")), ("Clock", ("CK", "CK_UNUSED")), ("Address", ("ADDR",)),
             ("Control", ("CTRL", "RESET")), ("ALERT", ("ALERT",)), ("SPD", ("SPD",)),
             ("Power", ("POWER",))]
    out = {}
    for label, cnames in order:
        for cname in cnames:
            for n in f["classes"].get(cname, []):
                out.setdefault(n, label)
    return out


def partners(f, net, self_des):
    return ", ".join("%s-%s" % (d, p) for d, p in f["net_pins"].get(net, []) if d != self_des) or "-"


def group_of(net, cls):
    if net in POWER:
        return "Power"
    if net and net.startswith("NetR"):
        return "Data" if cls.get(net) in (None, "Data") else cls[net]
    return cls.get(net, "-")


def pin_rows(f, cls, des, skip_power=True):
    rows = []
    for pin, net in sorted(f["pins"][des].items(), key=lambda kv: G.natural(kv[0])):
        if not net or (skip_power and net in POWER):
            continue                              # unconnected pins and plane pins are not routed here
        g = group_of(net, cls)
        rows.append([pin, net or "-", g, partners(f, net, des), LAYERS.get(g, "-"),
                     "%.2f" % f["len"].get(net, 0.0)])
    return rows


def build_html(f, desc, board_name):
    cls = classify(f)
    H = ["<h1>DDR4-UDIMM component guide</h1>",
         '<p class="sub">Every component by designator, with the net on each pin, what that net connects '
         'to, and the layers it may use. Companion to ROUTING_GUIDE.pdf, which is organised by layer. '
         'Read from %s.</p>' % html.escape(board_name)]

    counts = collections.Counter(d[0] for d in f["pins"])
    H.append("<h2>1. What is on the board</h2>")
    H.append(G.table(["Prefix", "What", "Count"], [
        ["J1", "288-pin DDR4 UDIMM edge connector (5 schematic parts, one footprint)", counts.get("J", 0)],
        ["U1-U8", "Micron MT40A2G8SA-062E:F DRAM, 78-ball FBGA", 8],
        ["U9", "Microchip 34AA04 SPD EEPROM", 1],
        ["R1-R126", "series, termination and pull-up resistors", counts.get("R", 0)],
        ["C1-C70", "decoupling and bulk capacitors", counts.get("C", 0)],
    ]))
    H.append('<p class="sub">Power and ground pins are left out of the per-pin tables below - they are '
             'connected to the planes with their own vias, not routed as signals.</p>')

    H.append("<h2>2. J1 - edge connector</h2>")
    H.append("<p>Signal pins only. Every one of these runs to a resistor first, never straight to a DRAM.</p>")
    rows = pin_rows(f, cls, "J1")
    H.append(G.table(["J1 pin", "Net", "Class", "Goes to", "Layers", "copper mm"], rows))

    for i in range(1, 9):
        des = "U%d" % i
        if des not in f["pins"]:
            continue
        H.append("<h2>3.%d %s - DRAM</h2>" % (i, des))
        H.append('<p class="sub">%s. Data balls take their own 15 ohm resistor; address, command and '
                 'clock balls are shared with the other seven DRAMs on the fly-by.</p>'
                 % html.escape(desc.get(des, "")))
        H.append(G.table(["Ball", "Net", "Class", "Goes to", "Layers", "copper mm"],
                         pin_rows(f, cls, des)))

    if "U9" in f["pins"]:
        H.append("<h2>4. U9 - SPD EEPROM</h2>")
        H.append('<p class="sub">%s</p>' % html.escape(desc.get("U9", "")))
        H.append(G.table(["Pin", "Net", "Class", "Goes to", "Layers", "copper mm"], pin_rows(f, cls, "U9")))

    H.append("<h2>5. Resistors</h2>")
    H.append("<p>Pad 1 and pad 2 of every resistor, with the net on each. The function column says what "
             "the part is there for; the layers column applies to the signal side.</p>")
    rows = []
    for des in sorted((d for d in f["pins"] if d.startswith("R")), key=G.natural):
        pins = f["pins"][des]
        p1, p2 = pins.get("1", "-"), pins.get("2", "-")
        nets = set(pins.values())
        if any(n and n.startswith("NetR") for n in nets) and "GND" in nets:
            fn, lay = "240 ohm ZQ to GND", "L1"
        elif any(n and n.startswith("NetR") for n in nets):
            fn, lay = "15 ohm series, data", "L1, L3, L8"
        elif "VTT" in nets:
            fn, lay = "39 ohm termination to VTT", "L1, L3, L5, L6, L8"
        elif "VDD" in nets:
            fn, lay = "47 ohm ALERT_n pull-up to VDD", "L1, L3, L5, L6, L8"
        elif "NetC56_1" in nets:
            fn, lay = "39 ohm clock termination", "L1, L6, L8"
        else:
            fn, lay = "75 ohm across the unused clock pair", "L1, L6, L8"
        sig = [n for n in (p1, p2) if n not in POWER]
        rows.append([des, desc.get(des, "") or "-", p1, p2, fn, lay,
                     "%.2f" % sum(f["len"].get(n, 0.0) for n in sig)])
    H.append(G.table(["Resistor", "Part", "Pad 1 net", "Pad 2 net", "Function", "Layers", "copper mm"], rows))

    H.append("<h2>6. Capacitors</h2>")
    H.append("<p>None of these is a routed signal: give each pad its own via straight into the plane it "
             "belongs to, as short as you can make it.</p>")
    rows = []
    for des in sorted((d for d in f["pins"] if d.startswith("C")), key=G.natural):
        pins = f["pins"][des]
        p1, p2 = pins.get("1", "-"), pins.get("2", "-")
        fn = "clock termination node to VDD" if "NetC56_1" in (p1, p2) else "decoupling"
        rows.append([des, desc.get(des, "") or "-", p1, p2, fn])
    H.append(G.table(["Capacitor", "Part", "Pad 1 net", "Pad 2 net", "Function"], rows))
    return "".join(H)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "docs", "COMPONENT_GUIDE.pdf")
    f = G.facts(path)
    story = pymupdf.Story(html=build_html(f, descriptions(path), os.path.basename(path)), user_css=G.CSS)
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
