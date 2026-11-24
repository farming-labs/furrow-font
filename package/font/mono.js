import localFont from "next/font/local";

export const GraftMono = localFont({
  src: "../fonts/GraftMono-Variable.woff2",
  variable: "--font-graft-mono",
  weight: "100 900",
  adjustFontFallback: false,
  fallback: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
});
