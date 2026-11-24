import { CodePanel } from "@/components/code-panel";
import { Credits } from "@/components/credits";
import { Download } from "@/components/download";
import { FaceDock } from "@/components/face-dock";
import { GlyphInspector } from "@/components/glyph-inspector";
import { Hero } from "@/components/hero";
import { MonoShowcase } from "@/components/mono-showcase";
import { Numbers } from "@/components/numbers";
import { Section } from "@/components/section";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Specimens } from "@/components/specimens";
import { Statement } from "@/components/statement";
import { Stats } from "@/components/stats";
import { Tester } from "@/components/tester";
import { Weights } from "@/components/weights";
import { fontData } from "@/lib/format";

const NUMBERS_CSS = `.price { font-variant-numeric: tabular-nums; }
.recipe { font-variant-numeric: diagonal-fractions; }
.footnote { font-variant-position: super; }`;

// The page reads no cookies, headers or session data, so it renders once at build time.
export const dynamic = "force-static";

const { sans, mono } = fontData.families;

export default function HomePage() {
  const numberRows = [
    { label: "Graft-Variable.woff2", value: sans.files.woff2.bytes, unit: "bytes" },
    { label: "GraftMono-Variable.woff2", value: mono.files.woff2.bytes, unit: "bytes" },
    { label: "Graft-Variable.ttf", value: sans.files.ttf.bytes, unit: "bytes" },
    { label: "Sans characters", value: sans.characters, unit: "chars" },
    { label: "Mono characters", value: mono.characters, unit: "chars" },
    { label: "GraftMono-Variable.ttf", value: mono.files.ttf.bytes, unit: "bytes" },
  ];

  return (
    <>
      <a className="skip-link" href="#content">
        Skip to content
      </a>
      <SiteHeader />
      <main id="content" tabIndex={-1}>
        <Hero />
        <Stats />
        <Statement />
        <Section
          id="glyphs"
          index="01"
          label="Glyphs"
          title={
            <>
              Every character, up close. <span>Filled, or down to its points.</span>
            </>
          }
        >
          <GlyphInspector
            families={{
              sans: { chars: sans.chars, metrics: sans.metrics },
              mono: { chars: mono.chars, metrics: mono.metrics },
            }}
          />
        </Section>
        <Specimens />
        <Section
          id="tester"
          index="02"
          label="Tester"
          title={
            <>
              Your own words. <span>At any size and weight.</span>
            </>
          }
        >
          <Tester />
        </Section>
        <Section
          id="weights"
          index="03"
          label="Weights"
          title={
            <>
              Nine named weights. <span>Every step between.</span>
            </>
          }
          lede="One variable file covers 100 to 900, in both the sans and the mono."
        >
          <Weights />
        </Section>
        <Section
          id="numbers"
          index="04"
          label="Numbers"
          title={
            <>
              Figures that line up. <span>And sit still.</span>
            </>
          }
          lede="Tabular, fraction, superscript and subscript figures are drawn with the digits, so every numeric style matches. Toggle the OpenType features to compare."
        >
          <Numbers rows={numberRows} />
          <div className="num-css">
            <CodePanel label="styles.css" language="css" code={NUMBERS_CSS} />
          </div>
        </Section>
        <Section
          id="mono"
          index="05"
          label="Mono"
          title={
            <>
              Graft Mono. <span>Same width, every character.</span>
            </>
          }
        >
          <MonoShowcase />
        </Section>
        <Section
          id="install"
          index="06"
          label="Install"
          title={
            <>
              Add it to a project. <span>A package, a URL, or the files.</span>
            </>
          }
        >
          <Download />
        </Section>
        <Section id="license" index="07" label="License">
          <Credits />
        </Section>
      </main>
      <SiteFooter />
      <FaceDock />
    </>
  );
}
