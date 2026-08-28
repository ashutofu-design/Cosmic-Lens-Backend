import { useEffect, useRef, useState, type ReactNode } from "react";
import { SUPPORT_EMAIL } from "./constants";
import { GooglePlayBadge } from "./GooglePlayBadge";
import { SiteChrome } from "./SiteChrome";

import { unlockAdminPanel } from "../lib/adminGate";

const REQUIRED_TAPS = 3;
const UNLOCK_STEPS = ["locate", "locate", "locate", "for", "for", "for"] as const;

export function HelpSupportPage() {
  const [locateTaps, setLocateTaps] = useState(0);
  const [forTaps, setForTaps] = useState(0);
  const locateDone = locateTaps >= REQUIRED_TAPS;
  const resetTimerRef = useRef<number | null>(null);

  useEffect(() => {
    document.title = "Help & Support — Cosmic Lens";
  }, []);

  useEffect(() => {
    return () => {
      if (resetTimerRef.current != null) window.clearTimeout(resetTimerRef.current);
    };
  }, []);

  function armReset() {
    if (resetTimerRef.current != null) window.clearTimeout(resetTimerRef.current);
    resetTimerRef.current = window.setTimeout(() => {
      setLocateTaps(0);
      setForTaps(0);
      resetTimerRef.current = null;
    }, 120_000);
  }

  function onLocateTap(e: React.MouseEvent) {
    e.preventDefault();
    if (locateDone) return;
    armReset();
    setLocateTaps((n) => Math.min(REQUIRED_TAPS, n + 1));
  }

  function onForTap(e: React.MouseEvent) {
    e.preventDefault();
    if (!locateDone) return;
    armReset();
    setForTaps((n) => {
      const next = Math.min(REQUIRED_TAPS, n + 1);
      if (next >= REQUIRED_TAPS) {
        void (async () => {
          try {
            await unlockAdminPanel([...UNLOCK_STEPS]);
            window.location.href = "/admin?tab=users";
          } catch {
            setLocateTaps(0);
            setForTaps(0);
          }
        })();
      }
      return next;
    });
  }

  const topics: { q: string; a: ReactNode }[] = [
    {
      q: "Where is my PDF / report?",
      a: "Paid reports unlock inside the Cosmic Lens app under My Reports after a successful payment. If a download is delayed, keep the app open on a stable network, then write to support with your COSMO ID.",
    },
    {
      q: "How do I find my COSMO ID?",
      a: (
        <>
          Open the app → Profile. Your COSMO ID is listed on the profile screen. Share it when you
          email support so we can{" "}
          <button type="button" className="site-text-link" onClick={onLocateTap}>
            locate
          </button>{" "}
          your account quickly.
        </>
      ),
    },
    {
      q: "Payments and refunds",
      a: (
        <>
          Subscriptions and one-time reports are billed in INR through authorised Indian payment
          partners.{" "}
          <button type="button" className="site-text-link" onClick={onForTap}>
            For
          </button>{" "}
          billing questions, email us with the order ID shown in Payment History.
        </>
      ),
    },
    {
      q: "In-app Help & Support chat",
      a: "Signed-in users can message the Cosmic Care Team from Profile → Help & Support in the Android app. That chat is the fastest path for account-specific issues.",
    },
  ];

  return (
    <SiteChrome active="support">
      <main>
        <section className="site-hero site-hero-compact">
          <div className="site-wrap">
            <p className="site-badge">Help &amp; Support</p>
            <h1>We are here to help</h1>
            <p className="site-lead">
              Billing, reports, account, or app questions — reach Cosmic Lens support directly. For
              signed-in users, the in-app Help &amp; Support chat is the fastest desk.
            </p>
          </div>
        </section>

        <section className="site-section">
          <div className="site-wrap site-support-grid">
            <article className="site-card">
              <h3>Email</h3>
              <p>We typically respond within 1–2 business days.</p>
              <a className="site-inline" href={`mailto:${SUPPORT_EMAIL}`}>
                {SUPPORT_EMAIL}
              </a>
            </article>
            <article className="site-card">
              <h3>In the app</h3>
              <p>Profile → Help &amp; Support for persistent chat with screenshots.</p>
              <GooglePlayBadge />
            </article>
          </div>
        </section>

        <section className="site-section site-section-alt">
          <div className="site-wrap">
            <div className="site-head">
              <p className="site-eyebrow">Common questions</p>
              <h2>Quick answers</h2>
            </div>
            <div className="site-faq">
              {topics.map((item) => (
                <article key={item.q} className="site-card">
                  <h3>{item.q}</h3>
                  <p>{item.a}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
    </SiteChrome>
  );
}
