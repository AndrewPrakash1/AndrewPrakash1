#!/usr/bin/env python3
"""Build Stranger Things-style profile banner SVG with lightning."""

from __future__ import annotations

import html
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent
FONT_PATH = Path("/tmp/fonts/CormorantGaramond.ttf")
OUT_SVG = ROOT / "readout.svg"

LINE1 = "WORK LIKE HELL"
LINE2 = "- ELON MUSK"

STRIKE_PERIOD_S = 4.5

# Each bolt: id, delay, kind, list of polylines (each polyline is point list)
BoltSpec = tuple[str, float, str, list[list[tuple[float, float]]]]

BOLT_SPECS: list[BoltSpec] = [
    (
        "bolt-a",
        0.0,
        "major",
        [
            [(0, 55), (95, 110), (62, 135), (155, 205), (118, 228), (210, 310), (175, 332), (290, 420)],
            [(155, 205), (205, 188), (248, 165)],
            [(118, 228), (85, 268), (55, 302)],
            [(210, 310), (260, 295), (310, 275)],
        ],
    ),
    (
        "bolt-b",
        0.08,
        "major",
        [
            [(1200, 40), (1095, 105), (1135, 128), (1040, 198), (1085, 218), (980, 295), (1025, 318), (920, 420)],
            [(1040, 198), (990, 175), (940, 158)],
            [(1085, 218), (1120, 255), (1155, 290)],
            [(980, 295), (930, 278), (875, 260)],
        ],
    ),
    (
        "bolt-c",
        0.0,
        "minor",
        [
            [(420, 0), (445, 75), (428, 92), (460, 165), (442, 182), (468, 250)],
            [(460, 165), (495, 148), (520, 130)],
        ],
    ),
    (
        "bolt-d",
        0.05,
        "minor",
        [
            [(780, 0), (758, 88), (778, 102), (745, 178), (768, 195), (738, 265)],
            [(745, 178), (715, 160), (688, 145)],
        ],
    ),
    (
        "bolt-e",
        0.1,
        "minor",
        [
            [(600, 0), (615, 62), (598, 78), (628, 145), (608, 162), (635, 228)],
        ],
    ),
    (
        "bolt-f",
        0.15,
        "minor",
        [
            [(350, 25), (368, 95), (352, 110), (382, 185), (365, 200), (390, 270)],
        ],
    ),
    (
        "bolt-g",
        0.12,
        "minor",
        [
            [(850, 20), (832, 90), (848, 105), (820, 175), (838, 190), (812, 255)],
        ],
    ),
]


def points_to_path(pts: list[tuple[float, float]]) -> str:
    if not pts:
        return ""
    parts = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L {x:.1f} {y:.1f}")
    return " ".join(parts)


def bolt_group(bolt_id: str, delay: float, kind: str, polylines: list[list[tuple[float, float]]]) -> str:
    if kind == "major":
        outer_w, mid_w, core_w = 16, 9, 2.2
    else:
        outer_w, mid_w, core_w = 10, 5.5, 1.4

    paths = "".join(
        f'<path d="{points_to_path(pts)}" class="bolt-outer" stroke-width="{outer_w}"/>'
        f'<path d="{points_to_path(pts)}" class="bolt-mid" stroke-width="{mid_w}"/>'
        f'<path d="{points_to_path(pts)}" class="bolt-core" stroke-width="{core_w}"/>'
        for pts in polylines
    )
    return f'  <g class="lightning {kind} {bolt_id}" style="animation-delay:{delay}s">{paths}</g>'


def lightning_svg() -> str:
    return "\n".join(bolt_group(*spec) for spec in BOLT_SPECS)


def treeline_svg() -> str:
    # Jagged forest silhouette along the bottom (Upside Down treeline)
    return """
  <path class="trees" d="M 0 420 L 0 398
    C 35 388, 55 402, 90 392 C 120 384, 145 398, 180 388
    C 215 378, 240 392, 275 384 C 310 376, 335 390, 370 382
    C 405 374, 430 388, 465 380 C 500 372, 525 386, 560 378
    C 595 370, 620 384, 655 376 C 690 368, 715 382, 750 374
    C 785 366, 810 380, 845 372 C 880 364, 905 378, 940 370
    C 975 362, 1000 376, 1035 368 C 1070 360, 1095 374, 1130 366
    C 1165 358, 1185 372, 1200 365 L 1200 420 Z"/>
"""


