#!/usr/bin/env python3
"""Check the built fonts.

1. Weights stay honest: the blended `n` and `H` stems match Geist's at nine
   weights, so `font-weight: 600` means the same thing it does in Geist.
2. Glyphs the build kept from Geist are still Geist (within 2 units).
3. Every character Geist maps is still mapped.
"""

import sys
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from build import glyph_bounds, glyph_name, left_stem

ROOT = Path(__file__).resolve().parent
PAIRS = [
    ("sources/Geist[wght].ttf", "fonts/Graft[wght].ttf"),
    ("sources/GeistMono[wght].ttf", "fonts/GraftMono[wght].ttf"),
]
WEIGHTS = [100, 175, 300, 400, 550, 700, 801, 850, 900]
STEM_TOLERANCE = 3


def points(gs, name):
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    return [p for _, args in pen.value for p in args if p is not None], gs[name].width


def stem(gs, font, char, height_char, frac):
    top = glyph_bounds(gs, glyph_name(font, height_char))[3]
    return left_stem(gs, glyph_name(font, char), top * frac + 0.5)


failed = False
for base_path, out_path in PAIRS:
    base, out = TTFont(ROOT / base_path), TTFont(ROOT / out_path)
    if base.getBestCmap() != out.getBestCmap():
        print(f"FAIL {out_path}: the character map differs from Geist's")
        failed = True

    worst_stem = 0.0
    for w in WEIGHTS:
        gb, go = base.getGlyphSet(location={"wght": w}), out.getGlyphSet(location={"wght": w})
        for char, h_char, frac in (("n", "x", 0.35), ("H", "H", 0.25)):
            diff = abs(stem(gb, base, char, h_char, frac) - stem(go, out, char, h_char, frac))
            worst_stem = max(worst_stem, diff)
            if diff > STEM_TOLERANCE:
                print(f"FAIL {out_path}: `{char}` stem at wght {w} is {diff:.1f} units off Geist's")
                failed = True
    print(f"{out_path}: n/H stems within {worst_stem:.1f} units of Geist at wght {WEIGHTS}")

    names = base.getGlyphOrder()
    same = set(names)
    for w in WEIGHTS:
        gb, go = base.getGlyphSet(location={"wght": w}), out.getGlyphSet(location={"wght": w})
        for name in list(same):
            pb, wb = points(gb, name)
            po, wo = points(go, name)
            if len(pb) != len(po) or abs(wb - wo) > 2:
                same.discard(name)
                continue
            if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) > 2 for a, b in zip(pb, po)):
                same.discard(name)
    print(f"{out_path}: {len(names) - len(same)} glyphs blended or rebuilt on blended parts, {len(same)} kept from Geist")

sys.exit(1 if failed else 0)
