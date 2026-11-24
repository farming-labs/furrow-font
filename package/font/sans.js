import localFont from "next/font/local";

export const GraftSans = localFont({
  src: "../fonts/Graft-Variable.woff2",
  variable: "--font-graft-sans",
  weight: "100 900",
  fallback: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
});
