import data from "@/data/font-data.json";

export type FamilyKey = "sans" | "mono";
export type FontData = typeof data;
export type Glyph = FontData["families"]["sans"]["chars"][number];

export const fontData = data;

/** Kilobytes in base 1000, the unit file browsers show. */
export function kb(bytes: number): string {
  return `${(bytes / 1000).toFixed(1)} KB`;
}

export function count(value: number): string {
  return value.toLocaleString("en-US");
}
