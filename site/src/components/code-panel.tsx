import { highlight } from "sugar-high";
import { CopyButton } from "./copy-button";

type CodePanelProps = {
  /** The file name or context shown in the header. */
  label: string;
  /** Short language tag shown beside the copy button. */
  language: string;
  code: string;
};

/** Highlights code the way farmjs.dev does: token classes only, one span per run of a kind. */
function renderHighlightedCode(code: string) {
  // sugar-high repeats each token's color as an inline style. The token classes carry it in
  // globals.css instead, whitespace and punctuation need no span, and neighbouring tokens of one
  // kind share a span.
  let html = highlight(code)
    .replace(/<span class="sh__token--(?:space|sign)"[^>]*>([^<]*)<\/span>/g, "$1")
    .replace(/ style="color:var\(--sh-[a-z]+\)"/g, "");
  for (let merged = ""; merged !== html; ) {
    merged = html;
    html = html.replace(
      /<span class="(sh__token--[a-z]+)">([^<]*)<\/span>(\s*)<span class="\1">/g,
      '<span class="$1">$2$3',
    );
  }
  return html.split("\n").join("");
}

/** A code block with a file header, line numbers and a copy button. */
export function CodePanel({ label, language, code }: CodePanelProps) {
  return (
    <figure className="code">
      <figcaption className="code-head">
        <span className="code-label">
          <svg aria-hidden="true" viewBox="0 0 24 24" className="code-icon">
            <path d="m18 16 4-4-4-4M6 8l-4 4 4 4M14.5 4l-5 16" />
          </svg>
          <span className="code-file">{label}</span>
        </span>
        <span className="code-meta">
          <span className="code-lang">{language}</span>
          <CopyButton text={code} label={`Copy ${label}`} className="code-copy" />
        </span>
      </figcaption>
      <pre tabIndex={0} aria-label={`${label} code`}>
        <code
          className="code-body"
          dangerouslySetInnerHTML={{ __html: renderHighlightedCode(code.trim()) }}
        />
      </pre>
    </figure>
  );
}
