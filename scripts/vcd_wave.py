#!/usr/bin/env python3
"""Minimal VCD -> SVG digital timing diagram renderer.

Supports the subset of VCD that Icarus emits for this project (scalar and
vector wires, #time stamps, scalar 0/1/x changes, vector b.. changes).
Renders a chosen set of signals over a chosen time window as a clean,
self-contained SVG suitable for slides. Not a general VCD tool.
"""
import argparse
import re


def parse_vcd(path):
    id2name, name2id, width = {}, {}, {}
    changes = {}   # id -> list of (time, value_str)
    t = 0
    with open(path) as f:
        in_defs = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if in_defs:
                if line.startswith("$var"):
                    # $var wire <w> <id> <name> [range] $end
                    parts = line.split()
                    w = int(parts[2]); vid = parts[3]; nm = parts[4]
                    id2name[vid] = nm; name2id[nm] = vid; width[nm] = w
                    changes.setdefault(vid, [])
                elif line.startswith("$enddefinitions"):
                    in_defs = False
                continue
            if line[0] == '#':
                t = int(line[1:])
            elif line[0] in "01xzXZ":
                vid = line[1:]
                changes.setdefault(vid, []).append((t, line[0]))
            elif line[0] in "bB":
                val, vid = line[1:].split()
                changes.setdefault(vid, []).append((t, val))
            elif line[0] == 'r':
                pass  # real, unused
    return name2id, width, changes


def value_at(series, t):
    v = None
    for (ct, cv) in series:
        if ct <= t:
            v = cv
        else:
            break
    return v


def changes_in(series, t0, t1):
    return [(ct, cv) for (ct, cv) in series if t0 < ct <= t1]


def render(path, out, signals, t0, t1, title, unit_ps=1000, label_us=True):
    name2id, width, changes = parse_vcd(path)
    row_h, top, left, w = 46, 64, 150, 940
    plot_w = w - left - 20
    height = top + row_h * len(signals) + 50

    def x(t):
        return left + (t - t0) / (t1 - t0) * plot_w

    hi, lo = 10, row_h - 14   # within-row offsets (relative to row top)
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" '
               f'viewBox="0 0 {w} {height}" font-family="Menlo,Consolas,monospace">')
    svg.append(f'<rect width="{w}" height="{height}" fill="#ffffff"/>')
    svg.append(f'<text x="{left}" y="34" font-size="20" font-weight="bold" '
               f'fill="#1a1a2e">{title}</text>')

    # light vertical gridlines at each SCK rising edge, if SCK present
    if "SCK" in name2id:
        sck = changes[name2id["SCK"]]
        for (ct, cv) in changes_in(sck, t0 - 1, t1):
            if cv == '1':
                gx = x(ct)
                svg.append(f'<line x1="{gx:.1f}" y1="{top-6}" x2="{gx:.1f}" '
                           f'y2="{top + row_h*len(signals)}" stroke="#e6e6ef" stroke-width="1"/>')

    for i, (nm, label, color) in enumerate(signals):
        ry = top + i * row_h
        svg.append(f'<text x="{left-14}" y="{ry+hi+16}" font-size="15" '
                   f'text-anchor="end" fill="#333">{label}</text>')
        svg.append(f'<line x1="{left}" y1="{ry+lo}" x2="{left+plot_w}" y2="{ry+lo}" '
                   f'stroke="#f0f0f0" stroke-width="1"/>')
        vid = name2id.get(nm)
        if vid is None:
            continue
        series = changes[vid]
        is_vec = width[nm] > 1
        start_v = value_at(series, t0)
        evs = changes_in(series, t0, t1)
        pts = [(t0, start_v)] + evs
        if is_vec:
            for j, (ct, cv) in enumerate(pts):
                nt = pts[j+1][0] if j+1 < len(pts) else t1
                x0, x1 = x(ct), x(nt)
                svg.append(f'<rect x="{x0:.1f}" y="{ry+hi}" width="{max(0,x1-x0):.1f}" '
                           f'height="{lo-hi}" fill="#eef" stroke="{color}" stroke-width="1.5"/>')
                try:
                    hexv = format(int(cv, 2), '08x')
                except ValueError:
                    hexv = cv
                svg.append(f'<text x="{(x0+x1)/2:.1f}" y="{ry+(hi+lo)/2+5:.1f}" '
                           f'font-size="13" text-anchor="middle" fill="{color}">{hexv}</text>')
        else:
            def ylvl(v):
                return ry + hi if v == '1' else ry + lo
            prev_x = x(t0)
            prev_y = ylvl(start_v if start_v else '0')
            path_d = [f'M {prev_x:.1f} {prev_y:.1f}']
            for (ct, cv) in evs:
                cx = x(ct)
                path_d.append(f'L {cx:.1f} {prev_y:.1f}')
                ny = ylvl(cv)
                path_d.append(f'L {cx:.1f} {ny:.1f}')
                prev_y = ny
            path_d.append(f'L {x(t1):.1f} {prev_y:.1f}')
            svg.append(f'<path d="{" ".join(path_d)}" fill="none" stroke="{color}" '
                       f'stroke-width="2.2"/>')

    # time axis
    ay = top + row_h * len(signals) + 8
    svg.append(f'<line x1="{left}" y1="{ay}" x2="{left+plot_w}" y2="{ay}" '
               f'stroke="#888" stroke-width="1"/>')
    for k in range(6):
        tt = t0 + (t1 - t0) * k / 5
        tx = x(tt)
        lbl = f'{tt/1e6:.1f}µs' if label_us else f'{int(tt)}'
        svg.append(f'<line x1="{tx:.1f}" y1="{ay}" x2="{tx:.1f}" y2="{ay+5}" stroke="#888"/>')
        svg.append(f'<text x="{tx:.1f}" y="{ay+20}" font-size="12" '
                   f'text-anchor="middle" fill="#666">{lbl}</text>')
    svg.append('</svg>')
    with open(out, "w") as f:
        f.write("\n".join(svg))
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vcd", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--t0", type=float, required=True)
    ap.add_argument("--t1", type=float, required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--signals", required=True,
                    help="comma list of name:label:color")
    args = ap.parse_args()
    sigs = []
    for spec in args.signals.split(","):
        nm, label, color = spec.split(":")
        sigs.append((nm, label, color))
    render(args.vcd, args.out, sigs, args.t0, args.t1, args.title)
