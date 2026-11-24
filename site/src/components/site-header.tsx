export function SiteHeader() {
  return (
    <header className="site-header">
      <a className="wordmark" href="/" aria-label="Graft home">
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M2 2h12v3H5v6h6v-1H8V7h6v7H2z" />
        </svg>
        Graft
      </a>
      <a className="btn primary btn-compact" href="#install">
        Get Graft
        <span className="btn-meta" aria-hidden="true">
          ↓
        </span>
      </a>
    </header>
  );
}
