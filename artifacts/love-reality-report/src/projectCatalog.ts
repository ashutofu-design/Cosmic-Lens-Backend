export type CatalogItem = {
  name: string;
  route?: string;
  purpose: string;
  fields?: string[];
  api?: string;
  price?: string;
  plan?: string;
};

export type CatalogSection = {
  id: string;
  title: string;
  emoji: string;
  description: string;
  items: CatalogItem[];
};

export const PROJECT_APPS = [
  {
    name: "Cosmic Lens Mobile",
    path: "artifacts/cosmic-lens-mobile",
    port: "Expo Metro",
    purpose: "Main app — Android, iOS, web preview. 70+ screens.",
    run: "cd artifacts/cosmic-lens-mobile && pnpm dev:local",
  },
  {
    name: "API Server",
    path: "artifacts/api-server",
    port: "8080",
    purpose: "Flask backend — kundli, Ask AI, payments, PDF generation.",
    run: "cd artifacts/api-server && bash start.sh",
  },
  {
    name: "Admin Web",
    path: "artifacts/admin-web",
    port: "5174",
    purpose: "Internal dashboard — users, orders, Ask Q&A, revenue.",
    run: "cd artifacts/admin-web && pnpm dev",
  },
  {
    name: "Love Reality Preview",
    path: "artifacts/love-reality-report",
    port: "5180",
    purpose: "Local PDF + form preview (yeh site).",
    run: "cd artifacts/love-reality-report && pnpm dev:only",
  },
  {
    name: "Mockup Sandbox",
    path: "artifacts/mockup-sandbox",
    port: "Vite",
    purpose: "UI design mockups — Dosh, Milan, tab bars.",
    run: "Replit / PORT + BASE_PATH env required",
  },
] as const;