def sky_svg() -> str:
    return """
  <rect width="1200" height="420" fill="url(#skyBase)"/>
  <ellipse cx="280" cy="120" rx="220" ry="140" fill="url(#cloudRed)" opacity="0.55"/>
  <ellipse cx="920" cy="100" rx="260" ry="150" fill="url(#cloudRed)" opacity="0.5"/>
  <ellipse cx="600" cy="80" rx="180" ry="100" fill="url(#cloudBright)" opacity="0.35"/>
  <rect width="1200" height="420" fill="url(#skyVignette)"/>
  <g class="sky-flash">
    <ellipse cx="300" cy="140" rx="240" ry="160" fill="#ff2840" opacity="0.25"/>
    <ellipse cx="900" cy="130" rx="280" ry="170" fill="#ff2840" opacity="0.22"/>
  </g>
"""


def load_font():
    if not FONT_PATH.is_file():
        raise SystemExit(f"Font missing: {FONT_PATH}")
    src = TTFont(FONT_PATH)
    font = instantiateVariableFont(src, {"wght": 700}, inplace=False)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]
    return upem, cmap, gs, hmtx


def word_paths(text: str, cmap, gs, hmtx, tracking: int = 70) -> tuple[str, float]:
    x = 0.0
    chunks: list[str] = []
    for ch in text:
        name = cmap[ord(ch)]
        adv = hmtx[name][0]
        pen = SVGPathPen(gs)
        gs[name].draw(pen)
        d = pen.getCommands()
        if d:
            chunks.append(
                f'<path transform="translate({x:.2f},0)" d="{html.escape(d, quote=True)}"/>'
            )
        x += adv + tracking
    if text:
        x -= tracking
    return "\n".join(chunks), x


def emit(
    text: str,
    cx: float,
    baseline: float,
    size: float,
    fill: str,
    upem: int,
    cmap,
    gs,
    hmtx,
    stroke: str | None = None,
    sw: float = 0,
    extra: str = "",
    tracking: int = 70,
) -> tuple[str, float]:
    inner, units = word_paths(text, cmap, gs, hmtx, tracking=tracking)
    width = units * size / upem
    x = cx - width / 2
    sy = -size / upem
    stroke_attr = ""
    if stroke:
        stroke_attr = f' stroke="{stroke}" stroke-width="{sw}"'
    return (
        f'<g fill="{fill}"{stroke_attr} transform="translate({x:.2f},{baseline:.2f}) scale({size / upem:.6f},{sy:.6f})" {extra}>\n'
        f"{inner}\n</g>"
    ), width


def layer(
    text: str,
    baseline: float,
    size: float,
    cx: float,
    upem: int,
    cmap,
    gs,
    hmtx,
    tracking: int,
    fill: str,
    stroke: str | None = None,
    sw: float = 0,
    extra: str = "",
) -> str:
    g, _ = emit(
        text,
        cx,
        baseline,
        size,
        fill,
        upem,
        cmap,
        gs,
        hmtx,
        stroke,
        sw,
        extra,
        tracking,
    )
    return g


