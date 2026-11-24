import { localFont } from "@farm.js/core/font";

export const GraftMono = localFont({
  src: "../fonts/GraftMono-Variable.woff2",
  family: "Graft Mono",
  weight: "100 900",
  variable: "--font-graft-mono",
  fallback: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
});
