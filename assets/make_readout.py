#!/usr/bin/env python3
"""Build Stranger Things-style profile banner SVG."""

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

    ghost_cyan = (
        layer(LINE1, 178, size1, cx, upem, cmap, gs, hmtx, track1, "#5dfff2", extra='class="ghost-a"')
        + layer(LINE2, 288, size2, cx, upem, cmap, gs, hmtx, track2, "#5dfff2", extra='class="ghost-a"')
    )
    ghost_hot = (
        layer(LINE1, 178, size1, cx, upem, cmap, gs, hmtx, track1, "#ff1744", extra='class="ghost-b"')
        + layer(LINE2, 288, size2, cx, upem, cmap, gs, hmtx, track2, "#ff1744", extra='class="ghost-b"')
    )

    _, w1 = emit(LINE1, cx, 178, size1, "#ff3a4a", upem, cmap, gs, hmtx, tracking=track1)
    _, w2 = emit(LINE2, cx, 288, size2, "#ff3a4a", upem, cmap, gs, hmtx, tracking=track2)
    rule_w = min(max(w1, w2) + 80, w - 80)
    x0 = cx - rule_w / 2
    x1 = cx + rule_w / 2

    aria = f"{LINE1} {LINE2.strip()}"

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{aria}">
  <title>{LINE1}</title>
  <desc>Neon quote banner: {aria}</desc>
  <style>
    @keyframes glitch-a {{
      0%, 83%, 100% {{ opacity: 0; transform: translate(0, 0); }}
      84% {{ opacity: 0.7; transform: translate(-12px, 0); }}
      86% {{ opacity: 0.45; transform: translate(10px, 1px); }}
      88% {{ opacity: 0.6; transform: translate(-5px, 0); }}
    }}
    @keyframes glitch-b {{
      0%, 83%, 100% {{ opacity: 0; transform: translate(0, 0); }}
      84% {{ opacity: 0.55; transform: translate(11px, -1px); }}
      86% {{ opacity: 0.35; transform: translate(-9px, 0); }}
      88% {{ opacity: 0.5; transform: translate(4px, 1px); }}
    }}
    @keyframes flicker {{
      0%, 92%, 100% {{ opacity: 1; }}
      93% {{ opacity: 0.72; }}
      94% {{ opacity: 0.95; }}
    }}
    .ghost-a, .ghost-b {{
      transform-box: fill-box;
      transform-origin: center;
    }}
    .ghost-a {{ animation: glitch-a 4.5s infinite; }}
    .ghost-b {{ animation: glitch-b 4.5s infinite 0.08s; }}
    .title {{ animation: flicker 8s infinite; }}
  </style>
  <defs>
    <radialGradient id="mist" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#3a0814" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="#0d1117"/>
  <rect width="{w}" height="{h}" fill="url(#mist)"/>
  <line x1="{x0}" y1="108" x2="{x1}" y2="108" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <line x1="{x0}" y1="328" x2="{x1}" y2="328" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <g class="ghost-a">{ghost_cyan}</g>
  <g class="ghost-b">{ghost_hot}</g>
  <g opacity="0.55">{glow}</g>
  <g class="title">{main_title}</g>
</svg>
"""
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_SVG} ({len(svg.encode())} bytes)")


if __name__ == "__main__":
    main()
