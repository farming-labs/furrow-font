import { localFont } from "@farm.js/core/font";

export const GraftSans = localFont({
  src: "../fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft-sans",
  fallback: ["ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
});