export const CATALOG_SECTIONS: CatalogSection[] = [
  {
    id: "auth",
    title: "Login & Onboarding",
    emoji: "🔐",
    description: "Pehli baar app khulte hi — profile banate hain.",
    items: [
      {
        name: "Login",
        route: "/login",
        purpose: "Google Sign-In / Firebase auth",
        fields: ["Google OAuth (no manual email/password)"],
      },
      {
        name: "Onboarding",
        route: "/onboarding",
        purpose: "Pehli kundli banani",
        fields: [
          "Full name",
          "DOB (day, month, year)",
          "Birth time (hour, minute, AM/PM)",
          "Birth place (search → lat/lon/timezone)",
        ],
        api: "POST /api/kundli",
      },
      {
        name: "Profile Edit",
        route: "/profile-edit",
        purpose: "Profile add/edit — self, partner, family",
        fields: [
          "Name, gender, relation",
          "DOB, birth time, birth place",
          "Display name, phone (+91)",
        ],
        api: "POST /api/user/:id/profiles/sync",
      },
    ],
  },
  {
    id: "tabs",
    title: "Bottom Tabs (Main App)",
    emoji: "📱",
    description: "Roz use hone wale 5 tabs.",
    items: [
      { name: "Home", route: "/(tabs)/index", purpose: "Aaj ki energy, forecast, dosh, risk cards" },
      { name: "Life Map", route: "/(tabs)/lifemap", purpose: "Relationship, Career, Health, Finance hub" },
      { name: "Ask Cosmo", route: "/(tabs)/ask", purpose: "AI chat — text/voice, kundli context", api: "POST /api/ask", plan: "Free: 1/day · Pro: unlimited" },
      { name: "Future", route: "/(tabs)/insights", purpose: "6-month forecasts, dasha timeline", plan: "Pro for deep" },
      { name: "Profile", route: "/(tabs)/profile", purpose: "Account, plan, language, subscription" },
    ],
  },
  {
    id: "kundli",
    title: "Kundli & Charts",
    emoji: "⭐",
    description: "Janam kundli, divisional charts, planets.",
    items: [
      { name: "My Kundli", route: "/my-kundli", purpose: "Saved profiles list → chart view" },
      { name: "Kundli Tab", route: "/(tabs)/kundli", purpose: "Full birth chart (hidden tab)" },
      { name: "Planet Position", route: "/planet-position", purpose: "Live planet positions" },
      { name: "Divisional Charts", route: "/divisional-charts", purpose: "D1, D9, D10… hub" },
      { name: "Varga Chart", route: "/varga-chart", purpose: "Single divisional chart viewer" },
      { name: "Dosh Analysis", route: "/dosh", purpose: "Mangal, Kaal Sarp, Pitra dosh", api: "POST /api/dosh-analysis" },
      { name: "Panchang", route: "/panchang", purpose: "Tithi, nakshatra, muhurat, festivals", api: "GET /api/panchang" },
      { name: "Muhurat", route: "/muhurat", purpose: "Shadi, griha, business muhurat dates" },
      { name: "Prashna Kundli", route: "/prashna-kundli", purpose: "Number 1–249 se jawab", fields: ["Number 1–249", "Optional question", "Category"], api: "POST /api/prashna/number-ask" },
      { name: "Divya Prashna", route: "/divya-prashna", purpose: "Free-text question Prashna", fields: ["Question text", "Category"], api: "POST /api/prashna/ask" },
    ],
  },
  {
    id: "daily",
    title: "Daily Tools",
    emoji: "☀️",
    description: "Roz ka rashifal, lucky, remedies.",
    items: [
      { name: "Forecast", route: "/forecast", purpose: "7-day energy chart", api: "POST /api/energy/today" },
      { name: "Rashifal", route: "/rashifal", purpose: "Daily horoscope by moon sign" },
      { name: "Lucky", route: "/lucky", purpose: "Lucky color, number, gemstone, mantra", api: "GET /api/lucky/today" },
      { name: "Remedies", route: "/remedies", purpose: "Planet-wise mantra, daan, upay" },
      { name: "Daily Alerts", route: "/daily-alerts", purpose: "Personalized alert cards", api: "POST /api/daily_alerts" },
      { name: "Risk Radar", route: "/dasha-risk", purpose: "24h + 7-day dasha/transit risk", api: "GET /api/risk-radar" },
      { name: "Personalization", route: "/personalization", purpose: "Life area snapshot cards" },
    ],
  },
  {
    id: "love",
    title: "Love & Marriage",
    emoji: "❤️",
    description: "Love Reality + Kundli Milan — Basic | Pro toggle.",
    items: [
      {
        name: "Relationship Hub",
        route: "/relationship",
        purpose: "Love Reality vs Kundli Milan choose karo",
      },
      {
        name: "Love Reality (Basic)",
        route: "/love-reality",
        purpose: "4 tools: compat, breakup, loyalty, future outcome",
        api: "POST /api/love-compatibility, breakup-chances, loyalty-check, future-outcome",
        plan: "Free",
      },
      {
        name: "Love Reality Pro",
        route: "/love-reality-pro",
        purpose: "Founder-verified couple PDF order",
        fields: ["P1/P2 birth (profiles se)", "PDF language", "Priority delivery (12h vs 24–48h)"],
        api: "POST /api/love-reality/human-order",
        price: "₹499 (+₹300 urgent)",
      },
      {
        name: "Love Pro Report Reader",
        route: "/love-reality-pro-report",
        purpose: "In-app Pro report + PDF download",
        api: "POST /api/love-reality/pro-report",
      },
      {
        name: "Kundli Milan (Basic)",
        route: "/kundli-milan",
        purpose: "36-guna milan, synastry, basic PDF",
        api: "POST /api/kundli-milan",
        plan: "Free",
      },
      {
        name: "Kundli Milan Pro",
        route: "/kundli-milan-pro",
        purpose: "Founder-verified marriage PDF",
        fields: ["Couple birth data", "PDF language", "Priority delivery"],
        api: "POST /api/kundli-milan/human-order",
        price: "₹699 (+₹300 urgent)",
      },
      {
        name: "Milan Result",
        route: "/kundli-milan-result",
        purpose: "Milan score detail view",
      },
    ],
  },
  {
    id: "lifemap",
    title: "Life Map Domains",
    emoji: "🗺️",
    description: "Career, health, finance deep analysis.",
    items: [
      { name: "Career", route: "/career", purpose: "Career analysis — deep unlock paid", api: "POST /api/career-analysis", plan: "Pro deep", price: "₹1 (dev test)" },
      { name: "Health", route: "/health", purpose: "Health analysis — Pro sections gated", api: "POST /api/health-analysis", plan: "Pro" },
      { name: "Finance", route: "/finance", purpose: "Wealth analysis — Pro sections gated", api: "POST /api/finance-analysis", plan: "Pro" },
      { name: "6-Month Future", route: "/six-month-future", purpose: "Category-wise 6-month outlook", api: "POST /api/future-6months", plan: "Pro" },
    ],
  },
  {
    id: "vastu",
    title: "Vastu & Property",
    emoji: "🏠",
    description: "Residential, commercial, floor plan scans.",
    items: [
      { name: "AstroVastu Hub", route: "/astrovastu", purpose: "Free vs Pro vs My Reports chooser" },
      { name: "Free Vastu", route: "/vastu", purpose: "Residential compass + room guide", plan: "Free" },
      { name: "AstroVastu Basic", route: "/astrovastu-basic", purpose: "Basic residential scan", api: "POST /api/astrovastu-basic", plan: "Subscription" },
      {
        name: "AstroVastu Pro",
        route: "/astrovastu-pro",
        purpose: "Room photos + floor plan + expert review",
        fields: ["Room photos", "Floor plan PDF", "North orientation", "Property name"],
        api: "POST /api/astrovastu-pro",
        price: "₹99–₹4,999 (SKU based)",
      },
      {
        name: "Business Vastu",
        route: "/business-vastu",
        purpose: "Shop/office/factory — photos + floor plan",
        fields: [
          "Business type (shop/office/factory)",
          "Premise name",
          "Room photos (up to 6)",
          "Floor plan PDF + north",
          "Optional partner kundlis (3)",
        ],
        api: "POST /api/business-vastu/submit-order",
        price: "₹999–₹2,999 lifetime",
      },
    ],
  },
  {
    id: "reports",
    title: "Paid Reports & Products",
    emoji: "📄",
    description: "One-time PDF reports aur gemstones.",
    items: [
      {
        name: "Life Mastery (Numerology)",
        route: "/numerology",
        purpose: "12-section numerology PDF",
        fields: ["Mobile number", "PDF language", "Priority delivery"],
        api: "POST /api/numerology-report/create-order",
        price: "₹499 (+₹300 priority)",
      },
      {
        name: "Face Reading Pro",
        route: "/face-reading-upload",
        purpose: "3-angle face photos → PDF",
        fields: ["Front/left/right photos", "Age", "Gender", "Report language"],
        api: "POST /api/face-reading-report/create-order",
        price: "₹299",
      },
      {
        name: "Gemstones",
        route: "/gemstones",
        purpose: "Navratna catalog (Pukhraj, Emerald…)",
      },
      {
        name: "Gemstone Buy",
        route: "/gemstone-buy",
        purpose: "SKU, ratti, self vs referral checkout",
        fields: ["Product + ratti", "Self-buy or referral", "Referral code"],
        api: "POST /api/gemstone/create-order",
        price: "MRP per ratti",
      },
      {
        name: "My Reports",
        route: "/my-reports",
        purpose: "Saved PDFs — Milan, Love, Numerology, Vastu, Face",
        api: "GET /api/my-reports",
      },
    ],
  },
  {
    id: "billing",
    title: "Subscription & Payments",
    emoji: "💳",
    description: "Plans, checkout, history.",
    items: [
      {
        name: "Subscription",
        route: "/subscription",
        purpose: "Basic / Pro plans, 7-day trial",
        price: "Trial ₹1 · Basic ₹199/mo · Pro ₹499/mo",
        api: "POST /api/payment/create-order",
      },
      {
        name: "Payment WebView",
        route: "/payment-webview",
        purpose: "Razorpay/Cashfree — sab paid flows",
        fields: ["Plan/cycle or SKU", "Amount", "Customer name/email/phone"],
      },
      { name: "Payment History", route: "/payment-history", purpose: "Purchase history", api: "GET /api/user/:id/purchases" },
      { name: "Delete Account", route: "/delete-account", purpose: "Account delete", fields: ['Type "DELETE" to confirm'] },
    ],
  },
  {
    id: "legal",
    title: "Legal & About",
    emoji: "📋",
    description: "Terms, privacy, support.",
    items: [
      { name: "About", route: "/about", purpose: "Version, support email, cosmiclens.app link" },
      { name: "Legal", route: "/legal", purpose: "Legal hub" },
      { name: "Privacy", route: "/privacy", purpose: "Privacy policy" },
      { name: "Terms", route: "/terms", purpose: "Terms of service" },
      { name: "Refund", route: "/refund", purpose: "Refund policy" },
      { name: "Disclaimer", route: "/disclaimer", purpose: "Astrology disclaimer" },
    ],
  },
  {
    id: "admin",
    title: "Admin Dashboard Tabs",
    emoji: "🛠️",
    description: "Internal ops — http://127.0.0.1:5174",
    items: [
      { name: "Dashboard", purpose: "Users, revenue, Pro count, plan distribution", api: "GET /api/admin/dashboard" },
      { name: "Transactions", purpose: "Paid orders, CSV export", api: "GET /api/admin/transactions" },
      { name: "Users", purpose: "Search, profiles, purchases, Give Pro, Delete", api: "GET /api/admin/users" },
      { name: "Gmail Logins", purpose: "Sign-in history, delete account", api: "GET /api/admin/login-activity" },
      { name: "Love Reality Orders", purpose: "Founder PDF queue — couple, lang, priority", api: "GET /api/admin/love-reality-orders" },
      { name: "Business Vastu", purpose: "Photos, floor plan, north — expandable detail", api: "GET /api/admin/business-vastu-orders" },
      { name: "PDF AI Costs", purpose: "OpenAI tokens, INR per PDF generation", api: "GET /api/admin/pdf-generations" },
      { name: "Ask Q&A", purpose: "Questions, answers, full LLM chart context", api: "GET /api/admin/ask-questions" },
    ],
  },
];

export const STATS = {
  mobileScreens: 70,
  catalogSections: CATALOG_SECTIONS.length,
  catalogItems: CATALOG_SECTIONS.reduce((n, s) => n + s.items.length, 0),
  apps: PROJECT_APPS.length,
  paidProducts: 12,
};
