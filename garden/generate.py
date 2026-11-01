#!/usr/bin/env python3
"""Grow a Delft-blue botanical plate from a year of GitHub contributions.

One stem per week: taller and more elaborate the busier the week was. Plants
are seeded from their week's date, so a week keeps its shape as the year rolls
on. Standard library only.

  python3 generate.py contributions.json --out .
"""
import argparse
import datetime as dt
import json
import math
import random
from pathlib import Path

W, H = 1280, 500
GROUND = 424
LEFT, RIGHT = 54, W - 54
H_MIN, H_RANGE = 30, 300

PALETTES = {
    "light": dict(ink="#16356f", deep="#1b47a0", mid="#3c74d2", pale="#c4d9f6",
                  leaf_deep="#163f7c", leaf="#2f6cb0", leaf_pale="#9cc2e4",
                  vein="#f4f8ff", gold="#d07a22", text="#16356f", muted="#5b6f94", ghost=.15),
    "dark": dict(ink="#a9c6f4", deep="#2a5fc4", mid="#5f97ec", pale="#d3e3fb",
                 leaf_deep="#2a5a9c", leaf="#4f8ccc", leaf_pale="#b5d4ee",
                 vein="#eef5ff", gold="#eeb062", text="#cfe0fa", muted="#8ba0c2", ghost=.08),
}


def f(n):
    """Compact number: one decimal, no trailing zero."""
    s = f"{n:.1f}"
    return s[:-2] if s.endswith(".0") else s


def d(*parts):
    return " ".join(f(p) if isinstance(p, (int, float)) else p for p in parts)


# ------------------------------------------------------------------ shapes
def petal_path(r, L, w):
    j = lambda v: v * (1 + r.uniform(-.07, .07))
    return d("M0 0 C", -j(w * .35), -L * .15, -j(w * .64), -j(L * .62), -j(w * .44), -j(L * .9),
             "C", -w * .26, -j(L * 1.05), -w * .08, -L * .98, 0, -L * r.uniform(.88, .94),
             "C", w * .09, -L * .98, w * .28, -j(L * 1.05), j(w * .46), -j(L * .88),
             "C", j(w * .64), -j(L * .6), j(w * .34), -L * .15, 0, 0, "Z")


def lily_petal_path(r, L, w):
    j = lambda v: v * (1 + r.uniform(-.06, .06))
    tip = r.uniform(-.1, .1) * w
    return d("M0 0 C", -j(w * .62), -L * .3, -j(w * .5), -j(L * .74), tip, -L,
             "C", j(w * .5), -j(L * .74), j(w * .62), -L * .3, 0, 0, "Z")


def flower(r, x, y, R, cls, lean=0):
    """Open bloom: gradient petals, engraved veins, a lifted highlight, gold stamens."""
    lily = r.random() < .3
    n = 6 if lily else r.choice((5, 5, 5, 6))
    tilt = r.uniform(.78, 1)
    start = r.uniform(0, 360)
    o = [f'<g transform="translate({f(x)} {f(y)}) rotate({f(lean)}) scale(1 {tilt:.2f})"><g class="{cls}">']
    width = R * .56 if lily else R * (2.7 / n + .48)
    shape = lily_petal_path if lily else petal_path
    for i in range(n):
        L = R * r.uniform(.9, 1.06)
        a = start + i * 360 / n + r.uniform(-5, 5)
        p = [f'<g transform="rotate({f(a)})">',
             f'<path d="{shape(r, L, width)}" fill="url(#p)" class="o"/>']
        if R > 11:
            veins = []
            count = 5 if R > 24 else 3
            for k in range(count):
                u = (k - (count - 1) / 2) / max(1, count - 1)
                veins.append(d("M", u * R * .08, -L * .12, "Q", u * width * .46, -L * .5,
                               u * width * .62, -L * r.uniform(.74, .86)))
            p.append(f'<path d="{" ".join(veins)}" class="v"/>')
            h = r.uniform(-.14, .14) * width
            p.append(f'<path d="{d("M", h, -L * .3, "Q", h - width * .05, -L * .6, h, -L * .84, "Q", h + width * .05, -L * .6, h, -L * .3, "Z")}" class="h"/>')
        p.append("</g>")
        o.append("".join(p))
    if R > 9:
        stamens = []
        heads = []
        for i in range(9 if R > 22 else 5):
            a = r.uniform(0, math.tau)
            s = R * r.uniform(.14, .26)
            px, py = s * math.cos(a), s * math.sin(a)
            stamens.append(d("M0 0L", px, py))
            heads.append(f'<circle cx="{f(px)}" cy="{f(py)}" r="{f(max(.7, R * .025))}"/>')
        o.append(f'<path d="{" ".join(stamens)}" class="st"/><g class="an">{"".join(heads)}</g>')
    o.append(f'<circle r="{f(max(1.2, R * .07))}" class="an"/></g></g>')
    return "".join(o)


