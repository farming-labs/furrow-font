# Graft

**A sans and a mono for interfaces and code. Both are variable from 100 to 900, share one set of vertical metrics, and are free under the SIL Open Font License.**

`font-weight: 600` is as heavy in Graft Mono as it is in Graft, so interface text and code sit together without a seam. Specimen and downloads: [graft.farming-labs.dev](https://graft.farming-labs.dev).

## The family

| | Graft | Graft Mono |
|---|---|---|
| Weights | 100 to 900, one variable file | 100 to 900, one variable file |
| Characters | 723 | 884 |
| Glyphs | 975 | 1,159 |
| WOFF2 size | 99 KB | 86 KB |

- **Figures.** Tabular, fraction, superscript and subscript figures (`tnum`, `frac`, `sups`, `subs`), drawn to match the default digits. Tabular figures keep one width at every weight.
- **Code.** Graft Mono has a slashed zero, and `0O`, `Il1|` and every bracket pair are drawn to stay distinct at small sizes.
- **Formats.** WOFF2 for the web and TTF for desktop apps.

## What it does not do

- It has no italics yet.
- It ships one variable file per family, not one file per weight.
- It is not hand-finished. Curves at very large sizes still need a type designer's review.

## Use

```sh
npm install @farming-labs/graft
```

Next.js: each export is a `next/font/local` font with a CSS variable.

```tsx
import { GraftSans } from "@farming-labs/graft/font/sans";
import { GraftMono } from "@farming-labs/graft/font/mono";
```

Farm.js: load the published files with `remoteFont`, which downloads them during the build and serves them from your app, or point `localFont` at the package.

```tsx
import { remoteFont } from "@farm.js/core/font";

const graft = remoteFont({
  src: "https://graft.farming-labs.dev/fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft-sans",
});
```

Any bundler: `import "@farming-labs/graft/graft.css"`. See [`package/README.md`](package/README.md) for every entry point. Without npm, download the files from [graft.farming-labs.dev](https://graft.farming-labs.dev) and declare them yourself:

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

## Build

```sh
python3 -m venv .venv
.venv/bin/pip install fonttools brotli skia-pathops opentype-sanitizer
.venv/bin/python build.py          # or: build.py sans / build.py mono
.venv/bin/python verify.py         # stem weights and character mappings
.venv/bin/python -m ots "fonts/Graft[wght].woff2"
```

The fonts land in `fonts/`. Open `specimen.html` in a browser to see them.

## Site

`site/` is the specimen site at [graft.farming-labs.dev](https://graft.farming-labs.dev), a Farm.js app.

```sh
.venv/bin/python export_site_data.py   # copy fonts into site/public, write site/src/data/font-data.json
cd site && pnpm install
pnpm dev                               # or: pnpm build && pnpm start
```

Every number on the site and the outline data in `site/public/outlines-*.json` come from `export_site_data.py`, so rerun it after every font build. Pushing to `main` deploys the site.

`node scripts/farmjs-preview.mjs` serves farmjs.dev at http://localhost:4318 set in Graft, to see the fonts on a real site. It reads `site/public/fonts` on every request.

## Package

`package/` is `@farming-labs/graft`. Its `prepack` step copies the built fonts and `OFL.txt` into it, so build the fonts first, then `npm pack` or publish from `package/`.

## License

SIL Open Font License 1.1. `OFL.txt` carries the license and the copyright notices it requires.
