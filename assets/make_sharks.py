#!/usr/bin/env python3
"""Generate a Haj-style ASCII-mosaic shark SVG for a GitHub profile README."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def in_ellipse(x, y, cx, cy, rx, ry) -> bool:
    if rx == 0 or ry == 0:
        return False
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def in_triangle(px, py, ax, ay, bx, by, cx, cy) -> bool:
    v0x, v0y = cx - ax, cy - ay
    v1x, v1y = bx - ax, by - ay
    v2x, v2y = px - ax, py - ay
    den = v0x * v1y - v1x * v0y
    if abs(den) < 1e-12:
        return False
    u = (v2x * v1y - v1x * v2y) / den
    v = (v0x * v2y - v2x * v0y) / den
    return u >= 0 and v >= 0 and u + v <= 1


def sample_hash(*parts) -> float:
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def in_poly(px: float, py: float, pts: list[tuple[float, float]]) -> bool:
    n = len(pts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and (
            px < (xj - xi) * (py - yi) / (yj - yi + 1e-16) + xi
        ):
            inside = not inside
        j = i
    return inside


# Filled side-view shark, head on the left. Coordinates in 0..1.
# Drawn to match the Haj mosaic: plump body, tall dorsal, forked tail, hanging pectoral.
SHARK_POLY = [
    (0.010, 0.500),  # snout tip
    (0.055, 0.445),
    (0.130, 0.405),
    (0.230, 0.385),
    (0.320, 0.375),
    (0.365, 0.355),  # dorsal leading
    (0.455, 0.055),  # dorsal tip
    (0.545, 0.360),  # dorsal trailing
    (0.640, 0.390),
    (0.720, 0.415),  # peduncle top
    (0.780, 0.400),
    (0.985, 0.250),  # upper caudal tip
    (0.860, 0.445),
    (0.805, 0.500),  # tail fork
    (0.860, 0.555),
    (0.970, 0.730),  # lower caudal tip
    (0.780, 0.590),
    (0.720, 0.575),  # peduncle bottom
    (0.630, 0.600),
    (0.560, 0.630),
    (0.535, 0.710),  # pelvic tip
    (0.500, 0.620),
    (0.400, 0.630),
    (0.255, 0.860),  # pectoral tip
    (0.300, 0.640),
    (0.220, 0.615),
    (0.140, 0.590),
    (0.080, 0.575),  # lower jaw
    (0.040, 0.545),
]

TAIL_CUT_X = 0.72


def shark_parts(nx: float, ny: float, flip_x: bool = False) -> str | None:
    """Return 'body', 'tail', 'eye' or None."""
    if flip_x:
        nx = 1.0 - nx
    bend = 0.048 * math.sin(nx * math.pi)
    y = ny - bend

    if in_ellipse(nx, y, 0.148, 0.455, 0.026, 0.030):
        return "eye"

    in_dorsal = in_triangle(nx, y, 0.355, 0.370, 0.455, 0.020, 0.560, 0.370)
    in_upper_tail = in_triangle(nx, y, 0.715, 0.430, 0.995, 0.235, 0.805, 0.510)
    in_lower_tail = in_triangle(nx, y, 0.715, 0.560, 0.805, 0.500, 0.975, 0.745)
    # Crescent fork: cut a disk out of the tail trailing edge
    tail_fork = in_ellipse(nx, y, 0.935, 0.500, 0.055, 0.070) and nx > 0.88
    in_extra_tail = (in_upper_tail or in_lower_tail) and not tail_fork

    in_shape = in_poly(nx, y, SHARK_POLY) or in_dorsal or in_extra_tail
    if not in_shape:
        if in_ellipse(nx, y, 0.40, 0.50, 0.30, 0.145) and 0.08 < nx < 0.70:
            return "tail" if nx >= TAIL_CUT_X else "body"
        return None

    return "tail" if (nx >= TAIL_CUT_X or in_extra_tail) else "body"


def shade_at(nx: float, ny: float, part: str, flip_x: bool = False) -> int:
    """0 lightest … 3 darkest. Lighting from upper-left, darker belly and eye."""
    if flip_x:
        nx = 1.0 - nx
    bend = 0.048 * math.sin(nx * math.pi)
    y = ny - bend
    ymid = 0.50
    # vertical lighting
    v = (y - (ymid - 0.22)) / 0.44
    v = max(0.0, min(1.0, v))  # 0 top (light), 1 belly (dark)
    shade = 0.35 + 0.55 * v
    # snout a touch darker
    if nx < 0.16:
        shade += 0.12
    # gill slit band
    if 0.22 < nx < 0.27 and abs(y - ymid) < 0.12:
        shade += 0.18
    if part == "eye":
        return 3
    if part == "tail":
        shade += 0.08
    # edge highlight: cells near boundary slightly lighter — approximated by noise
    n = sample_hash("shade", round(nx, 3), round(ny, 3))
    shade = shade * 0.88 + n * 0.22
    if shade < 0.42:
        return 0
    if shade < 0.60:
        return 1
    if shade < 0.78:
        return 2
    return 3


CHARS = "abcdefghijkmnpqrstuvwxyz23456789#%+=<>~*o"

SHADE_BIAS = [
    ".:'`^",
    "abcdeghnosu~",
    "kmprvwxyz#%+=",
    "@HMNW8&%#",
]


def char_for(i: int, j: int, part: str, shade: int) -> str:
    if part == "eye":
        return "@"
    alphabet = SHADE_BIAS[shade]
    # Mix in general charset so it feels like Haj's mixed mosaic
    mixed = alphabet + CHARS
    n = int(sample_hash("ch", i, j, part) * len(mixed))
    return mixed[n]


def rasterize(cols: int, rows: int, flip_x: bool = False):
    """Return list of (i, j, ch, shade, part) for occupied cells, cropped to bbox."""
    raw = []
    for j in range(rows):
        ny = (j + 0.5) / rows
        for i in range(cols):
            nx = (i + 0.5) / cols
            part = shark_parts(nx, ny, flip_x=flip_x)
            if not part:
                continue
            shade = shade_at(nx, ny, part, flip_x=flip_x)
            ch = char_for(i, j, part, shade)
            raw.append((i, j, ch, shade, part))
    if not raw:
        return raw
    min_i = min(c[0] for c in raw)
    min_j = min(c[1] for c in raw)
    return [(i - min_i, j - min_j, ch, shade, part) for i, j, ch, shade, part in raw]


def preview_ascii(cols=88, rows=28) -> str:
    cells = rasterize(cols, rows)
    if not cells:
        return "(empty)"
    w = max(c[0] for c in cells) + 1
    h = max(c[1] for c in cells) + 1
    grid = [[" "] * w for _ in range(h)]
    for i, j, ch, shade, part in cells:
        grid[j][i] = "@" if part == "eye" else "#%*+."[3 - min(shade, 3)]
    return "\n".join("".join(row).rstrip() for row in grid)


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------

CELL_W = 7.2
CELL_H = 10.6
SHARK_COLS = 92
SHARK_ROWS = 30

# Scene
VB_W, VB_H = 1100, 340


def shark_group_svg(prefix: str, twinkle_every: int = 7, flip_x: bool = False) -> str:
    cells = rasterize(SHARK_COLS, SHARK_ROWS, flip_x=flip_x)
    body_chars = []
    tail_chars = []
    tail_pts = []
    for n, (i, j, ch, shade, part) in enumerate(cells):
        x = i * CELL_W
        y = (j + 1) * CELL_H
        tw = " tw" if (n % twinkle_every == 0 and part != "eye") else ""
        node = (
            f'<text x="{x:.1f}" y="{y:.1f}" class="s{shade}{tw}">{xml_escape(ch)}</text>'
        )
        if part == "tail":
            tail_chars.append(node)
            tail_pts.append((x, y))
        else:
            body_chars.append(node)
    body = "\n      ".join(body_chars)
    tail = "\n      ".join(tail_chars)
    if tail_pts:
        ox = max(p[0] for p in tail_pts) if flip_x else min(p[0] for p in tail_pts)
        oy = sum(p[1] for p in tail_pts) / len(tail_pts)
    else:
        ox = oy = 0
    return f'''  <g id="{prefix}">
    <g class="body">
      {body}
    </g>
    <g class="tail" style="transform-origin: {ox:.1f}px {oy:.1f}px;">
      {tail}
    </g>
  </g>'''


def xml_escape(ch: str) -> str:
    return (
        ch.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def grid_svg() -> str:
    lines = []
    step = 22
    for x in range(0, VB_W, step):
        for y in range(0, VB_H, step):
            # tiny mosaic specks, very faint, like Haj graph paper
            ch = "·" if ((x // step) + (y // step)) % 3 else "+"
            lines.append(
                f'<text x="{x}" y="{y}" class="grid">{ch}</text>'
            )
    return "\n    ".join(lines)


THEMES = {
    "light": {
        "grid": "#d4d2cc",
        "s0": "#8d8b84",
        "s1": "#5f5d58",
        "s2": "#353430",
        "s3": "#141413",
    },
    "dark": {
        "grid": "#2a2f38",
        "s0": "#5c6570",
        "s1": "#8b95a3",
        "s2": "#c5ced8",
        "s3": "#eef3f7",
    },
}


def build_svg(theme: str = "light") -> str:
    shark_l = shark_group_svg("shark-l", flip_x=False)
    shark_r = shark_group_svg("shark-r", flip_x=True)
    grid = grid_svg()
    pal = THEMES[theme]
    colors = f'''
    .grid {{ fill: {pal["grid"]}; }}
    .s0 {{ fill: {pal["s0"]}; }}
    .s1 {{ fill: {pal["s1"]}; }}
    .s2 {{ fill: {pal["s2"]}; }}
    .s3 {{ fill: {pal["s3"]}; }}
'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{VB_W}" height="{VB_H}" viewBox="0 0 {VB_W} {VB_H}" role="img"
     aria-label="Swimming ASCII mosaic sharks">
  <title>ASCII sharks</title>
  <style>
    text {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0;
    }}
    .grid {{
      font-size: 9px;
      font-weight: 400;
    }}
{colors}

    /* Glyphs stay upright. Direction comes from a left-facing vs right-facing mosaic. */
    @keyframes swim-a {{
      0%   {{ transform: translate(-420px, 210px) rotate(-7deg) scale(1.08, 1.08); }}
      45%  {{ transform: translate( 180px,  95px) rotate(  3deg) scale(1.08, 1.08); }}
      100% {{ transform: translate(1200px, -50px) rotate( -6deg) scale(1.08, 1.08); }}
    }}
    @keyframes swim-b {{
      0%   {{ transform: translate(1150px, -10px) rotate(  4deg) scale(0.58, 0.58); }}
      100% {{ transform: translate(-560px, 230px) rotate(  5deg) scale(0.58, 0.58); }}
    }}
    @keyframes swim-c {{
      0%   {{ transform: translate(-260px, -30px) rotate(  3deg) scale(0.40, 0.40); }}
      100% {{ transform: translate(1220px,  90px) rotate( -2deg) scale(0.40, 0.40); }}
    }}
    @keyframes swim-d {{
      0%   {{ transform: translate(1100px, 250px) rotate( -3deg) scale(0.28, 0.28); }}
      100% {{ transform: translate(-420px,  40px) rotate(  3deg) scale(0.28, 0.28); }}
    }}
    @keyframes wag {{
      0%, 100% {{ transform: rotate(-3deg); }}
      50%      {{ transform: rotate(3deg); }}
    }}
    @keyframes twinkle {{
      0%, 100% {{ opacity: 1; }}
      50%      {{ opacity: 0.42; }}
    }}

    .swimmer {{ transform-box: fill-box; transform-origin: center; }}
    .a {{ animation: swim-a 22s linear infinite; animation-delay: -8s; }}
    .b {{ animation: swim-b 29s linear infinite; animation-delay: -2s; }}
    .c {{ animation: swim-c 36s linear infinite; animation-delay: -22s; opacity: 0.65; }}
    .d {{ animation: swim-d 41s linear infinite; animation-delay: -30s; opacity: 0.45; }}
    .tail {{
      transform-box: fill-box;
      animation: wag 0.8s ease-in-out infinite;
    }}
    .tw {{ animation: twinkle 3s steps(2, end) infinite; }}

    @media (prefers-reduced-motion: reduce) {{
      .a, .b, .c, .d, .tail, .tw {{ animation: none !important; }}
      .a {{ transform: translate(90px, 120px) rotate(-5deg) scale(1.08, 1.08); }}
      .b {{ transform: translate(680px, 20px) rotate(4deg) scale(0.58, 0.58); }}
      .c {{ transform: translate(20px, 10px) rotate(3deg) scale(0.40, 0.40); }}
      .d {{ transform: translate(820px, 230px) rotate(-3deg) scale(0.28, 0.28); }}
    }}
  </style>

  <rect width="100%" height="100%" fill="transparent"/>
  <g class="paper">{grid}</g>

  <defs>
{shark_r}
{shark_l}
  </defs>

  <g class="swimmer a"><use href="#shark-r" xlink:href="#shark-r"/></g>
  <g class="swimmer b"><use href="#shark-l" xlink:href="#shark-l"/></g>
  <g class="swimmer c"><use href="#shark-r" xlink:href="#shark-r"/></g>
  <g class="swimmer d"><use href="#shark-l" xlink:href="#shark-l"/></g>
</svg>
'''


def main():
    out_dir = Path("/tmp/shark-gen")
    out_dir.mkdir(parents=True, exist_ok=True)
    preview = preview_ascii()
    (out_dir / "preview.txt").write_text(preview + "\n")
    print(preview)
    print("\n--- occupancy ---")
    cells = rasterize(SHARK_COLS, SHARK_ROWS)
    print(f"cells: {len(cells)} / {SHARK_COLS * SHARK_ROWS}")
    for theme in ("light", "dark"):
        svg = build_svg(theme)
        path = out_dir / f"haj-sharks-{theme}.svg"
        path.write_text(svg)
        print(f"wrote {path} ({path.stat().st_size} bytes)")
    # Combined preview file (light as default)
    (out_dir / "haj-sharks.svg").write_text(build_svg("light"))


if __name__ == "__main__":
    main()
