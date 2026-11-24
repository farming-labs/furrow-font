# @farming-labs/graft

**Graft and Graft Mono as an npm package: variable fonts from 100 to 900, for Next.js, Farm.js or plain CSS.**

`font-weight: 600` is as heavy in Graft Mono as it is in Graft, so interface text and code match. Specimen and downloads: [graft.farming-labs.dev](https://graft.farming-labs.dev).

```sh
npm install @farming-labs/graft
```

## Next.js

Each export is a `next/font/local` font with a CSS variable.

```tsx
// app/layout.tsx
import { GraftSans } from "@farming-labs/graft/font/sans";
import { GraftMono } from "@farming-labs/graft/font/mono";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GraftSans.variable} ${GraftMono.variable}`}>
      <body className={GraftSans.className}>{children}</body>
    </html>
  );
}
```

Then use `var(--font-graft-sans)` and `var(--font-graft-mono)`, or in Tailwind v4:

```css
@theme inline {
  --font-sans: var(--font-graft-sans);
  --font-mono: var(--font-graft-mono);
}
```

## Farm.js

`localFont` reads the files straight from the package and fingerprints them.

```tsx
// src/app/layout.tsx
import { localFont } from "@farm.js/core/font";

const graft = localFont({
  src: "@farming-labs/graft/fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft-sans",
});

const graftMono = localFont({
  src: "@farming-labs/graft/fonts/GraftMono-Variable.woff2",
  family: "Graft Mono",
  weight: "100 900",
  variable: "--font-graft-mono",
});
```

## CSS

Any bundler that resolves `url()` in CSS (Vite, webpack, Parcel) can import the stylesheets. Each one declares the font and a CSS variable.

```ts
import "@farming-labs/graft/graft.css"; // both
import "@farming-labs/graft/sans.css"; // Graft only
import "@farming-labs/graft/mono.css"; // Graft Mono only
```

```css
body {
  font-family: var(--font-graft-sans);
}
code {
  font-family: var(--font-graft-mono);
}
```

## Files

| Path | What it is |
| --- | --- |
| `fonts/Graft-Variable.woff2` | Graft, web |
| `fonts/Graft-Variable.ttf` | Graft, desktop |
| `fonts/GraftMono-Variable.woff2` | Graft Mono, web |
| `fonts/GraftMono-Variable.ttf` | Graft Mono, desktop |

## What it does not do

- It ships one variable file per family, not one file per weight.
- It has no italics yet.

## License

SIL Open Font License 1.1. `OFL.txt` carries the license and the copyright notices it requires. Source: the [repository](https://github.com/farming-labs/graft-font).