def main() -> None:
    upem, cmap, gs, hmtx = load_font()

    w, h = 1200, 420
    cx = w / 2
    size1, track1 = 78, 38
    size2, track2 = 56, 42

    line1_main = layer(LINE1, 178, size1, cx, upem, cmap, gs, hmtx, track1, "#ff3a4a", "#ff6b78", 2.0, "")
    line2_main = layer(LINE2, 288, size2, cx, upem, cmap, gs, hmtx, track2, "#ff3a4a", "#ff6b78", 1.8, "")
    main_title = line1_main + line2_main

    glow_l1 = layer(LINE1, 178, size1, cx, upem, cmap, gs, hmtx, track1, "#ff3a4a", extra='opacity="0.45"')
    glow_l2 = layer(LINE2, 288, size2, cx, upem, cmap, gs, hmtx, track2, "#ff3a4a", extra='opacity="0.45"')
    glow = glow_l1 + glow_l2

    _, w1 = emit(LINE1, cx, 178, size1, "#ff3a4a", upem, cmap, gs, hmtx, tracking=track1)
    _, w2 = emit(LINE2, cx, 288, size2, "#ff3a4a", upem, cmap, gs, hmtx, tracking=track2)
    rule_w = min(max(w1, w2) + 80, w - 80)
    x0 = cx - rule_w / 2
    x1 = cx + rule_w / 2

    aria = f"{LINE1} {LINE2.strip()}"
    bolts = lightning_svg()

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{aria}">
  <title>{LINE1}</title>
  <desc>Neon quote banner with lightning: {aria}</desc>
  <style>
    @keyframes neon-flicker {{
      0%, 83%, 100% {{ opacity: 1; }}
      84% {{ opacity: 0.72; }}
      86% {{ opacity: 0.95; }}
      88% {{ opacity: 0.55; }}
      91% {{ opacity: 1; }}
    }}
    @keyframes strike-major {{
      0%, 83%, 100% {{ opacity: 0; }}
      84% {{ opacity: 1; }}
      86% {{ opacity: 0.35; }}
      88% {{ opacity: 0.75; }}
      91% {{ opacity: 0; }}
    }}
    @keyframes strike-minor {{
      0%, 100% {{ opacity: 0; }}
      17.8% {{ opacity: 0; }}
      18.4% {{ opacity: 0.55; }}
      19% {{ opacity: 0; }}
      34.8% {{ opacity: 0; }}
      35.3% {{ opacity: 0.42; }}
      35.8% {{ opacity: 0; }}
      51.5% {{ opacity: 0; }}
      52% {{ opacity: 0.48; }}
      52.5% {{ opacity: 0; }}
      68.2% {{ opacity: 0; }}
      68.7% {{ opacity: 0.38; }}
      69.2% {{ opacity: 0; }}
      83%, 91% {{ opacity: 0; }}
    }}
    @keyframes sky-pulse {{
      0%, 83%, 100% {{ opacity: 0; }}
      84% {{ opacity: 0.85; }}
      86% {{ opacity: 0.25; }}
      88% {{ opacity: 0.65; }}
      91% {{ opacity: 0; }}
    }}
    .title {{ animation: neon-flicker {STRIKE_PERIOD_S}s infinite; }}
    .sky-flash {{ animation: sky-pulse {STRIKE_PERIOD_S}s infinite; opacity: 0; }}
    .lightning.major {{
      animation: strike-major {STRIKE_PERIOD_S}s infinite;
      opacity: 0;
    }}
    .lightning.minor {{
      animation: strike-minor {STRIKE_PERIOD_S}s infinite;
      opacity: 0;
    }}
    .bolt-outer, .bolt-mid, .bolt-core {{
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .bolt-outer {{
      stroke: #8b0018;
      opacity: 0.55;
    }}
    .bolt-mid {{
      stroke: #ff1a28;
      opacity: 0.75;
    }}
    .bolt-core {{
      stroke: #fff5ee;
      opacity: 0.95;
    }}
    .trees {{
      fill: #050508;
      opacity: 0.92;
    }}
  </style>
  <defs>
    <linearGradient id="skyBase" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5a0818"/>
      <stop offset="45%" stop-color="#2a0610"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <radialGradient id="cloudRed" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff3048" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#ff3048" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="cloudBright" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff5868" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#ff5868" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="skyVignette" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.45"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="#0d1117"/>
{sky_svg()}
{bolts}
{treeline_svg()}
  <line x1="{x0}" y1="108" x2="{x1}" y2="108" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <line x1="{x0}" y1="328" x2="{x1}" y2="328" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <g opacity="0.55">{glow}</g>
  <g class="title">{main_title}</g>
</svg>
"""
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_SVG} ({len(svg.encode())} bytes)")


if __name__ == "__main__":
    main()
