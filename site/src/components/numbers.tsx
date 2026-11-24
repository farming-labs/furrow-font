"use client";

import { useEffect, useRef, useState } from "react";

type Row = { label: string; value: number; unit: string };

function Toggle({
  label,
  on,
  onChange,
  options,
}: {
  label: string;
  on: boolean;
  onChange: (on: boolean) => void;
  options: [string, string];
}) {
  return (
    <div className="chips" role="group" aria-label={label}>
      <button type="button" className="chip" aria-pressed={!on} onClick={() => onChange(false)}>
        {options[0]}
      </button>
      <button type="button" className="chip" aria-pressed={on} onClick={() => onChange(true)}>
        {options[1]}
      </button>
    </div>
  );
}

const COUNT_MS = 1400;

/**
 * Counts every row up from zero when the table scrolls into view, and again on
 * each spacing toggle, so proportional digits visibly jitter while tabular ones
 * hold still. The server renders the final values.
 */
function useCountUp(replay: unknown) {
  const ref = useRef<HTMLElement>(null);
  const [progress, setProgress] = useState(1);
  const seen = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const run = () => {
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / COUNT_MS);
        setProgress(1 - (1 - t) ** 4);
        if (t < 1) frame = requestAnimationFrame(tick);
      };
      setProgress(0);
      frame = requestAnimationFrame(tick);
    };
    if (seen.current) {
      run();
      return () => cancelAnimationFrame(frame);
    }
    // Start from zero only while the table is still below the fold, so nobody
    // watches the final values reset.
    if (el.getBoundingClientRect().top > window.innerHeight) setProgress(0);
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        seen.current = true;
        run();
      },
      { threshold: 0.5 },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [replay]);

  return { ref, progress };
}

function TabularTable({ rows }: { rows: Row[] }) {
  const [tabular, setTabular] = useState(true);
  const { ref, progress } = useCountUp(tabular);
  return (
    <article className="num-card" ref={ref}>
      <header>
        <h3>Tabular figures</h3>
        <Toggle
          label="Figure spacing"
          on={tabular}
          onChange={setTabular}
          options={["Proportional", "Tabular"]}
        />
      </header>
      <table
        className="num-table"
        style={{ fontVariantNumeric: tabular ? "tabular-nums" : "proportional-nums" }}
      >
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row" className="mono">
                {row.label}
              </th>
              <td>
                {Math.round(row.value * progress).toLocaleString("en-US")} <span>{row.unit}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="num-note">
        The real file sizes and counts of this release. Tabular figures share one width, so columns
        line up.
      </p>
    </article>
  );
}

function format(date: Date) {
  const pad = (n: number, size = 2) => String(n).padStart(size, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`;
}

function LiveClock() {
  const root = useRef<HTMLElement>(null);
  const proportional = useRef<HTMLSpanElement>(null);
  const tabular = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const node = root.current;
    if (!node) return;
    const write = () => {
      const text = format(new Date());
      if (proportional.current) proportional.current.textContent = text;
      if (tabular.current) tabular.current.textContent = text;
    };
    write();
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    let visible = false;
    const loop = () => {
      write();
      frame = requestAnimationFrame(loop);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      if (visible && !document.hidden) frame = requestAnimationFrame(loop);
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = Boolean(entry?.isIntersecting);
      sync();
    });
    observer.observe(node);
    document.addEventListener("visibilitychange", sync);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", sync);
    };
  }, []);

  return (
    <article className="num-card" ref={root}>
      <header>
        <h3>Why it matters</h3>
        <span className="tag">Your local time</span>
      </header>
      <div className="clock">
        <div>
          <span className="tag">Proportional</span>
          <span
            ref={proportional}
            className="clock-value"
            style={{ fontVariantNumeric: "proportional-nums" }}
          >
            00:00:00.000
          </span>
        </div>
        <div>
          <span className="tag">Tabular</span>
          <span
            ref={tabular}
            className="clock-value"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            00:00:00.000
          </span>
        </div>
      </div>
      <p className="num-note">
        Proportional digits change width as they count, so the line shakes. Tabular digits hold
        still.
      </p>
    </article>
  );
}

function Fractions() {
  const [on, setOn] = useState(true);
  return (
    <article className="num-card">
      <header>
        <h3>Fractions</h3>
        <Toggle label="Fractions" on={on} onChange={setOn} options={["Off", "frac"]} />
      </header>
      <p className="num-big" style={{ fontVariantNumeric: on ? "diagonal-fractions" : "normal" }}>
        1/2 3/4 5/8 15/16
      </p>
      <p className="num-note">
        Numerator and denominator figures are drawn to match the digits around them.
      </p>
    </article>
  );
}

function Positions() {
  const [on, setOn] = useState(true);
  const position = (value: "super" | "sub") => (on ? { fontVariantPosition: value } : undefined);
  return (
    <article className="num-card">
      <header>
        <h3>Superscript and subscript</h3>
        <Toggle label="Position forms" on={on} onChange={setOn} options={["Off", "sups subs"]} />
      </header>
      <p className="num-big">
        E = mc<span style={position("super")}>2</span> · H<span style={position("sub")}>2</span>O ·
        x<span style={position("super")}>10</span>
      </p>
      <p className="num-note">
        Real superscript and subscript glyphs from the font, not shrunken digits.
      </p>
    </article>
  );
}

export function Numbers({ rows }: { rows: Row[] }) {
  return (
    <div className="numbers">
      <div className="num-hero" aria-label="Figures zero to nine">
        <span>0123456789</span>
        <span>0123456789</span>
      </div>
      <div className="num-grid">
        <TabularTable rows={rows} />
        <LiveClock />
        <Fractions />
        <Positions />
      </div>
    </div>
  );
}
