import type { ReactNode } from "react";

type SectionProps = {
  id: string;
  index: string;
  label: string;
  title?: ReactNode;
  lede?: ReactNode;
  children: ReactNode;
};

export function Section({ id, index, label, title, lede, children }: SectionProps) {
  return (
    <section id={id} className="section" aria-labelledby={`${id}-title`}>
      <header className="section-head">
        <p className="eyebrow">
          <span className="index">{index}</span> <span className="slash">/</span> {label}
        </p>
        {title ? (
          <h2 id={`${id}-title`} className="h2">
            {title}
          </h2>
        ) : (
          <h2 id={`${id}-title`} className="sr-only">
            {label}
          </h2>
        )}
        {lede ? <p className="lede">{lede}</p> : null}
      </header>
      <div className="section-body">{children}</div>
    </section>
  );
}
