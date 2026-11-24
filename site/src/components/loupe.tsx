"use client";

import { useEffect, useRef } from "react";

type Metrics = { upm: number; capHeight: number; xHeight: number; descent: number };
type LoupeGlyph = { label: string; font: string; metrics: Metrics };

const ZOOM = 2.5;
const VIEW_W = 1400;
const VIEW_H = 1300;
const BASELINE = 950;

function Scene({ glyphs }: { glyphs: LoupeGlyph[] }) {
  return (
    <div className="loupe-scene">
      {glyphs.map((glyph) => {
        const lines = [
          { y: BASELINE - glyph.metrics.xHeight, label: "x-height" },
          { y: BASELINE, label: "Baseline" },
          { y: BASELINE - glyph.metrics.descent, label: "Descender" },
        ];
        return (
          <figure key={glyph.label} className="loupe-figure">
            <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} aria-hidden="true">
              {lines.map((line) => (
                <line
                  key={line.label}
                  x1="0"
                  x2={VIEW_W}
                  y1={line.y}
                  y2={line.y}
                  className="loupe-line"
                />
              ))}
              <text
                x={VIEW_W / 2}
                y={BASELINE}
                textAnchor="middle"
                fontSize="1000"
                style={{ fontFamily: glyph.font }}
              >
                ag
              </text>
            </svg>
            <figcaption className="tag">{glyph.label}</figcaption>
          </figure>
        );
      })}
    </div>
  );
}

/**
 * A specimen with a magnifier. The lens rests on the first glyph's terminal
 * and follows a fine pointer; it shows the same scene drawn two and a half times
 * larger, so the zoom is real type, not a scaled bitmap.
 */
export function Loupe({ glyphs }: { glyphs: LoupeGlyph[] }) {
  const stageRef = useRef<HTMLDivElement>(null);
  const lensRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stage = stageRef.current;
    const lens = lensRef.current;
    const inner = innerRef.current;
    if (!stage || !lens || !inner) return;
    let rest = { x: 0, y: 0 };
    // The lens size comes from CSS (smaller on phones).
    let radius = lens.offsetWidth / 2;
    let frame = 0;
    let target = rest;

    const move = (point: { x: number; y: number }) => {
      lens.style.transform = `translate(${point.x - radius}px, ${point.y - radius}px)`;
      inner.style.transform = `translate(${radius - point.x * ZOOM}px, ${radius - point.y * ZOOM}px) scale(${ZOOM})`;
    };
    const measure = () => {
      const box = stage.getBoundingClientRect();
      radius = lens.offsetWidth / 2;
      inner.style.width = `${box.width}px`;
      inner.style.height = `${box.height}px`;
      const first = stage.querySelector("svg")?.getBoundingClientRect();
      // The top terminal of the first `a`.
      rest = first
        ? {
            x: Math.max(radius + 1, first.left - box.left + first.width * 0.25),
            y: first.top - box.top + first.height * 0.45,
          }
        : { x: box.width / 3, y: box.height / 2 };
      if (!("tracking" in stage.dataset)) move(rest);
    };
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(stage);
    void document.fonts.ready.then(measure);
    stage.dataset.ready = "";

    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || reduce) return () => resize.disconnect();

    const paint = () => {
      frame = 0;
      move(target);
    };
    const onMove = (event: PointerEvent) => {
      const box = stage.getBoundingClientRect();
      target = { x: event.clientX - box.left, y: event.clientY - box.top };
      stage.dataset.tracking = "";
      frame ||= requestAnimationFrame(paint);
    };
    const onLeave = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      delete stage.dataset.tracking;
      move(rest);
    };
    stage.addEventListener("pointermove", onMove);
    stage.addEventListener("pointerleave", onLeave);
    return () => {
      resize.disconnect();
      cancelAnimationFrame(frame);
      stage.removeEventListener("pointermove", onMove);
      stage.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  return (
    <div className="loupe-stage" ref={stageRef}>
      <Scene glyphs={glyphs} />
      <div className="loupe" ref={lensRef} aria-hidden="true">
        <div className="loupe-inner" ref={innerRef}>
          <Scene glyphs={glyphs} />
        </div>
      </div>
    </div>
  );
}
