import outlines from "../../public/outlines-sans.json";
import { count, fontData } from "@/lib/format";

const { sans, mono } = fontData.families;
const MARQUEE = "Sans and mono for interfaces and code — Variable from 100 to 900 — Open source — ";

const SCALE = [
  { tag: "H72", size: 72, weight: 600 },
  { tag: "H48", size: 48, weight: 600 },
  { tag: "H32", size: 32, weight: 500 },
  { tag: "H24", size: 24, weight: 500 },
  { tag: "L16", size: 16, weight: 400 },
  { tag: "L14", size: 14, weight: 400 },
  { tag: "C12", size: 12, weight: 400 },
];

/** One glyph's real outline with its on-curve and off-curve points. */
function AnchorPoster({ char }: { char: string }) {
  const glyph = outlines.glyphs[char as keyof typeof outlines.glyphs];
  const height = outlines.ascent + outlines.descent;
  const pad = 120;
  return (
    <svg
      className="poster-anchors"
      viewBox={`${-pad} 180 ${glyph.w + pad * 2} ${height - 330}`}
      role="img"
      aria-label={`The outline of ${char} with its anchor points`}
    >
      <path d={glyph.d} className="poster-fill" />
      {/* On-curve points only: TrueType's many off-curve points read as noise at this size. */}
      {glyph.p.map(([x, y, on], index) =>
        on ? <circle key={index} cx={x} cy={y} r="9" className="poster-node" /> : null,
      )}
    </svg>
  );
}

export function Specimens() {
  return (
    <section className="specimens" aria-labelledby="specimens-title">
      <h2 id="specimens-title" className="sr-only">
        Specimens
      </h2>
      <div className="marquee" aria-hidden="true">
        <div className="marquee-track">
          {MARQUEE.repeat(4)}
          {MARQUEE.repeat(4)}
        </div>
      </div>
      <div className="posters">
        <figure className="poster poster-tall">
          <AnchorPoster char="a" />
          <figcaption className="poster-caption">
            <span>Lowercase a, from the font file</span>
            <span>On-curve points marked</span>
          </figcaption>
        </figure>
        <figure className="poster poster-letter" aria-label="The letter R at weight 900">
          <span className="poster-glyph" aria-hidden="true">
            R
          </span>
        </figure>
        <figure className="poster poster-card">
          <pre className="poster-colophon mono">
            {`Graft 0.2\n\nsans    Graft\nmono    Graft Mono\nwght    100–900\nglyphs  ${count(sans.glyphs + mono.glyphs)}`}
          </pre>
          <p className="poster-text">A sans and a mono that share weights, metrics and rhythm.</p>
        </figure>
        <figure className="poster poster-scale">
          <ul>
            {SCALE.map((step) => (
              <li key={step.tag}>
                <span className="tag">{step.tag}</span>
                <span style={{ fontSize: step.size, fontWeight: step.weight }}>Readable</span>
              </li>
            ))}
          </ul>
        </figure>
        <figure className="poster poster-mono">
          <pre className="mono">
            {`const graft = {\n  sans: "Graft",\n  mono: "Graft Mono",\n  weights: [100, 900],\n  glyphs: ${mono.glyphs},\n};`}
          </pre>
          <figcaption className="tag">Graft Mono, 400</figcaption>
        </figure>
      </div>
      <div className="poster-strip">
        <figure className="poster poster-weights" aria-label="Aa at nine weights">
          {[100, 200, 300, 400, 500, 600, 700, 800, 900].map((weight) => (
            <span key={weight} style={{ fontWeight: weight }} aria-hidden="true">
              Aa
            </span>
          ))}
        </figure>
      </div>
    </section>
  );
}