def leaf(r, x, y, angle, L, cls, lobed=True):
    w = L * r.uniform(.2, .27)
    lobes = 4 if lobed else 0
    if lobes:
        sides = []
        for s in (-1, 1):
            pts = []
            for k in range(1, lobes * 2):
                t = k / (lobes * 2)
                tip = k % 2 == 1
                profile = math.sin(math.pi * t ** .8) ** .8
                pts.append((s * w * profile * (1.14 if tip else .78), -L * (t + (.05 if tip else 0))))
            sides.append(pts)
        left, right = sides
        path = ["M0 0"]
        for i in range(0, len(left) - 1, 2):
            path.append(d("Q", left[i][0], left[i][1], left[i + 1][0], left[i + 1][1]))
        path.append(d("Q", left[-1][0], left[-1][1], 0, -L))
        right = right[::-1]
        for i in range(0, len(right) - 1, 2):
            path.append(d("Q", right[i][0], right[i][1], right[i + 1][0], right[i + 1][1]))
        path.append(d("Q", right[-1][0], right[-1][1], 0, 0))
        outline = " ".join(path) + "Z"
    else:
        outline = d("M0 0 C", -w, -L * .3, -w * .8, -L * .75, 0, -L,
                    "C", w * .8, -L * .75, w, -L * .3, 0, 0, "Z")
    ribs = [d("M0", -L * .04, "L0", -L * .92)]
    if L > 15:
        for k in range(1, 5):
            t = k / 5.4
            for s in (-1, 1):
                ribs.append(d("M0", -L * t, "L", s * w * .62 * math.sin(math.pi * t), -L * (t + .12)))
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})"><g class="{cls}">'
            f'<path d="{outline}" fill="url(#l)" class="o"/>'
            f'<path d="{" ".join(ribs)}" class="r"/></g></g>')


def bud(r, x, y, angle, s, cls):
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})"><g class="{cls}">'
            f'<path d="{d("M0 0 C", -s * .55, -s * .5, -s * .3, -s * 1.1, 0, -s * 1.35, "C", s * .3, -s * 1.1, s * .55, -s * .5, 0, 0, "Z")}" fill="url(#p)" class="o"/>'
            f'<path d="{d("M0 0 Q", -s * .42, -s * .28, -s * .24, -s * .6, "M0 0 Q", s * .42, -s * .28, s * .24, -s * .6)}" class="a"/>'
            "</g></g>")


def forget_me_nots(r, x, y, cls):
    """A tight cyme of tiny five-petalled flowers."""
    o = [f'<g transform="translate({f(x)} {f(y)})"><g class="{cls}">']
    for _ in range(r.randint(4, 7)):
        cx, cy, R = r.uniform(-11, 11), r.uniform(-9, 9), r.uniform(2.1, 3.4)
        petals = "".join(
            f'<circle cx="{f(cx + R * .75 * math.cos(k * math.tau / 5))}" cy="{f(cy + R * .75 * math.sin(k * math.tau / 5))}" r="{f(R * .56)}"/>'
            for k in range(5))
        o.append(f'<g class="fm">{petals}</g><circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * .25)}" class="an"/>')
    o.append("</g></g>")
    return "".join(o)


def umbel(r, x, y, angle, s, cls):
    """Queen Anne's lace: a fan of rays, each ending in a floret."""
    rays, dots = [], []
    for k in range(9):
        a = math.radians(-152 + k * 124 / 8 + r.uniform(-3, 3))
        L = s * r.uniform(.84, 1.08)
        px, py = L * math.cos(a), L * math.sin(a)
        rays.append(d("M0 0L", px, py))
        for _ in range(3):
            dots.append(f'<circle cx="{f(px + r.uniform(-2.6, 2.6))}" cy="{f(py + r.uniform(-2.6, 2.6))}" r="{f(r.uniform(.8, 1.4))}"/>')
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})"><g class="{cls}">'
            f'<path d="{" ".join(rays)}" class="a"/><g class="fm">{"".join(dots)}</g></g></g>')


