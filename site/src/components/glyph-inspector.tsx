"use client";

import { useEffect, useMemo, useState } from "react";
import { FACE_FONT, type Face, useFace } from "@/lib/family";

type Glyph = { c: string; u: string; n: string };
type Metrics = { upm: number; capHeight: number; xHeight: number; descent: number };
type Family = { chars: Glyph[]; metrics: Metrics };
type OutlineGlyph = { d: string; w: number; p: Array<[number, number, number]> };
type Outlines = { ascent: number; glyphs: Record<string, OutlineGlyph> };

const FILTERS = [
  { key: "all", label: "All" },
  { key: "letters", label: "Letters" },
  { key: "figures", label: "Figures" },
  { key: "symbols", label: "Symbols" },
] as const;
type FilterKey = (typeof FILTERS)[number]["key"];

const VIEW_W = 1400;
const VIEW_H = 1300;
const BASELINE = 950;

function matches(glyph: Glyph, filter: FilterKey) {
  switch (filter) {
    case "letters":
      return /\p{L}/u.test(glyph.c);
    case "figures":
      return /\p{N}/u.test(glyph.c);
    case "symbols":
      return !/[\p{L}\p{N}]/u.test(glyph.c);
    default:
      return true;
  }
}

function category(char: string) {
  if (/\p{L}/u.test(char)) return "Letter";
  if (/\p{N}/u.test(char)) return "Figure";
  return "Symbol";
}

// Outline data is fetched once per family, and only when Points is chosen.
const outlineCache = new Map<Face, Promise<Outlines>>();
function loadOutlines(face: Face) {
  let promise = outlineCache.get(face);
  if (!promise) {
    promise = fetch(`/outlines-${face}.json`).then((response) => {
      if (!response.ok) throw new Error(`Outline data failed to load (${response.status}).`);
      return response.json() as Promise<Outlines>;
    });
    promise.catch(() => outlineCache.delete(face));
    outlineCache.set(face, promise);
  }
  return promise;
}

function OutlineView({ glyph, outlines }: { glyph: OutlineGlyph; outlines: Outlines }) {
  const dx = (VIEW_W - glyph.w) / 2;
  const dy = BASELINE - outlines.ascent;
  // Handles join each off-curve point to its on-curve neighbours.
  const handles: Array<[number, number, number, number]> = [];
  glyph.p.forEach((point, index) => {
    const next = glyph.p[index + 1];
    if (next && (point[2] === 0 || next[2] === 0))
      handles.push([point[0], point[1], next[0], next[1]]);
  });
  return (
    <g transform={`translate(${dx} ${dy})`}>
      <path d={glyph.d} className="gi-outline" />
      {handles.map(([x1, y1, x2, y2], index) => (
        <line key={index} x1={x1} y1={y1} x2={x2} y2={y2} className="gi-handle" />
      ))}
      {glyph.p.map(([x, y, on], index) =>
        on ? (
          <rect key={index} x={x - 9} y={y - 9} width="18" height="18" className="gi-node" />
        ) : (
          <circle key={index} cx={x} cy={y} r="8" className="gi-control" />
        ),
      )}
    </g>
  );
}

