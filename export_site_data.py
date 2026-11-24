#!/usr/bin/env python3
"""Copy the built fonts into the site and write the data its pages read.

Everything the site states about the fonts (glyph counts, file sizes, metrics,
outlines) comes from here, so the page never carries a hand-typed number.

Usage: python export_site_data.py   (after python build.py)
"""

from __future__ import annotations

import json
import shutil
import unicodedata
import zipfile
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

import build

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
PUBLIC_FONTS = SITE / "public" / "fonts"
DATA = SITE / "src" / "data" / "font-data.json"

FAMILIES = {
    "sans": {
        "built": "fonts/Graft[wght]",
        "public": "Graft-Variable",
        "family": "Graft",
    },
    "mono": {
        "built": "fonts/GraftMono[wght]",
        "public": "GraftMono-Variable",
        "family": "Graft Mono",
    },
}

# Control, format, separator and unassigned code points have nothing to show.
SKIP = {"Cc", "Cf", "Zs", "Zl", "Zp", "Co", "Cn"}

def svg_path(draw, flip_height):
    pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    draw(TransformPen(pen, (1, 0, 0, -1, 0, flip_height)))
    return pen.getCommands()


def outlines(out):
    """Paths and on/off-curve points for printable ASCII at weight 400, for the
    glyph inspector's outline view. Y runs down from the ascender."""
    gs = out.getGlyphSet(location={"wght": 400})
    ascent, descent = out["hhea"].ascent, -out["hhea"].descent
    cmap = out.getBestCmap()
    glyphs = {}
    for code in range(0x21, 0x7F):
        name = cmap.get(code)
        if not name:
            continue
        rec = DecomposingRecordingPen(gs)
        gs[name].draw(rec)
        points = []
        for op, args in rec.value:
            if op in ("moveTo", "lineTo"):
                points.append([*args[0], 1])
            elif op in ("qCurveTo", "curveTo"):
                points.extend([*pt, 0] for pt in args[:-1] if pt is not None)
                if args[-1] is not None:
                    points.append([*args[-1], 1])
        glyphs[chr(code)] = {
            "d": svg_path(rec.replay, ascent),
            "w": gs[name].width,
            "p": [[round(x), round(ascent - y), on] for x, y, on in points],
        }
    os2 = out["OS/2"]
    return {
        "ascent": ascent,
        "descent": descent,
        "capHeight": os2.sCapHeight,
        "xHeight": os2.sxHeight,
        "glyphs": glyphs,
    }


def write_favicon(font):
    """A Graft G on black, drawn from the real outline at weight 500."""
    gs = font.getGlyphSet(location={"wght": 500})
    name = build.glyph_name(font, "G")
    x0, y0, x1, y1 = build.glyph_bounds(gs, name)
    size, box = 512, 300
    k = box / (y1 - y0)
    dx = (size - (x1 - x0) * k) / 2 - x0 * k
    dy = (size + (y1 - y0) * k) / 2 + y0 * k
    pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    gs[name].draw(TransformPen(pen, (k, 0, 0, -k, dx, dy)))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<title>Graft</title><rect width="{size}" height="{size}" fill="#000"/>'
        f'<path d="{pen.getCommands()}" fill="#ededed"/></svg>\n'
    )
    (SITE / "public" / "favicon.svg").write_text(svg)


def main():
    PUBLIC_FONTS.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "OFL.txt", PUBLIC_FONTS / "OFL.txt")
    data = {"families": {}}
    for key, cfg in FAMILIES.items():
        files = {}
        for ext in ("woff2", "ttf"):
            src = ROOT / f"{cfg['built']}.{ext}"
            dest = PUBLIC_FONTS / f"{cfg['public']}.{ext}"
            shutil.copyfile(src, dest)
            files[ext] = {"url": f"/fonts/{dest.name}", "bytes": dest.stat().st_size}
        out = TTFont(ROOT / f"{cfg['built']}.ttf")
        cmap = out.getBestCmap()
        chars = []
        for code, name in sorted(cmap.items()):
            char = chr(code)
            if unicodedata.category(char) in SKIP:
                continue
            chars.append(
                {
                    "c": char,
                    "u": f"{code:04X}",
                    "n": unicodedata.name(char, name).title(),
                }
            )
        (axis,) = out["fvar"].axes
        data["families"][key] = {
            "family": cfg["family"],
            "glyphs": len(out.getGlyphOrder()),
            "characters": len(chars),
            "weight": [axis.minValue, axis.maxValue],
            "weights": len(out["fvar"].instances),
            "stylisticSets": len({r.FeatureTag for r in out["GSUB"].table.FeatureList.FeatureRecord if r.FeatureTag.startswith("ss")}),
            "metrics": {
                "upm": out["head"].unitsPerEm,
                "ascender": out["hhea"].ascent,
                "descender": out["hhea"].descent,
                "capHeight": out["OS/2"].sCapHeight,
                "xHeight": out["OS/2"].sxHeight,
                # How far a descender actually reaches, for the hero's metric lines.
                "descent": round(build.glyph_bounds(out.getGlyphSet(location={"wght": 400}), build.glyph_name(out, "p"))[1]),
            },
            "files": files,
            "chars": chars,
        }
        (SITE / "public" / f"outlines-{key}.json").write_text(json.dumps(outlines(out), separators=(",", ":")))
        print(f"{cfg['family']}: {len(chars)} characters, files {files}")
    write_favicon(TTFont(ROOT / f"{FAMILIES['sans']['built']}.ttf"))
    archive = PUBLIC_FONTS / "Graft.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for cfg in FAMILIES.values():
            for ext in ("woff2", "ttf"):
                zf.write(PUBLIC_FONTS / f"{cfg['public']}.{ext}", f"Graft/{cfg['public']}.{ext}")
        zf.write(PUBLIC_FONTS / "OFL.txt", "Graft/OFL.txt")
    data["zip"] = {"url": f"/fonts/{archive.name}", "bytes": archive.stat().st_size}
    DATA.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {DATA.relative_to(ROOT)} ({DATA.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
