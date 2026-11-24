# Graft

**A sans and mono family blended from two typefaces each: Geist and Public Sans for the sans, Geist Mono and JetBrains Mono for the mono. The sans is 55% Public Sans and 45% Geist; the mono leans the other way, 55% Geist Mono and 45% JetBrains Mono.**

Every letter the two fonts share is interpolated. Proportions, x-height, curves and terminals land 55% of the way toward Public Sans for the sans, and 45% of the way toward JetBrains Mono for the mono, so both stay close to Geist and pick up the second font's proportions and curves. Both families are single variable fonts with weights from 100 to 900, and the weights match Geist's: `font-weight: 600` in Graft is as heavy as it is in Geist.

The name comes from gardening: a graft joins two plants so they grow as one.

## What it does not do

- It does not blend letters whose two designs are built differently. Geist's `J` has a tall hook and Public Sans's a short one, and averaging them gives a lump. In the sans those letters take the second font's drawing whole, weight-matched to Geist's stems. The mono's `mix` is below 0.5, so its unmatched letters keep Geist Mono's. The build lists every one and why.
- It does not redraw kerning or mark anchors. Spacing between pairs and OpenType features come from Geist. Precomposed accents (`á`, `ç`) are repositioned over the blended letter. Combining marks typed after a letter use Geist's anchors.
- It is not hand-finished. A type designer would still review curves at large sizes and redraw the kept letters to match.

## Where it stands

| | Graft | Graft Mono |
|---|---|---|
| Glyphs blended, taken from the second font, or rebuilt from those parts | 623 | 718 |
| Glyphs kept from Geist | 352 | 441 |
| Letters and figures drawn whole by the second font | `J Q f g` | none |
| Letters and figures kept whole from Geist | none | `G J Q Y l r u 3 4 6 7 8 9` |

The mono keeps Geist Mono's slashed `0` by choice (`keep` in `build.py`).

Tabular, fraction, superscript and subscript figures (`tnum`, `frac`, `sups`, `subs`) are blended too, and tabular figures share one width at every weight.

Most kept glyphs are symbols, box-drawing and stylistic alternates that the second font does not draw.

## How the build works

`python build.py` does this for each family:

1. **Weight-matches the second font.** At each of Geist's masters (100, 400, 801 and 900 for the sans; 100, 400 and 900 for the mono), it measures the `n` and `H` stems in both fonts and finds the second font's weight with the same stems. Past the end of the second font's weight range, it offsets the outline to close the gap.
2. **Makes the outlines compatible.** Two fonts never share point structure, so for each letter `blend.py` pairs contours, finds matching start points, aligns corners, and splits both outlines until every piece has a partner. When that fails and a letter is drawn with overlapping strokes (Geist draws `f` as a stem plus a crossbar, and Geist Mono's `A` as legs plus a bar), the strokes are unioned into one shape and matched again. The union is worked out once at the default weight and rebuilt from the same points at every other weight, with the crossings solved again, so the letter still interpolates along the weight axis.
3. **Interpolates.** Each piece is drawn at the `mix` ratio (0.55 for the sans, 0.45 for the mono) at every master, so the blend still varies with weight.
4. **Rejects bad blends.** A blend that crosses itself, or whose ink area strays more than 3% from the sources' area mixed at the same ratio, means the letters differ in structure. That letter takes the drawing of the font the mix leans toward.
5. **Assembles the family.** It repositions accents on composites, rebuilds the variable font with `fontTools.varLib`, renames everything and writes `.ttf` and `.woff2`.

## Build

```sh
python3 -m venv .venv
.venv/bin/pip install fonttools brotli skia-pathops opentype-sanitizer
.venv/bin/python build.py          # or: build.py sans / build.py mono
.venv/bin/python verify.py
.venv/bin/python -m ots "fonts/Graft[wght].woff2"
```

`verify.py` checks that the blended `n` and `H` stems match Geist's within 3 units at nine weights from 100 to 900, that kept glyphs are still Geist's, and that no character lost its mapping.

Open `specimen.html` in a browser to see the result.

## Site

`site/` is the showcase, a Farm.js app with a dark layout: a Sans/Mono switch for the whole page, a wordmark with measured metric lines, a magnified specimen, a glyph inspector with solid and outline (anchor point) views, specimen posters, a type tester, weights, a figure built from the real outlines, OpenType number features, and install instructions.

```sh
.venv/bin/python export_site_data.py   # copy fonts into site/public, write site/src/data/font-data.json
cd site && pnpm install
pnpm dev                               # or: pnpm build && pnpm start
```

Every number on the site (glyph counts, file sizes, metrics, advances in the figure) and the outline data in `site/public/outlines-*.json` come from `export_site_data.py`, so rerun it after every font build.

To see the fonts on a real site, `node scripts/farmjs-preview.mjs` serves farmjs.dev at http://localhost:4318 with Graft in place of Geist. It reads the fonts from `site/public/fonts` on every request, so reload after `export_site_data.py`.

## Use

```sh
npm install @farming-labs/graft
```

```tsx
// Next.js, the same shape as the geist package
import { GraftSans } from "@farming-labs/graft/font/sans";
import { GraftMono } from "@farming-labs/graft/font/mono";
```

The package also works with Farm.js `localFont` (`src: "@farming-labs/graft/fonts/Graft-Variable.woff2"`) and with any bundler through `@farming-labs/graft/graft.css`. See [`package/README.md`](package/README.md). Without npm, download the files from [graft.farming-labs.dev](https://graft.farming-labs.dev) and declare them yourself:

```css
@font-face {
  font-family: "Graft";
  src: url("/fonts/Graft-Variable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}
@font-face {
  font-family: "Graft Mono";
  src: url("/fonts/GraftMono-Variable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}
```

## Package

`package/` is `@farming-labs/graft`. Its `prepack` step copies the built fonts and `OFL.txt` into it, so build the fonts first, then `npm pack` or publish from `package/`.

## Change the look

Set `mix` in `FAMILIES` in `build.py`: `0` is pure Geist, `1` is pure Public Sans (or JetBrains Mono), and `0.3` leans toward Geist. Above 0.5, letters that can't be blended take the second font's drawing; at or below, Geist's. List glyph names in `keep` to hold Geist's drawing whatever the mix. Rebuild and run `verify.py`.

## License

SIL Open Font License 1.1. See `OFL.txt`. Graft is a derivative of Geist (Copyright 2024 The Geist Project Authors), Public Sans (Copyright 2015 The Public Sans Project Authors) and JetBrains Mono (Copyright 2020 The JetBrains Mono Project Authors). None of them declares a Reserved Font Name. Graft does not use their names, as the license expects of modified versions.
