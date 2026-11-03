#!/usr/bin/env python3
"""Build Stranger Things-style READ OUT banner (GitHub-safe SVG)."""

from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent
FONT_PATH = Path("/tmp/fonts/CormorantGaramond.ttf")
OUT_SVG = ROOT / "readout.svg"


def fetch_contributions() -> int:
    try:
        out = subprocess.check_output(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                'query=query { user(login: "AndrewPrakash1") { contributionsCollection { contributionCalendar { totalContributions } } } }',
            ],
            text=True,
        )
        data = json.loads(out)
        return int(
            data["data"]["user"]["contributionsCollection"]["contributionCalendar"][
                "totalContributions"
            ]
        )
    except (subprocess.CalledProcessError, KeyError, TypeError, ValueError):
        return 121


def load_font():
    if not FONT_PATH.is_file():
        raise SystemExit(f"Font missing: {FONT_PATH}")
    src = TTFont(FONT_PATH)
    font = instantiateVariableFont(src, {"wght": 700}, inplace=False)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]
    return font, upem, cmap, gs, hmtx


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


def main() -> None:
    contrib = fetch_contributions()
    _, upem, cmap, gs, hmtx = load_font()

    w, h = 1200, 420
    cx = w / 2

    def t(
        text: str,
        baseline: float,
        size: float,
        fill: str,
        stroke: str | None = None,
        sw: float = 0,
        extra: str = "",
        tracking: int = 70,
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

    read = t("READ", 168, 118, "#ff3a4a", "#ff6b78", 2.2)
    out = t("OUT", 292, 118, "#ff3a4a", "#ff6b78", 2.2)
    read_glow = t("READ", 168, 118, "#ff3a4a", extra='opacity="0.45"')
    out_glow = t("OUT", 292, 118, "#ff3a4a", extra='opacity="0.45"')
    read_cyan = t("READ", 168, 118, "#5dfff2", extra='class="ghost-a"')
    read_hot = t("READ", 168, 118, "#ff1744", extra='class="ghost-b"')
    out_cyan = t("OUT", 292, 118, "#5dfff2", extra='class="ghost-a"')
    out_hot = t("OUT", 292, 118, "#ff1744", extra='class="ghost-b"')
    num = t(str(contrib), 248, 280, "#ff2a3c", extra='opacity="0.14"')

    footer_label = (
        f'<text x="{cx}" y="382" fill="#a88490" font-family="Courier New, Courier, monospace" '
        f'font-size="14" letter-spacing="2" text-anchor="middle">'
        f"GITHUB CONTRIBUTIONS {contrib}</text>"
    )

    rule_w = 520
    x0 = cx - rule_w / 2
    x1 = cx + rule_w / 2

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="READ OUT, {contrib} GitHub contributions">
  <title>READ OUT</title>
  <desc>Neon title card. GitHub contributions: {contrib}.</desc>
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
    @keyframes drift {{
      0%, 100% {{ opacity: 0.12; }}
      50% {{ opacity: 0.17; }}
    }}
    .ghost-a, .ghost-b {{
      transform-box: fill-box;
      transform-origin: center;
    }}
    .ghost-a {{ animation: glitch-a 4.5s infinite; }}
    .ghost-b {{ animation: glitch-b 4.5s infinite 0.08s; }}
    .title {{ animation: flicker 8s infinite; }}
    .bgnum {{ animation: drift 6s ease-in-out infinite; }}
  </style>
  <defs>
    <radialGradient id="mist" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#3a0814" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="#0d1117"/>
  <rect width="{w}" height="{h}" fill="url(#mist)"/>
  <g class="bgnum">{num}</g>
  <line x1="{x0}" y1="98" x2="{x1}" y2="98" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <line x1="{x0}" y1="338" x2="{x1}" y2="338" stroke="#ff4a5a" stroke-width="2.5" opacity="0.9"/>
  <g class="ghost-a">{read_cyan}{out_cyan}</g>
  <g class="ghost-b">{read_hot}{out_hot}</g>
  <g opacity="0.55">{read_glow}{out_glow}</g>
  <g class="title">{read}{out}</g>
  {footer_label}
</svg>
"""
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_SVG} ({len(svg.encode())} bytes), contributions={contrib}")


if __name__ == "__main__":
    main()
