import type { LayoutProps, Metadata } from "@farm.js/core";
import { defineLayoutFonts, localFont } from "@farm.js/core/font";
import "./globals.css";

const graft = localFont({
  src: "/fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft",
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
});

const graftMono = localFont({
  src: "/fonts/GraftMono-Variable.woff2",
  family: "Graft Mono",
  weight: "100 900",
  variable: "--font-graft-mono",
  fallback: ["ui-monospace", "SFMono-Regular", "monospace"],
});

export const fonts = defineLayoutFonts({
  body: graft,
  code: graftMono,
});

export const metadata: Metadata = {
  metadataBase: new URL("https://graft.farming-labs.dev"),
  title: "Graft",
  description:
    "Graft is an open-source sans and mono for interfaces and code. Variable weights 100 to 900, free under the SIL Open Font License.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml", sizes: "any" }],
  },
};

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang="en" className={`${graft.variable} ${graftMono.variable}`}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#000000" />
        {/* Both faces render above the fold. Farm 0.1.81 emits no preload hint for public-dir fonts, so declare them here. */}
        <link
          rel="preload"
          href="/fonts/Graft-Variable.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/GraftMono-Variable.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
      </head>
      <body className={graft.className}>{children}</body>
    </html>
  );
}
