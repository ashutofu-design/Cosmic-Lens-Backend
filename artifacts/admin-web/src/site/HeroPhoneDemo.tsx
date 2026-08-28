import { useEffect, useState } from "react";

const HERO_QUESTIONS = [
  {
    question: "When will I buy my new house?",
    answer:
      "Your chart points to an upcoming June window. An east-facing home looks supportive.",
    context: "4th house · Jupiter · Timing",
  },
  {
    question: "Will I have a relationship with the person I am talking to?",
    answer:
      "The connection can deepen, but communication needs clarity. A stronger relationship window develops ahead.",
    context: "D9 · Venus · Relationship",
  },
] as const;

export function HeroPhoneDemo() {
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<"question" | "reading" | "answer">("question");
  const [answer, setAnswer] = useState("");
  const active = HERO_QUESTIONS[index];

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setPhase("answer");
      setAnswer(active.answer);
      return;
    }

    let character = 0;
    let typingTimer = 0;
    const timers: number[] = [];
    setPhase("question");
    setAnswer("");

    timers.push(window.setTimeout(() => setPhase("reading"), 950));
    timers.push(
      window.setTimeout(() => {
        setPhase("answer");
        typingTimer = window.setInterval(() => {
          character += 1;
          setAnswer(active.answer.slice(0, character));
          if (character >= active.answer.length) window.clearInterval(typingTimer);
        }, 20);
      }, 1900),
    );
    timers.push(
      window.setTimeout(() => {
        setIndex((current) => (current + 1) % HERO_QUESTIONS.length);
      }, 7200),
    );

    return () => {
      timers.forEach(window.clearTimeout);
      window.clearInterval(typingTimer);
    };
  }, [active.answer]);

  return (
    <div className="hero-phone-demo">
      <div className="hero-chat-header">
        <span className="hero-chat-avatar" aria-hidden>✦</span>
        <span className="hero-chat-identity">
          <strong>Cosmic V1</strong>
          <small><i /> Chart guidance · Online</small>
        </span>
        <button type="button" tabIndex={-1} aria-label="Conversation menu">•••</button>
      </div>

      <div className="hero-chat-conversation">
        <span className="hero-chat-day">Today</span>

        <div className="hero-chat-user-row" key={`hero-question-${index}`}>
          <div className="hero-chat-user-bubble">{active.question}</div>
          <small>Now</small>
        </div>

        {phase !== "question" ? (
          <div className="hero-chat-astrologer-row">
            <span className="hero-chat-mini-avatar" aria-hidden>✦</span>
            <div>
              {phase === "reading" ? (
                <div className="hero-chat-typing" aria-label="Astrologer is reading your chart">
                  <i /><i /><i />
                </div>
              ) : (
                <div className="hero-chat-answer">
                  <span className="hero-chat-chart-chip">✧ {active.context}</span>
                  <p>
                    {answer}
                    {answer.length < active.answer.length ? <i className="hero-phone-caret" /> : null}
                  </p>
                </div>
              )}
              <small>{phase === "reading" ? "Reading your chart…" : "Just now"}</small>
            </div>
          </div>
        ) : null}
      </div>

      <div className="hero-chat-composer">
        <span>Ask about your life…</span>
        <i aria-hidden>↑</i>
      </div>

      <div className="hero-phone-progress" aria-hidden>
        {HERO_QUESTIONS.map((item, itemIndex) => (
          <span key={item.question} className={itemIndex === index ? "is-active" : undefined} />
        ))}
      </div>
    </div>
  );
}
