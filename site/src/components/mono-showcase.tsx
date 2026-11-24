import { CodePanel } from "./code-panel";

const CODE = `import { defineConfig } from "@farm.js/core";

export default defineConfig({
  deploy: { target: "vercel" },
  theme: { default: "dark" },
});

// 0O Il1| {} [] () => !== <=
const total = items.reduce((sum, item) => sum + item.price, 0);`;

const MONO_LINE = 'const graft = { sans: "Graft", mono: "Graft Mono" };';

export function MonoShowcase() {
  return (
    <div className="mono-showcase">
      <div className="mono-pairs mono" aria-label="Characters that are easy to confuse">
        <span>0O</span>
        <span>Il1|</span>
        <span>{"{}"}</span>
        <span>[]</span>
        <span>()</span>
        <span>;:</span>
      </div>
      <CodePanel label="farm.config.ts" language="ts" code={CODE} />
      <div className="mono-weights rows">
        {[200, 400, 600, 800].map((weight) => (
          <p key={weight} className="mono" style={{ fontWeight: weight }}>
            <span className="tag tnum">{weight}</span> {MONO_LINE}
          </p>
        ))}
      </div>
    </div>
  );
}
