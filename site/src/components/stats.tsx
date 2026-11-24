import type { ReactNode } from "react";
import { count, fontData, kb } from "@/lib/format";
import { Loupe } from "./loupe";

const { sans, mono } = fontData.families;

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      className="stat-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const STATS = [
  {
    label: "Weights",
    sans: sans.weights,
    mono: mono.weights,
    icon: (
      <Icon>
        <path d="M5 4v16M10 4v16M15 4v16M20 4v16" />
      </Icon>
    ),
  },
  {
    label: "Glyphs",
    sans: count(sans.glyphs),
    mono: count(mono.glyphs),
    icon: (
      <Icon>
        <rect x="3" y="3" width="18" height="18" />
        <path d="m8 16 4-9 4 9M9.5 13h5" />
      </Icon>
    ),
  },
  {
    label: "Characters",
    sans: count(sans.characters),
    mono: count(mono.characters),
    icon: (
      <Icon>
        <rect x="3" y="3" width="7" height="7" />
        <rect x="14" y="3" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" />
      </Icon>
    ),
  },
  {
    label: "Stylistic sets",
    sans: sans.stylisticSets,
    mono: mono.stylisticSets,
    icon: (
      <Icon>
        <path d="M4 7h10M4 12h16M4 17h7" />
        <circle cx="18" cy="7" r="2" />
        <circle cx="15" cy="17" r="2" />
      </Icon>
    ),
  },
  {
    label: "WOFF2 size",
    sans: kb(sans.files.woff2.bytes),
    mono: kb(mono.files.woff2.bytes),
    icon: (
      <Icon>
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <path d="M14 3v5h5" />
      </Icon>
    ),
  },
];

export function Stats() {
  return (
    <section className="stats" aria-label="The family in numbers">
      <dl className="stat-list">
        {STATS.map((stat) => (
          <div key={stat.label} className="stat">
            {stat.icon}
            <dt>{stat.label}</dt>
            <dd className="tnum">
              <span data-face-only="sans">{stat.sans}</span>
              <span data-face-only="mono">{stat.mono}</span>
            </dd>
          </div>
        ))}
      </dl>
      <Loupe
        glyphs={[
          { label: "Graft", font: "var(--sans)", metrics: sans.metrics },
          { label: "Graft Mono", font: "var(--mono)", metrics: mono.metrics },
        ]}
      />
    </section>
  );
}
