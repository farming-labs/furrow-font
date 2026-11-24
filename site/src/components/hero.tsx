import { fontData, kb } from "@/lib/format";
import { HeroTitle } from "./hero-title";

const { sans, mono } = fontData.families;

export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <p className="hero-meta">
        <span>v0.2</span>
        <span>Sans + Mono</span>
        <span>
          wght {sans.weight[0]}–{sans.weight[1]}
        </span>
      </p>
      <HeroTitle word="Graft." metrics={{ sans: sans.metrics, mono: mono.metrics }} />
      <div className="hero-foot">
        <p className="hero-sub">
          A typeface for interfaces and code. <span>Open source under the SIL OFL.</span>
        </p>
        <div className="hero-actions">
          <a className="btn primary" href={fontData.zip.url} download>
            Download <span className="tnum btn-meta">{kb(fontData.zip.bytes)}</span>
          </a>
          <a className="btn" href="#tester">
            Try it
          </a>
        </div>
      </div>
    </section>
  );
}
