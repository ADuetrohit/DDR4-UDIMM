"""Per-byte routing and length-tuning worklist, by component designator.

For byte k the eleven series resistors are R(12k+2) .. R(12k+12) and the DRAM is U(k+1). Each data
line runs J1 finger -> Rn pad 2 -> Rn pad 1 -> DRAM ball, so its length is the finger-side net plus
about 1.0 mm through the resistor plus the DRAM-side net NetRn_1. Tracks AND arcs are counted
(rounded serpentines are drawn as arcs, which is easy to miss).

The byte is matched to its longest line (main spec Table 11: DQ/DM within DQS +/- 1.0 mm), so the
"add" column is what each line still needs and "net target" is the number to type into Altium's
length tuning dialog, which measures one net at a time.

Usage:
    py -3.11 tools/byte_status.py <board.PcbDoc> [byte ...]        # default: every byte
"""
import math
import os
import sys

import olefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_lengths as CL                        # noqa: E402
import route_dram_side as R                       # noqa: E402

RESISTOR_MM = 1.0                                 # pad-to-pad through the 15 ohm 0402


def lengths(path):
    ole = olefile.OleFileIO(path)
    names = CL.nets(ole)
    out = {}
    for net, _lay, length, _w in CL.segments(ole, names):
        out[net] = out.get(net, 0.0) + length
    return out


def byte_rows(path, k):
    L = lengths(path)
    _tracks, _vias, pads = R.streams(path)
    dram = f"U{k + 1}"
    rows = []
    for i in range(12 * k + 2, 12 * k + 13):
        des, net = f"R{i}", f"NetR{i}_1"
        fin = [p for p in pads if p[1] == des and p[2] == "2"]
        ball = [p for p in pads if p[0] == net and p[1] == dram]
        if not fin or not ball:
            continue
        signal = fin[0][0]
        lf, ld = L.get(signal, 0.0), L.get(net, 0.0)
        rows.append({"res": des, "signal": signal, "ball": ball[0][2], "finger": lf,
                     "dram": ld, "total": lf + ld + RESISTOR_MM})
    return dram, rows


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    which = [int(a) for a in sys.argv[2:]] or list(range(8))
    for k in which:
        dram, rows = byte_rows(path, k)
        if not rows:
            print(f"\nbyte {k} ({dram}): nothing found")
            continue
        target = max(r["total"] for r in rows)
        print(f"\nbyte {k} ({dram}) - target {target:.2f} mm (longest line), Table 11 window "
              f"{target - 1.0:.2f} to {target + 1.0:.2f}")
        print(f"  {'res':5} {'signal':8} {'ball':5} {'finger':>7} {'DRAM':>8} {'full':>7} "
              f"{'net target':>10} {'add':>7}")
        done = 0
        for r in sorted(rows, key=lambda r: r["total"] - target):
            add = target - r["total"]
            net_target = target - RESISTOR_MM - r["finger"]
            ok = abs(add) <= 1.0
            done += ok
            print(f"  {r['res']:5} {r['signal']:8} {r['ball']:5} {r['finger']:7.2f} {r['dram']:8.3f} "
                  f"{r['total']:7.2f} {net_target:10.2f} {add:+7.2f}{'  OK' if ok else ''}")
        print(f"  {done} of {len(rows)} inside the +/- 1.0 mm window")


if __name__ == "__main__":
    main()
