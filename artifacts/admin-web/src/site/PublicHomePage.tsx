import { useEffect } from "react";
import { DailyEnergyVisual } from "./DailyEnergyVisual";
import { EngineV3Preview } from "./EngineV3Preview";
import { HeroPhoneDemo } from "./HeroPhoneDemo";
import { HeroMotion } from "./HeroMotion";
import { FeatureVisual } from "./ProductVisuals";
import { SiteChrome } from "./SiteChrome";
import { WhatYouGetVisual } from "./WhatYouGetVisual";
import "./experience.css";

const FEATURES = [
  {
    kind: "face" as const,
    eyebrow: "Face Reading · Launching Soon",
    title: "A multi-layer Vedic + science face scan.",
    text: "Front and profile imagery mapped through facial geometry, feature layers and predictive synthesis.",
    proof: ["Geometry mapping", "Vedic synthesis", "Launching soon"],
  },
  {
    kind: "vastu" as const,
    eyebrow: "AstroVastu Pro",
    title: "Scan the energy of every room.",
    text: "Read room photos, floor plans, compass direction and practical Vastu signals through one live scan.",
    proof: ["Live room scan", "Directional zones", "Dasha layer"],
  },
  {
    kind: "numerology" as const,
    eyebrow: "Numerology Pro",
    title: "Your numbers, read as a connected system.",
    text: "Life Path, Destiny, Soul Urge and name patterns assembled into one personalized analysis.",
    proof: ["Life Path", "Destiny", "Name patterns"],
  },
  {
    kind: "palmistry" as const,
    eyebrow: "Palmistry · Concept Preview",
    title: "Your palm lines, mapped layer by layer.",
    text: "A premium visual concept for a future palm scan experience. Palmistry is not currently live in the app.",
    proof: ["Life line", "Head line", "Heart line", "Concept preview"],
  },
];

export function PublicHomePage() {
  useEffect(() => {
    document.title = "Cosmic Lens — Your Kundli. Your Timing. Your Answers.";
    document.documentElement.classList.add("js");

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const targets = Array.from(
      document.querySelectorAll<HTMLElement>(".experience-section, .feature-story"),
    );

    if (reducedMotion || !("IntersectionObserver" in window)) {
      targets.forEach((target) => target.classList.add("is-visible"));
      return () => document.documentElement.classList.remove("js");
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 },
    );
    targets.forEach((target) => observer.observe(target));

    return () => {
      observer.disconnect();
      document.documentElement.classList.remove("js");
    };
  }, []);

  return (
    <SiteChrome active="home">
      <main className="experience">
        <section className="experience-hero" id="top">
          <HeroMotion />
          <div className="site-wrap experience-hero-grid">
            <div className="experience-hero-copy">
              <p className="experience-kicker">Vedic Engine · Cosmic Intelligence</p>
              <h1 className="experience-visually-hidden">Cosmic Lens</h1>
              <EngineV3Preview />
              <p className="experience-engine-headline">
                Advanced Vedic Intelligence. Built Around Your Chart.
              </p>
            </div>

            <div className="experience-hero-product">
              <div className="hero-product-halo" />
              <div className="hero-product-phone">
                <div className="hero-product-speaker" />
                <div className="hero-product-header">
                  <span><i /> Cosmic Lens</span>
                  <small>Chart Analysis</small>
                </div>
                <HeroPhoneDemo />
              </div>
            </div>
          </div>
        </section>

        <section className="experience-section analysis-section" id="analysis">
          <div className="site-wrap analysis-layout">
            <div className="experience-section-copy">
              <p className="experience-kicker">What You Will Get</p>
              <p>
                Four important areas of life, interpreted through your chart and timing.
              </p>
            </div>
            <WhatYouGetVisual />
          </div>
        </section>

        <section className="experience-section feature-showcase" id="features">
          <div className="site-wrap">
            <div className="experience-section-heading">
              <div>
                <p className="experience-kicker">Daily Cosmic Intelligence</p>
                <h2>Check Your Energy.</h2>
              </div>
              <p>See how current planetary movement interacts with your chart and active timing.</p>
            </div>

            <DailyEnergyVisual />

            <div className="feature-story-list">
              {FEATURES.map((feature, index) => (
                <article
                  key={feature.eyebrow}
                  className={`feature-story${index % 2 ? " feature-story-reverse" : ""}`}
                >
                  <div className="feature-story-visual">
                    <FeatureVisual kind={feature.kind} />
                  </div>
                  <div className="feature-story-copy">
                    <p className="experience-kicker">{feature.eyebrow}</p>
                    <h3>{feature.title}</h3>
                    <p>{feature.text}</p>
                    <div className="feature-proof-list">
                      {feature.proof.map((item) => <span key={item}>{item}</span>)}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
    </SiteChrome>
  );
}
