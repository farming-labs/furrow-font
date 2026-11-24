"use client";

import { type Face, FACE_FONT, setFace, useFace } from "@/lib/family";

const FACES: Array<{ key: Face; label: string }> = [
  { key: "sans", label: "Sans" },
  { key: "mono", label: "Mono" },
];

/** The family switch, docked at the bottom of the viewport so it is in reach on every section. */
export function FaceDock() {
  const face = useFace();
  return (
    <div className="face-dock" role="group" aria-label="Family shown on the page" data-face={face}>
      <span className="face-dock-label" aria-hidden="true">
        Family
      </span>
      <div className="face-dock-track">
        <span className="face-dock-thumb" aria-hidden="true" />
        {FACES.map((item) => (
          <button
            key={item.key}
            type="button"
            aria-pressed={face === item.key}
            onClick={() => setFace(item.key)}
            style={{ fontFamily: FACE_FONT[item.key] }}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}
