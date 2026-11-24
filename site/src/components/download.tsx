import { fontData, kb } from "@/lib/format";
import { CodePanel } from "./code-panel";

const { sans, mono } = fontData.families;

const NPM = "npm install @farming-labs/graft";

const NEXT = `import { GraftSans } from "@farming-labs/graft/font/sans";
import { GraftMono } from "@farming-labs/graft/font/mono";

export default function RootLayout({ children }) {
  return (
    <html className={\`\${GraftSans.variable} \${GraftMono.variable}\`}>
      <body className={GraftSans.className}>{children}</body>
    </html>
  );
}`;

const FARM_REMOTE = `import { remoteFont } from "@farm.js/core/font";

const graft = remoteFont({
  src: "https://graft.farming-labs.dev/fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft-sans",
});

const graftMono = remoteFont({
  src: "https://graft.farming-labs.dev/fonts/GraftMono-Variable.woff2",
  family: "Graft Mono",
  weight: "100 900",
  variable: "--font-graft-mono",
});`;

const FARM_LOCAL = `import { localFont } from "@farm.js/core/font";

const graft = localFont({
  src: "@farming-labs/graft/fonts/Graft-Variable.woff2",
  family: "Graft",
  weight: "100 900",
  variable: "--font-graft-sans",
});`;

const CSS = `import "@farming-labs/graft/graft.css";

/* Then, in your styles: */
body { font-family: var(--font-graft-sans); }
code { font-family: var(--font-graft-mono); }`;

/** How to install: a heading on the left, an accordion of methods on the right. */
export function Download() {
  const files = [
    { name: "Graft-Variable.woff2", use: "Web", ...sans.files.woff2 },
    { name: "Graft-Variable.ttf", use: "Desktop", ...sans.files.ttf },
    { name: "GraftMono-Variable.woff2", use: "Web", ...mono.files.woff2 },
    { name: "GraftMono-Variable.ttf", use: "Desktop", ...mono.files.ttf },
  ];
  return (
    <div className="install">
      <div className="accordion">
        <details open>
          <summary>npm package</summary>
          <div className="accordion-body">
            <p>
              One package with both families: a Next.js font, a Farm.js font source, or a stylesheet
              for any bundler.
            </p>
            <CodePanel label="Terminal" language="sh" code={NPM} />
          </div>
        </details>
        <details>
          <summary>Next.js</summary>
          <div className="accordion-body">
            <p>
              Each export is a <code>next/font/local</code> font with a CSS variable,{" "}
              <code>--font-graft-sans</code> and <code>--font-graft-mono</code>.
            </p>
            <CodePanel label="app/layout.tsx" language="tsx" code={NEXT} />
          </div>
        </details>
        <details>
          <summary>Farm.js</summary>
          <div className="accordion-body">
            <p>
              No install needed. <code>remoteFont</code> downloads both files during the build and
              serves them from your app, fingerprinted like any other asset.
            </p>
            <CodePanel label="src/app/layout.tsx" language="tsx" code={FARM_REMOTE} />
            <p>
              Or, with the npm package, <code>localFont</code> reads the file straight from{" "}
              <code>node_modules</code>.
            </p>
            <CodePanel label="src/app/layout.tsx" language="tsx" code={FARM_LOCAL} />
          </div>
        </details>
        <details>
          <summary>Plain CSS</summary>
          <div className="accordion-body">
            <p>Vite, webpack and Parcel bundle the font files from the stylesheet.</p>
            <CodePanel label="main.ts" language="ts" code={CSS} />
          </div>
        </details>
        <details>
          <summary>Font files</summary>
          <div className="accordion-body">
            <p>
              Both families as variable WOFF2 for the web and TTF for desktop apps, with the
              license.
            </p>
            <a className="btn primary" href={fontData.zip.url} download>
              Download everything <span className="tnum btn-meta">{kb(fontData.zip.bytes)}</span>
            </a>
            <table className="files">
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col" className="files-use">
                    Use
                  </th>
                  <th scope="col">Size</th>
                  <th scope="col">
                    <span className="sr-only">Download</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.name}>
                    <td className="mono">{file.name}</td>
                    <td className="files-use">{file.use}</td>
                    <td className="tnum">{kb(file.bytes)}</td>
                    <td>
                      <a href={file.url} download aria-label={`Download ${file.name}`}>
                        ↓
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}
