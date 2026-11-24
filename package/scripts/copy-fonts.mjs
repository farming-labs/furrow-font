// Copies the built fonts and the license into the package before `npm pack`
// or `npm publish`, so the repository keeps one copy of each font file.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";

const root = new URL("../../", import.meta.url);
const pkg = new URL("../", import.meta.url);
const files = [
  ["fonts/Graft[wght].woff2", "fonts/Graft-Variable.woff2"],
  ["fonts/Graft[wght].ttf", "fonts/Graft-Variable.ttf"],
  ["fonts/GraftMono[wght].woff2", "fonts/GraftMono-Variable.woff2"],
  ["fonts/GraftMono[wght].ttf", "fonts/GraftMono-Variable.ttf"],
  ["OFL.txt", "OFL.txt"],
];

const missing = files.filter(([from]) => !existsSync(new URL(from, root))).map(([from]) => from);
if (missing.length > 0) {
  throw new Error(
    `Missing ${missing.join(", ")}. Run \`python build.py\` at the repository root before packing.`,
  );
}
mkdirSync(new URL("fonts/", pkg), { recursive: true });
for (const [from, to] of files) copyFileSync(new URL(from, root), new URL(to, pkg));
console.log(`Copied ${files.length} files into the package.`);
