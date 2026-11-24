"use client";

import { type CSSProperties, useEffect, useRef } from "react";
import { useFace } from "@/lib/family";

const REST = 600;
const NEAR = 160;
/** Letters within this many pixels of the pointer thin toward `NEAR`. */
const RADIUS_PX = 280;

type Metrics = { upm: number; capHeight: number; xHeight: number; descent: number };

type HeroTitleProps = {
  word: string;
  metrics: Record<"sans" | "mono", Metrics>;
};

/**
 * The hero wordmark with real metric lines drawn across the page. Each letter
 * sweeps the weight axis once on load (CSS), then thins out under the pointer.
 */
export function HeroTitle({ word, metrics }: HeroTitleProps) {
  const face = useFace();
  const rootRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const probeRef = useRef<HTMLSpanElement>(null);
  const readoutRef = useRef<HTMLSpanElement>(null);
  const m = metrics[face];
  const lines = [
    { key: "cap", label: "Cap height", value: m.capHeight },
    { key: "x", label: "x-height", value: m.xHeight },
    { key: "base", label: "Baseline", value: 0 },
    { key: "desc", label: "Descender", value: m.descent },
  ];

  // Lines sit at the rendered baseline: a zero-height inline-block ends exactly
  // on it, so its bottom edge is the baseline whatever the font's line metrics.
  useEffect(() => {
    const root = rootRef.current;
    const title = titleRef.current;
    const probe = probeRef.current;
    if (!root || !title || !probe) return;
    const place = () => {
      const size = Number.parseFloat(getComputedStyle(title).fontSize);
      const baseline = probe.offsetTop + probe.offsetHeight + title.offsetTop;
      for (const line of lines) {
        const y = baseline - (line.value / m.upm) * size;
        root.style.setProperty(`--line-${line.key}`, `${y.toFixed(1)}px`);
      }
      root.dataset.placed = "";
    };
    place();
    const observer = new ResizeObserver(place);
    observer.observe(title);
    void document.fonts.ready.then(place);
    return () => observer.disconnect();
    // `lines` follows `m`, which follows the face.
  }, [m]);

  useEffect(() => {
    const title = titleRef.current;
    const readout = readoutRef.current;
    if (!title || !readout) return;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (!fine.matches || reduce.matches) return;

    const letters = Array.from(title.querySelectorAll<HTMLSpanElement>("[data-letter]"));
    let centers: Array<{ x: number; y: number }> = [];
    let frame = 0;
    let pointer = { x: 0, y: 0 };

    // Centers are measured once per hover, not per frame: letters change width
    // with weight, and re-measuring would chase that movement.
    const measure = () => {
      centers = letters.map((letter) => {
        const box = letter.getBoundingClientRect();
        return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
      });
    };

    const paint = () => {
      frame = 0;
      let lightest = REST;
      letters.forEach((letter, index) => {
        const center = centers[index];
        if (!center) return;
        const distance = Math.hypot(pointer.x - center.x, (pointer.y - center.y) * 0.6);
        const t = Math.max(0, 1 - distance / RADIUS_PX);
        const weight = Math.round(REST + (NEAR - REST) * t * t * (3 - 2 * t));
        letter.style.fontWeight = String(weight);
        lightest = Math.min(lightest, weight);
      });
      readout.textContent = String(lightest);
    };

    const onEnter = (event: PointerEvent) => {
      measure();
      title.dataset.tracking = "";
      pointer = { x: event.clientX, y: event.clientY };
      frame ||= requestAnimationFrame(paint);
    };
    const onMove = (event: PointerEvent) => {
      pointer = { x: event.clientX, y: event.clientY };
      frame ||= requestAnimationFrame(paint);
    };
    const onLeave = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      delete title.dataset.tracking;
      for (const letter of letters) letter.style.removeProperty("font-weight");
      readout.textContent = String(REST);
    };
    const onScroll = () => {
      if ("tracking" in title.dataset) measure();
    };

    title.addEventListener("pointerenter", onEnter);
    title.addEventListener("pointermove", onMove);
    title.addEventListener("pointerleave", onLeave);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(frame);
      title.removeEventListener("pointerenter", onEnter);
      title.removeEventListener("pointermove", onMove);
      title.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", measure);
    };
  }, [face]);

  return (
    <div className="hero-word" ref={rootRef}>
      <div className="metric-lines" aria-hidden="true">
        {lines.map((line, index) => (
          <div
            key={line.key}
            className="metric-line"
            data-line={line.key}
            style={{ top: `var(--line-${line.key})`, "--i": index } as CSSProperties}
          >
            <span className="metric-name">{line.label}</span>
            <span className="metric-value tnum">{line.value}</span>
          </div>
        ))}
      </div>
      <h1 id="hero-title" className="hero-title" ref={titleRef} aria-label={word}>
        {Array.from(word).map((letter, index) => (
          <span
            key={`${face}-${letter}-${index}`}
            data-letter=""
            className="hero-letter"
            aria-hidden="true"
            style={{ animationDelay: `${index * 60}ms` }}
          >
            {letter}
          </span>
        ))}
        <span ref={probeRef} className="hero-probe" aria-hidden="true" />
      </h1>
      <p className="hero-axis tag" aria-hidden="true">
        wght <span ref={readoutRef}>{REST}</span>
        <span className="hero-axis-hint">Point at the word</span>
      </p>
    </div>
  );
}
