import { useEffect, useState, type ReactNode } from "react";
import { BrandMark } from "./BrandMark";
import { GooglePlayBadge } from "./GooglePlayBadge";
import { PLAY_STORE_URL, SUPPORT_EMAIL } from "./constants";

export function SiteChrome({
  children,
  active,
}: {
  children: ReactNode;
  active: "home" | "support";
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    document.body.classList.add("site-lock");
    return () => document.body.classList.remove("site-lock");
  }, []);

  function closeNav() {
    setOpen(false);
  }

  return (
    <div className="site">
      <div className="site-stars" aria-hidden />
      <header className="site-header">
        <div className="site-wrap site-header-inner">
          <a className="site-logo" href="/" aria-label="Cosmic Lens home">
            <BrandMark size={34} />
            <span>Cosmic Lens</span>
          </a>
          <nav className={`site-nav${open ? " is-open" : ""}`}>
            <a href="/" onClick={closeNav}>
              Home
            </a>
            <a href="/#features" onClick={closeNav}>
              Features
            </a>
            <a href="/#analysis" onClick={closeNav}>
              Chart Analysis
            </a>
            <a
              href="/help-support"
              className={active === "support" ? "is-active" : undefined}
              onClick={closeNav}
            >
              Support
            </a>
          </nav>
          <div className="site-header-actions">
            <GooglePlayBadge header />
            <button
              type="button"
              className={`site-burger${open ? " is-open" : ""}`}
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <div className="site-wrap site-footer-grid">
          <div>
            <a className="site-logo" href="/">
              <BrandMark size={28} />
              <span>Cosmic Lens</span>
            </a>
            <p className="site-footer-blurb">
              Vedic chart analysis and Cosmic Intelligence for kundli, timing,
              compatibility and guidance. Android app on Google Play.
            </p>
          </div>
          <div>
            <h4>App</h4>
            <ul>
              <li>
                <a href="/#features">Features</a>
              </li>
              <li>
                <a href="/#analysis">Chart analysis</a>
              </li>
              <li>
                <a href={PLAY_STORE_URL} target="_blank" rel="noopener noreferrer">
                  Google Play
                </a>
              </li>
            </ul>
            <div style={{ marginTop: "0.75rem" }}>
              <GooglePlayBadge large />
            </div>
          </div>
          <div>
            <h4>Support</h4>
            <ul>
              <li>
                <a href="/help-support">Help &amp; Support</a>
              </li>
              <li>
                <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
              </li>
            </ul>
          </div>
        </div>
        <div className="site-wrap site-footer-bottom">
          <p>© {new Date().getFullYear()} Cosmic Lens</p>
          <p>For entertainment and personal guidance. Outcomes are not guaranteed.</p>
        </div>
      </footer>
    </div>
  );
}
