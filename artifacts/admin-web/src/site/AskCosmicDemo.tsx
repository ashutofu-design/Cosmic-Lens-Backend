import { useEffect, useMemo, useRef, useState } from "react";

type DemoQuestion = {
  question: string;
  answer: string;
  signal: string;
  timing: string;
  houses: number[];
};

const QUESTIONS: DemoQuestion[] = [
  {
    question: "Shaadi kab hogi?",
    answer:
      "Your 7th-house pattern is strengthening. The clearer commitment window develops in the period ahead.",
    signal: "7th house · Venus",
    timing: "Commitment window developing",
    houses: [1, 7, 11],
  },
  {
    question: "Career change kab karna chahiye?",
    answer:
      "Your current period favors preparation, but the stronger transition window begins after the present cycle settles.",
    signal: "10th house · Dasha",
    timing: "Transition window ahead",
    houses: [2, 6, 10],
  },
  {
    question: "Will this relationship last?",
    answer:
      "The bond has continuity, but the current transit tests communication. Stability improves with the next supportive period.",
    signal: "D9 · Relationship",
    timing: "Communication phase active",
    houses: [3, 7, 9],
  },
  {
    question: "Business ke liye right time?",
    answer:
      "Planning is supported now. The cleaner execution window arrives when Jupiter strengthens your opportunity houses.",
    signal: "2nd · 7th · 11th",
    timing: "Build now · launch later",
    houses: [2, 7, 11],
  },
  {
    question: "Should I relocate?",
    answer:
      "Your chart supports movement, especially when the upcoming transit activates home, travel and career together.",
    signal: "4th · 9th · 10th",
    timing: "Mobility window approaching",
    houses: [4, 9, 10],
  },
  {
    question: "Property purchase ka timing?",
    answer:
      "The present cycle needs careful review. A more stable purchase window follows after the current pressure eases.",
    signal: "4th house · Saturn",
    timing: "Review first · stability ahead",
    houses: [4, 8, 11],
  },
];

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener?.("change", update);
    return () => media.removeEventListener?.("change", update);
  }, []);

  return reduced;
}

export function AskCosmicDemo({
  compact = false,
  singleQuestion = false,
}: {
  compact?: boolean;
  singleQuestion?: boolean;
}) {
  const reducedMotion = useReducedMotion();
  const hostRef = useRef<HTMLDivElement | null>(null);
  const demos = useMemo(() => (singleQuestion ? QUESTIONS.slice(0, 1) : QUESTIONS), [singleQuestion]);
  const [index, setIndex] = useState(0);
  const [typedAnswer, setTypedAnswer] = useState("");
  const [phase, setPhase] = useState<"reading" | "answer" | "timing">("reading");
  const [visible, setVisible] = useState(false);
  const active = demos[index % demos.length];

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !("IntersectionObserver" in window)) {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin: "120px" },
    );
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      setTypedAnswer(active.answer);
      setPhase("timing");
      return;
    }
    if (!visible) return;

    let character = 0;
    let typingTimer = 0;
    const timers: number[] = [];
    setTypedAnswer("");
    setPhase("reading");

    timers.push(
      window.setTimeout(() => {
        setPhase("answer");
        typingTimer = window.setInterval(() => {
          character += 1;
          setTypedAnswer(active.answer.slice(0, character));
          if (character >= active.answer.length) {
            window.clearInterval(typingTimer);
            setPhase("timing");
          }
        }, compact ? 14 : 18);
      }, compact ? 520 : 720),
    );

    if (demos.length > 1) {
      timers.push(
        window.setTimeout(() => {
          setIndex((current) => (current + 1) % demos.length);
        }, 6500),
      );
    }

    return () => {
      timers.forEach(window.clearTimeout);
      window.clearInterval(typingTimer);
    };
  }, [active.answer, compact, demos.length, reducedMotion, visible]);

  return (
    <div ref={hostRef} className={`ask-product-demo${compact ? " ask-product-demo-compact" : ""}`}>
      <div className="ask-demo-topline">
        <span className="ask-demo-engine">
          <i />
          Cosmic Intelligence
        </span>
        <span className="ask-demo-chart-id">D1 · D9 · Dasha</span>
      </div>

      <div className="ask-demo-body">
        <div className="ask-demo-question" key={`question-${index}`}>
          <small>You asked</small>
          <strong>{active.question}</strong>
        </div>

        <div className="ask-demo-analysis">
          <MiniChart activeHouses={active.houses} phase={phase} />
          <div className="ask-demo-signal">
            <small>Chart signal</small>
            <strong>{active.signal}</strong>
            <span className={`analysis-scan${phase !== "reading" ? " is-complete" : ""}`}>
              <i />
            </span>
          </div>
        </div>

        <div className={`ask-demo-answer phase-${phase}`} aria-live="polite">
          {phase === "reading" ? (
            <span className="ask-typing" aria-label="Reading chart">
              <i />
              <i />
              <i />
              <em>Reading chart context</em>
            </span>
          ) : (
            <p>
              {typedAnswer}
              {phase === "answer" ? <span className="typing-caret" /> : null}
            </p>
          )}
        </div>

        <div className={`ask-demo-timing${phase === "timing" ? " is-visible" : ""}`}>
          <span className="timing-orbit">
            <i />
          </span>
          <div>
            <small>Life timing</small>
            <strong>{active.timing}</strong>
          </div>
          <span className="timing-bars" aria-hidden>
            <i />
            <i />
            <i />
            <i />
          </span>
        </div>
      </div>

      {!singleQuestion ? (
        <div className="ask-demo-pagination" aria-label={`Question ${index + 1} of ${demos.length}`}>
          {demos.map((demo, itemIndex) => (
            <button
              key={demo.question}
              type="button"
              className={itemIndex === index ? "is-active" : undefined}
              aria-label={`Show: ${demo.question}`}
              onClick={() => setIndex(itemIndex)}
            />
          ))}
        </div>
      ) : null}

      <span className="product-preview-note">Representative product preview</span>
    </div>
  );
}

function MiniChart({
  activeHouses,
  phase,
}: {
  activeHouses: number[];
  phase: "reading" | "answer" | "timing";
}) {
  return (
    <div className={`mini-vedic-chart phase-${phase}`} aria-label="Vedic chart preview">
      <span className="chart-diamond chart-diamond-a" />
      <span className="chart-diamond chart-diamond-b" />
      <span className="chart-axis chart-axis-a" />
      <span className="chart-axis chart-axis-b" />
      {Array.from({ length: 12 }, (_, index) => {
        const house = index + 1;
        return (
          <i
            key={house}
            className={activeHouses.includes(house) ? "is-active" : undefined}
            style={{
              left: `${50 + Math.cos((index / 12) * Math.PI * 2 - Math.PI / 2) * 38}%`,
              top: `${50 + Math.sin((index / 12) * Math.PI * 2 - Math.PI / 2) * 38}%`,
            }}
          >
            {house}
          </i>
        );
      })}
      <b>La</b>
    </div>
  );
}