export function GlyphInspector({ families }: { families: Record<Face, Family> }) {
  const face = useFace();
  const family = families[face];
  const [filter, setFilter] = useState<FilterKey>("all");
  const [mode, setMode] = useState<"solid" | "outline">("solid");
  const [outlines, setOutlines] = useState<Partial<Record<Face, Outlines>>>({});
  const [failed, setFailed] = useState(false);
  const visible = useMemo(
    () => family.chars.filter((glyph) => matches(glyph, filter)),
    [family, filter],
  );
  const [selected, setSelected] = useState<string>("a");
  const current = visible.find((glyph) => glyph.c === selected) ?? visible[0];
  const m = family.metrics;
  const lines = [
    { key: "cap", label: "Cap height", value: m.capHeight },
    { key: "x", label: "x-height", value: m.xHeight },
    { key: "base", label: "Baseline", value: 0 },
    { key: "desc", label: "Descender", value: m.descent },
  ];

  useEffect(() => {
    if (mode !== "outline" || outlines[face]) return;
    let live = true;
    setFailed(false);
    loadOutlines(face).then(
      (data) => live && setOutlines((all) => ({ ...all, [face]: data })),
      () => live && setFailed(true),
    );
    return () => {
      live = false;
    };
  }, [mode, face, outlines]);

  const outlineGlyph = current ? outlines[face]?.glyphs[current.c] : undefined;
  const showOutline = mode === "outline" && outlineGlyph && outlines[face];

  return (
    <div className="gi">
      <div className="gi-preview">
        <div className="gi-tabs" role="group" aria-label="Preview style">
          <button type="button" aria-pressed={mode === "solid"} onClick={() => setMode("solid")}>
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <rect x="2.5" y="2.5" width="11" height="11" />
              <path d="M2.5 9.5 9.5 2.5M2.5 13.5l11-11M6.5 13.5l7-7" />
            </svg>
            Filled
          </button>
          <button
            type="button"
            aria-pressed={mode === "outline"}
            onClick={() => setMode("outline")}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M3 13C3 7 7 3 13 3" />
              <rect x="1.5" y="11.5" width="3" height="3" />
              <rect x="11.5" y="1.5" width="3" height="3" />
              <circle cx="3" cy="5" r="1.2" />
            </svg>
            Points
          </button>
        </div>
        <div className="gi-canvas">
          {lines.map((line) => (
            <div
              key={line.key}
              className="gi-line"
              style={{ top: `${((BASELINE - line.value) / VIEW_H) * 100}%` }}
              aria-hidden="true"
            >
              <span className="gi-line-name">{line.label}</span>
              <span className="metric-value tnum">{line.value}</span>
            </div>
          ))}
          {current ? (
            <svg
              key={`${face}-${current.u}-${mode}`}
              className="gi-glyph"
              viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
              role="img"
              aria-label={`${current.n} in Graft${face === "mono" ? " Mono" : ""}`}
            >
              {showOutline ? (
                <OutlineView glyph={outlineGlyph} outlines={outlines[face]!} />
              ) : (
                <text
                  x={VIEW_W / 2}
                  y={BASELINE}
                  textAnchor="middle"
                  fontSize="1000"
                  style={{ fontFamily: FACE_FONT[face] }}
                >
                  {current.c}
                </text>
              )}
            </svg>
          ) : (
            <p className="gi-empty">No characters match this filter.</p>
          )}
        </div>
        {current ? (
          <dl className="gi-meta">
            <div>
              <dt className="tag">Name</dt>
              <dd>{current.n}</dd>
            </div>
            <div>
              <dt className="tag">Unicode</dt>
              <dd className="mono tnum">U+{current.u}</dd>
            </div>
            <div>
              <dt className="tag">Category</dt>
              <dd>{category(current.c)}</dd>
            </div>
          </dl>
        ) : null}
        {mode === "outline" && current && !outlineGlyph ? (
          <p className="gi-note" role="status">
            {failed
              ? "Outline data did not load. Check your connection and choose Points again."
              : outlines[face]
                ? "The outline view covers basic Latin; this character is shown solid."
                : "Loading outlines…"}
          </p>
        ) : null}
      </div>

      <div className="gi-side">
        <div className="gi-toolbar">
          <div className="chips" role="group" aria-label="Filter">
            {FILTERS.map((item) => (
              <button
                key={item.key}
                type="button"
                className="chip"
                aria-pressed={item.key === filter}
                onClick={() => setFilter(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <span className="tag tnum">
            {visible.length} of {family.chars.length}
          </span>
        </div>
        <ul className="gi-grid" style={{ fontFamily: FACE_FONT[face] }}>
          {visible.map((glyph) => (
            <li key={glyph.u}>
              <button
                type="button"
                className="gi-cell"
                aria-pressed={current?.u === glyph.u}
                aria-label={`${glyph.n}, U+${glyph.u}`}
                onClick={() => setSelected(glyph.c)}
                onPointerEnter={(event) => {
                  if (event.pointerType === "mouse") setSelected(glyph.c);
                }}
              >
                {glyph.c}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
