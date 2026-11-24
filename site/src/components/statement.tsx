const STATEMENT =
  "Made for the text people read most: labels, tables, documents and code. Clear at twelve pixels, composed at two hundred.";

/**
 * Three short columns, then a large statement whose words fill in as it
 * scrolls through the viewport (CSS scroll timeline; static elsewhere).
 */
export function Statement() {
  return (
    <section className="statement" aria-labelledby="statement-title">
      <h2 id="statement-title" className="sr-only">
        About Graft
      </h2>
      <div className="statement-cols">
        <p>
          <strong>Graft</strong> is a sans and a mono drawn as one family. Both share the same
          weights, the same vertical metrics and the same quiet rhythm, so interface text and code
          sit together without a seam.
        </p>
        <p>
          Both are <strong>variable</strong>, with every weight from 100 to 900 in one file, and{" "}
          <code>font-weight: 600</code> means the same thing in the sans and the mono.
        </p>
        <p>
          It is free under the <strong>SIL Open Font License</strong>. Use it in products, ship it
          inside apps, change it and share your version.
        </p>
      </div>
      <p className="statement-big">
        {STATEMENT.split(" ").map((word, index) => (
          <span key={`${word}-${index}`} className="statement-word">
            {word}{" "}
          </span>
        ))}
      </p>
    </section>
  );
}