def tendril(r, x, y, s, side, delay):
    pts = []
    turns = r.uniform(1.6, 2.3)
    for k in range(25):
        t = k / 24
        a = t * turns * math.tau
        rad = s * (1 - t) ** 1.25
        pts.append((x + side * (s * .9 * t + rad * math.sin(a) * .62), y - s * 1.1 * t + rad * (1 - math.cos(a)) * .52))
    path = d("M", pts[0][0], pts[0][1])
    for i in range(1, len(pts) - 1, 2):
        path += " " + d("Q", pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
    return f'<path d="{path}" pathLength="1" class="a s" style="animation-delay:{delay:.2f}s"/>'


# ------------------------------------------------------------------ plants
def stem_at(p, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    m = 1 - t
    x = m ** 3 * x0 + 3 * m * m * t * x1 + 3 * m * t * t * x2 + t ** 3 * x3
    y = m ** 3 * y0 + 3 * m * m * t * y1 + 3 * m * t * t * y2 + t ** 3 * y3
    dx = 3 * m * m * (x1 - x0) + 6 * m * t * (x2 - x1) + 3 * t * t * (x3 - x2)
    dy = 3 * m * m * (y1 - y0) + 6 * m * t * (y2 - y1) + 3 * t * t * (y3 - y2)
    return x, y, math.degrees(math.atan2(dx, -dy))


def stem_path(p):
    return d("M", p[0][0], p[0][1], "C", p[1][0], p[1][1], p[2][0], p[2][1], p[3][0], p[3][1])


def tuft(r, x, delay):
    blades = []
    for _ in range(r.randint(2, 4)):
        tx = x + r.uniform(-9, 9)
        blades.append(d("M", x + r.uniform(-2, 2), GROUND, "Q", (x + tx) / 2, GROUND - 9, tx, GROUND - r.uniform(9, 20)))
    return f'<path d="{" ".join(blades)}" pathLength="1" class="a s" style="animation-delay:{delay:.2f}s"/>'


def plant(week, ratio, x, index, side):
    """One week's plant. ratio is log(1+c)/log(1+cmax), so 0 is an empty week."""
    r = random.Random(week)
    t0 = index * .085
    if ratio == 0:
        return tuft(r, x, t0)
    h = H_MIN + H_RANGE * ratio
    lean = side * r.uniform(4, 30) * (0.5 + ratio)
    top = (x + lean, GROUND - h)
    bow = side * r.uniform(10, 28) * (.5 + ratio)
    p = ((x, GROUND), (x - bow, GROUND - h * .4), (top[0] + bow * .8, GROUND - h * .72), top)
    width = 1 + 1.8 * ratio
    o = [f'<g style="--t:{t0:.2f}s">',
         f'<path d="{stem_path(p)}" pathLength="1" class="w s" stroke-width="{f(width)}"/>']

    # leaves alternate up the stem and shrink towards the tip
    leaves = 2 + round(ratio * 6)
    for k in range(leaves):
        t = .14 + .72 * k / max(1, leaves - 1) if leaves > 1 else .4
        lx, ly, a = stem_at(p, t)
        s = 1 if k % 2 else -1
        L = (14 + 30 * ratio) * (1.1 - t * .65) * r.uniform(.85, 1.15)
        o.append(leaf(r, lx, ly, a + s * r.uniform(46, 74), L, f"g d{min(k + 1, 6)}", lobed=ratio > .3))

    if ratio > .42 and r.random() < .75:
        lx, ly, _ = stem_at(p, r.uniform(.3, .55))
        o.append(tendril(r, lx, ly, r.uniform(10, 19), r.choice((-1, 1)), t0 + .6))

    # side branches on the busier weeks
    branches = 0 if ratio < .36 else 1 if ratio < .62 else 2
    for b in range(branches):
        bx, by, _ = stem_at(p, r.uniform(.38, .72))
        s = -side if b == 0 else side
        L = (40 + 54 * ratio) * r.uniform(.8, 1.1)
        if not 34 < bx + s * L * .72 < W - 34:       # keep the branch on the plate
            s = -s
        end = (bx + s * L * .72, by - L * .72)
        q = ((bx, by), (bx + s * L * .12, by - L * .36), (end[0] - s * L * .24, end[1] + L * .24), end)
        o.append(f'<path d="{stem_path(q)}" pathLength="1" class="w s" stroke-width="{f(width * .6)}" style="animation-delay:{t0 + .5:.2f}s"/>')
        lx, ly, a = stem_at(q, .5)
        o.append(leaf(r, lx, ly, a + s * 60, 15 + 12 * ratio, "g d4", lobed=False))
        _, _, a = stem_at(q, 1)
        kind = r.choice(("fm", "umbel", "bud", "flower"))
        if kind == "fm":
            o.append(forget_me_nots(r, end[0], end[1], "g d7"))
        elif kind == "umbel":
            o.append(umbel(r, end[0], end[1], a, 26, "g d7"))
        elif kind == "bud":
            o.append(bud(r, end[0], end[1], a, 11, "g d7"))
        else:
            o.append(flower(r, end[0], end[1], 11 + 9 * ratio, "g d7", a))

    # what the stem ends in
    _, _, a = stem_at(p, 1)
    if ratio < .28:
        o.append(bud(r, top[0], top[1], a, 7 + 8 * ratio, "g d8"))
    elif ratio < .42:
        o.append(forget_me_nots(r, top[0], top[1], "g d8") if r.random() < .5
                 else umbel(r, top[0], top[1], a, 20, "g d8"))
    else:
        o.append(flower(r, top[0], top[1], 8 + 46 * ratio ** 2.2, "g d8", a))
    o.append("</g>")
    return "".join(o)


def ghost(week, ratio, x, index):
    """A pale bloom behind the busiest weeks, like a wash left to dry."""
    r = random.Random(week + "ghost")
    y = GROUND - (H_MIN + H_RANGE * ratio) * r.uniform(.42, .6)
    gx = min(x + r.choice((-1, 1)) * r.uniform(26, 58), RIGHT - 70)
    return (f'<g class="gh" style="--t:{index * .085:.2f}s">'
            + flower(r, gx, y, r.uniform(46, 66), "g d8", r.uniform(0, 40))
            + "</g>")


def star(x, y, s, delay):
    """Four-pointed gold compass star, marking the year's peak."""
    q = s * .13
    long = d("M0", -s, "L", q, -q, s, 0, q, q, 0, s, -q, q, -s, 0, -q, -q, "Z")
    k = s * .46
    short = d("M", -k, -k, "L0", -q, k, -k, q, 0, k, k, 0, q, -k, k, -q, 0, "Z")
    return (f'<g transform="translate({f(x)} {f(y)})"><g class="g" style="animation-delay:{delay:.2f}s">'
            f'<path d="{short}" class="an" opacity=".55"/><path d="{long}" class="an"/></g></g>')


def groundline(r):
    """The stems' shared baseline: a slow wave with small leaves."""
    pts = [(LEFT - 26 + i * (RIGHT - LEFT + 52) / 40, GROUND + 3 * math.sin(i * .9) + r.uniform(-.8, .8)) for i in range(41)]
    path = d("M", pts[0][0], pts[0][1])
    for i in range(1, len(pts) - 1, 2):
        path += " " + d("Q", pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
    o = [f'<path d="{path}" pathLength="1" class="w s" stroke-width="1.5" style="animation-duration:3s"/>']
    for i in range(3, 39, 3):
        x, y = pts[i]
        o.append(leaf(r, x, y, r.choice((-1, 1)) * r.uniform(68, 112), r.uniform(9, 15), "g", lobed=False))
    return "".join(o)


# ------------------------------------------------------------------ the plate
def css(c):
    return f"""
.gh{{opacity:{c['ghost']}}}
.o{{stroke:{c['ink']};stroke-width:.55;stroke-linejoin:round}}
.v{{fill:none;stroke:{c['ink']};stroke-width:.4;stroke-opacity:.5}}
.h{{fill:{c['vein']};fill-opacity:.55}}
.r{{fill:none;stroke:{c['vein']};stroke-width:.6;stroke-opacity:.85}}
.st{{fill:none;stroke:{c['gold']};stroke-width:.6}}
.an{{fill:{c['gold']}}}
.fm{{fill:{c['mid']}}}
.a{{fill:none;stroke:{c['leaf']};stroke-width:.8;stroke-linecap:round}}
.w{{fill:none;stroke:{c['leaf_deep']};stroke-linecap:round}}
text{{font-family:Georgia,'Iowan Old Style','Times New Roman',serif;fill:{c['text']}}}
.t{{font-size:17px;font-style:italic}}
.m{{font-size:11.5px;letter-spacing:.14em;fill:{c['muted']}}}
.s{{stroke-dasharray:1;animation:draw 1.1s cubic-bezier(.4,0,.2,1) var(--t,0s) both}}
.g{{animation:open .7s cubic-bezier(.3,1.5,.5,1) both}}
.d1{{animation-delay:calc(var(--t) + .25s)}}.d2{{animation-delay:calc(var(--t) + .35s)}}
.d3{{animation-delay:calc(var(--t) + .45s)}}.d4{{animation-delay:calc(var(--t) + .55s)}}
.d5{{animation-delay:calc(var(--t) + .65s)}}.d6{{animation-delay:calc(var(--t) + .75s)}}
.d7{{animation-delay:calc(var(--t) + .9s)}}.d8{{animation-delay:calc(var(--t) + 1s)}}
@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}
@keyframes open{{from{{transform:scale(0);opacity:0}}to{{transform:scale(1);opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.s,.g{{animation:none}}}}
"""


def weeks_from(days):
    """Group days into Sunday-started weeks, matching GitHub's calendar."""
    weeks = {}
    for day in days:
        date = dt.date.fromisoformat(day["date"])
        start = date - dt.timedelta(days=(date.weekday() + 1) % 7)
        weeks[start] = weeks.get(start, 0) + day["count"]
    return sorted(weeks.items())


def month_labels(weeks, xs):
    o, seen = [], None
    for (start, _), x in zip(weeks, xs):
        if start.month != seen:
            seen = start.month
            o.append(f'<text x="{f(x)}" y="{GROUND + 27}" class="m">{start.strftime("%b").upper()}</text>')
    return "".join(o)


def plate(days, theme):
    c = PALETTES[theme]
    weeks = weeks_from(days)
    total = sum(n for _, n in weeks)
    active = sum(1 for day in days if day["count"] > 0)
    cmax = max(n for _, n in weeks)
    step = (RIGHT - LEFT) / (len(weeks) - 1)
    xs = [LEFT + i * step for i in range(len(weeks))]
    plants, ghosts = [], []
    peak = 0
    for i, ((start, n), x) in enumerate(zip(weeks, xs)):
        ratio = math.log1p(n) / math.log1p(cmax)
        plants.append((ratio, plant(start.isoformat(), ratio, x, i, 1 if i % 2 else -1)))
        if ratio > .7:
            ghosts.append(ghost(start.isoformat(), ratio, x, i))
        if n == cmax:
            peak = i
    plants.sort(key=lambda item: -item[0])       # the tall stand behind the short
    span = f'{weeks[0][0].strftime("%b %Y")} to {weeks[-1][0].strftime("%b %Y")}'
    return "".join((
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Botanical plate of {total} GitHub contributions, one plant per week">',
        f"<style>{css(c)}</style><defs>",
        f'<linearGradient id="p" x1=".5" y1="1" x2=".5" y2="0"><stop offset="0" stop-color="{c["deep"]}"/>'
        f'<stop offset=".5" stop-color="{c["mid"]}"/><stop offset="1" stop-color="{c["pale"]}"/></linearGradient>',
        f'<linearGradient id="l" x1=".5" y1="1" x2=".5" y2="0"><stop offset="0" stop-color="{c["leaf_deep"]}"/>'
        f'<stop offset=".6" stop-color="{c["leaf"]}"/><stop offset="1" stop-color="{c["leaf_pale"]}"/></linearGradient>',
        "</defs>",
        "".join(ghosts),
        "".join(item[1] for item in plants),
        star(xs[peak] + 60, 46, 15, peak * .085 + 1.6),
        groundline(random.Random(weeks[0][0].isoformat())),
        month_labels(weeks, xs),
        f'<text x="{W / 2}" y="{H - 16}" text-anchor="middle" class="t">Hortus Dimas, {span}: '
        f"{total} contributions over {active} days, one stem per week</text>",
        "</svg>",
    ))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("data", help="JSON list of {date, count}")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    days = json.loads(Path(args.data).read_text())
    for theme in PALETTES:
        Path(args.out, f"garden-{theme}.svg").write_text(plate(days, theme), encoding="utf-8")


if __name__ == "__main__":
    main()
