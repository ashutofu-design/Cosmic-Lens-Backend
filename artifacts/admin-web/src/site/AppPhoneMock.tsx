/** CSS app previews styled to match Cosmic Lens mobile UI (#0B0F19, purple accent). */
export type MockScreen = "home" | "ask" | "kundli" | "milan";

export function AppPhoneMock({
  screen,
  hero = false,
}: {
  screen: MockScreen;
  hero?: boolean;
}) {
  return (
    <div className={`app-phone${hero ? " app-phone-hero" : ""}`}>
      <div className="app-phone-orbit" aria-hidden />
      <div className="app-phone-frame">
        <div className="app-phone-notch" />
        <div className="app-phone-screen">
          {screen === "home" && <MockHome />}
          {screen === "ask" && <MockAsk />}
          {screen === "kundli" && <MockKundli />}
          {screen === "milan" && <MockMilan />}
          <MockTabBar active={screen === "ask" ? "ask" : screen === "home" ? "home" : "home"} />
        </div>
      </div>
    </div>
  );
}

function MockTabBar({ active }: { active: "home" | "ask" }) {
  const tabs = [
    { id: "home", label: "Home" },
    { id: "map", label: "Life Map" },
    { id: "ask", label: "Ask" },
    { id: "future", label: "Future" },
  ] as const;
  return (
    <div className="mock-tabs">
      {tabs.map((t) => (
        <span key={t.id} className={t.id === active ? "on" : undefined}>
          {t.label}
        </span>
      ))}
    </div>
  );
}

function MockHome() {
  return (
    <>
      <p className="mock-app-greet">Namaste</p>
      <p className="mock-app-title">Today&apos;s Energy</p>
      <div className="mock-energy-bar">
        <span style={{ width: "72%" }} />
      </div>
      <div className="mock-mini-cards">
        <div>Dosh Analysis</div>
        <div>Risk Radar</div>
      </div>
    </>
  );
}

function MockAsk() {
  return (
    <>
      <p className="mock-app-kicker">Ask</p>
      <p className="mock-app-q">Shaadi ke liye sahi time kab hai?</p>
      <div className="mock-app-reply">
        Venus antardasha supports commitment from late monsoon. Chart shows strong 7th house
        activation — timing clears after Navratri window.
      </div>
    </>
  );
}

function MockKundli() {
  return (
    <>
      <p className="mock-app-kicker">Kundli</p>
      <p className="mock-app-title">Lagna · Simha</p>
      <div className="mock-kundli-wheel" />
      <div className="mock-app-tags">
        <span>Mahadasha · Shani</span>
        <span>Moon · Karka</span>
      </div>
    </>
  );
}

function MockMilan() {
  return (
    <>
      <p className="mock-app-kicker">Kundli Milan</p>
      <p className="mock-app-title">Compatibility</p>
      <div className="mock-score">78<span>/100</span></div>
      <p className="mock-app-sub">Guna milan + dasha harmony</p>
    </>
  );
}
