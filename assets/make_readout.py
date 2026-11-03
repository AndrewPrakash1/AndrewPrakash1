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

# Jagged bolt polylines: list of (x,y) points from top toward bottom
BOLTS: list[tuple[str, list[tuple[float, float]], float]] = [
    (
        "bolt-a",
        [
            (180, 0),
            (198, 62),
            (172, 78),
            (205, 145),
            (188, 158),
            (215, 230),
            (192, 248),
            (220, 320),
            (200, 335),
            (228, 420),
        ],
        0.0,
    ),
    (
        "bolt-b",
        [
            (1020, 20),
            (1002, 95),
            (1030, 110),
            (998, 190),
            (1025, 205),
            (1005, 280),
            (1035, 295),
            (1010, 360),
            (1040, 380),
            (1015, 420),
        ],
        1.7,
    ),
    (
        "bolt-c",
        [
            (320, 40),
            (338, 120),
            (312, 132),
            (345, 210),
            (328, 225),
            (352, 300),
        ],
        3.4,
    ),
    (
        "bolt-d",
        [
            (880, 55),
            (862, 130),
            (890, 145),
            (868, 220),
            (895, 240),
            (875, 310),
        ],
        2.2,
    ),
    (
        "bolt-e",
        [
            (560, 0),
            (548, 70),
            (572, 85),
            (545, 160),
            (568, 175),
            (550, 250),
            (575, 265),
            (552, 340),
        ],
        4.8,
    ),
    (
        "bolt-f",
        [
            (680, 0),
            (698, 88),
            (672, 102),
            (705, 185),
            (688, 198),
            (710, 275),
        ],
        5.5,
    ),
]


def points_to_path(pts: list[tuple[float, float]]) -> str:
    if not pts:
        return ""
    parts = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L {x:.1f} {y:.1f}")
    return " ".join(parts)


def lightning_svg() -> str:
    chunks: list[str] = []
    for bolt_id, pts, delay in BOLTS:
        d = points_to_path(pts)
        chunks.append(
            f'  <g class="lightning {bolt_id}" style="animation-delay:{delay}s">'
            f'<path d="{d}" class="bolt-glow"/>'
            f'<path d="{d}" class="bolt-core"/>'
            f"</g>"
        )
    return "\n".join(chunks)


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
      0%, 90%, 100% {{ opacity: 1; }}
      91% {{ opacity: 0.78; }}
      92% {{ opacity: 0.95; }}
      93% {{ opacity: 0.65; }}
      94% {{ opacity: 1; }}
    }}
    @keyframes strike {{
      0%, 88%, 100% {{ opacity: 0; }}
      89% {{ opacity: 0.15; }}
      89.5% {{ opacity: 0.95; }}
      90% {{ opacity: 0.25; }}
      90.5% {{ opacity: 0.85; }}
      91% {{ opacity: 0; }}
      96% {{ opacity: 0; }}
      96.3% {{ opacity: 0.7; }}
      96.6% {{ opacity: 0; }}
    }}
    @keyframes strike-dim {{
      0%, 100% {{ opacity: 0.08; }}
      50% {{ opacity: 0.14; }}
    }}
    .title {{ animation: neon-flicker 6s infinite; }}
    .lightning {{
      animation: strike 7s infinite;
      opacity: 0;
    }}
    .bolt-core {{
      fill: none;
      stroke: #ff5060;
      stroke-width: 2.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .bolt-glow {{
      fill: none;
      stroke: #ff1a30;
      stroke-width: 7;
      stroke-linecap: round;
      stroke-linejoin: round;
      opacity: 0.35;
    }}
    .lightning.bolt-e, .lightning.bolt-f {{
      animation: strike 9s infinite;
    }}
    .ambient-bolt {{
      animation: strike-dim 4s ease-in-out infinite;
    }}
  </style>
  <defs>
    <radialGradient id="mist" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#4a0a18" stop-opacity="0.65"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="#0d1117"/>
  <rect width="{w}" height="{h}" fill="url(#mist)"/>
  <g class="ambient-bolt" opacity="0.12">
    <path d="M 450 0 L 465 180 L 440 195 L 470 420" fill="none" stroke="#ff3040" stroke-width="1.5"/>
    <path d="M 750 0 L 735 200 L 760 215 L 730 420" fill="none" stroke="#ff3040" stroke-width="1.5"/>
  </g>
{bolts}
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
