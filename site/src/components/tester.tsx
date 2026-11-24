"use client";

import { type CSSProperties, useEffect, useId, useRef, useState } from "react";
import { FACE_FONT, useFace } from "@/lib/family";

const DEFAULT_TEXT = "Write something worth reading.";
const DEFAULTS = { weight: 500, size: 128, spacing: -3, align: "center" as Align };
type Align = "left" | "center" | "right";

const ALIGNS: Array<{ key: Align; label: string; path: string }> = [
  { key: "left", label: "Align left", path: "M2 4h12M2 8h8M2 12h10" },
  { key: "center", label: "Align center", path: "M2 4h12M4 8h8M3 12h10" },
  { key: "right", label: "Align right", path: "M2 4h12M6 8h8M4 12h10" },
];

function Slider({
  label,
  value,
  min,
  max,
  unit = "",
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  unit?: string;
  onChange: (value: number) => void;
}) {
  const id = useId();
  return (
    <div className="slider">
      <label htmlFor={id}>{label}</label>
      <output htmlFor={id} className="tnum">
        {value}
        {unit}
      </output>
      <input
        id={id}
        className="range"
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        style={{ "--fill": `${((value - min) / (max - min)) * 100}%` } as CSSProperties}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}

export function Tester() {
  const face = useFace();
  const [weight, setWeight] = useState(DEFAULTS.weight);
  const [size, setSize] = useState(DEFAULTS.size);
  const [spacing, setSpacing] = useState(DEFAULTS.spacing);
  const [align, setAlign] = useState<Align>(DEFAULTS.align);
  const [text, setText] = useState(DEFAULT_TEXT);
  const [playing, setPlaying] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const textId = useId();

  // Play sweeps the weight axis from 100 to 900 and back, and pauses while the
  // tester is off screen.
  useEffect(() => {
    const root = rootRef.current;
    if (!playing || !root) return;
    let frame = 0;
    let visible = true;
    let phase = Math.asin(Math.max(-1, Math.min(1, (weight - 500) / 400)));
    let last = performance.now();
    const tick = (now: number) => {
      phase += ((now - last) / 4000) * Math.PI * 2;
      last = now;
      setWeight(Math.round(500 + 400 * Math.sin(phase)));
      if (visible) frame = requestAnimationFrame(tick);
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = Boolean(entry?.isIntersecting);
      cancelAnimationFrame(frame);
      if (visible) {
        last = performance.now();
        frame = requestAnimationFrame(tick);
      }
    });
    observer.observe(root);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
    // The sweep starts from the weight at the moment Play is pressed.
  }, [playing]);

  return (
    <div className="tester" ref={rootRef}>
      <div className="tester-bar">
        <span className="tester-face tag">{face === "mono" ? "Graft Mono" : "Graft"}</span>
        <div className="tester-group" role="group" aria-label="Alignment">
          {ALIGNS.map((item) => (
            <button
              key={item.key}
              type="button"
              className="icon-btn"
              aria-label={item.label}
              aria-pressed={align === item.key}
              onClick={() => setAlign(item.key)}
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d={item.path} />
              </svg>
            </button>
          ))}
        </div>
        <Slider
          label="Weight"
          value={weight}
          min={100}
          max={900}
          onChange={(value) => {
            setPlaying(false);
            setWeight(value);
          }}
        />
        <Slider label="Size" value={size} min={16} max={200} onChange={setSize} />
        <Slider label="Spacing" value={spacing} min={-8} max={12} unit="%" onChange={setSpacing} />
        <div className="tester-group">
          <button
            type="button"
            className="icon-btn tester-play"
            aria-pressed={playing}
            aria-label={playing ? "Pause the weight sweep" : "Sweep the weight axis"}
            onClick={() => setPlaying((value) => !value)}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              {playing ? <path d="M5 3v10M11 3v10" /> : <path d="M5 3l8 5-8 5z" />}
            </svg>
          </button>
          <button
            type="button"
            className="icon-btn"
            aria-label="Reset"
            onClick={() => {
              setPlaying(false);
              setWeight(DEFAULTS.weight);
              setSize(DEFAULTS.size);
              setSpacing(DEFAULTS.spacing);
              setAlign(DEFAULTS.align);
              setText(DEFAULT_TEXT);
            }}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M3 8a5 5 0 1 0 1.5-3.5M3 2.5v3h3" />
            </svg>
          </button>
        </div>
      </div>
      <label htmlFor={textId} className="sr-only">
        Sample text
      </label>
      <textarea
        id={textId}
        className="tester-text"
        spellCheck={false}
        rows={2}
        value={text}
        onChange={(event) => setText(event.target.value)}
        style={{
          fontFamily: FACE_FONT[face],
          fontWeight: weight,
          fontSize: `min(${size}px, 14vw)`,
          letterSpacing: `${spacing / 100}em`,
          textAlign: align,
        }}
      />
    </div>
  );
}
