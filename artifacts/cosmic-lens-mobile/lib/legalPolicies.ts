/**
 * Cosmic Lens — legal policy text (English).
 * Used by Privacy, Terms, Refund, and Disclaimer screens for app + payment-gateway compliance.
 */

export const LEGAL_META = {
  lastUpdated: "23 May 2026",
  appName: "Cosmic Lens",
  operator: "Cosmic Lens",
  country: "India",
  supportEmail: "support@cosmiclens.app",
  website: "https://cosmiclens.app",
  paymentProcessor: "Razorpay Software Private Limited",
  grievanceOfficer: "Grievance Officer — Cosmic Lens",
  grievanceResponseDays: 30,
} as const;

export type LegalBlock =
  | { type: "p"; text: string }
  | { type: "bullet"; text: string }
  | { type: "callout"; text: string; tone?: "info" | "warn" | "danger" };

export type LegalSection = { title: string; blocks: LegalBlock[] };

export type LegalDoc = {
  title: string;
  subtitle?: string;
  intro?: string;
  topCallout?: { text: string; tone?: "info" | "warn" | "danger" };
  sections: LegalSection[];
};

// ─── Privacy Policy ───────────────────────────────────────────────────────────

export const privacyPolicyDoc: LegalDoc = {
  title: "Privacy Policy",
  subtitle: "How we collect, use, and protect your information",
  intro:
    `${LEGAL_META.operator} ("we", "us", "our") operates the ${LEGAL_META.appName} mobile application and related services (the "Service"), available on Android, iOS, and web. This Privacy Policy explains what personal data we collect, why we collect it, how long we keep it, whom we share it with, and your rights under applicable law, including India's Digital Personal Data Protection Act, 2023 (DPDP Act). By creating an account or using the Service, you agree to this Policy.`,
  topCallout: {
    tone: "info",
    text: "We do not sell your personal data. We do not share your birth chart (kundli), chat history, or uploaded photos with advertisers for targeted advertising.",
  },
  sections: [
    {
      title: "1. Information We Collect",
      blocks: [
        { type: "p", text: "We collect only what is needed to run the Service:" },
        {
          type: "bullet",
          text: "Account data — name, email address, mobile number (if used for login), profile photo (optional), language preference, and authentication identifiers (including Google Sign-In ID if you choose that method). Passwords are hashed with scrypt; we never store plain-text passwords.",
        },
        {
          type: "bullet",
          text: "Birth & astrology profile data — full name, date of birth, time of birth, place of birth (city/coordinates), gender, and saved family profiles. This is required to compute Vedic kundli, dashas, compatibility, muhurat, and personalised reports.",
        },
        {
          type: "bullet",
          text: "User-generated & computed content — kundli charts, dasha timelines, dosha reports, numerology inputs, compatibility (Kundli Milan) parameters, Jyotish Q&A history, AstroVastu / Business Vastu scan inputs, Face Reading photos (front/left/right selfies), floor-plan and room photos, generated PDF reports, and items saved to “My Reports” on your device.",
        },
        {
          type: "bullet",
          text: "Payment & transaction data — order ID, product/plan purchased, amount (INR), payment status, and timestamps. Card numbers, UPI PINs, CVVs, and full bank account numbers are processed only by our payment partner; we do not store them.",
        },
        {
          type: "bullet",
          text: "Device & technical data — device model, operating system, app version, language, time zone, IP address (for security and fraud prevention), crash logs, and anonymous usage metrics to fix bugs and improve performance.",
        },
        {
          type: "bullet",
          text: "Communications — emails or in-app messages you send to support, and optional push-notification tokens if you enable notifications.",
        },
      ],
    },
    {
      title: "2. How We Use Your Information",
      blocks: [
        { type: "bullet", text: "Create and maintain your account and saved profiles." },
        { type: "bullet", text: "Compute and display astrological, numerological, Vastu, Panchang, Muhurat, and related reports you request." },
        { type: "bullet", text: "Process one-time purchases and subscription payments through Razorpay." },
        { type: "bullet", text: "Deliver digital reports (including PDF downloads) and restore entitlements after payment." },
        { type: "bullet", text: "Enforce fair-use limits (e.g. daily Jyotish question quotas by plan)." },
        { type: "bullet", text: "Send optional reminders (horoscope, Panchang, Muhurat) if you opt in — you can disable notifications in device or app settings." },
        { type: "bullet", text: "Detect fraud, abuse, and security incidents; comply with law and valid government requests." },
        { type: "bullet", text: "Improve the Service through aggregated, non-identifying analytics." },
      ],
    },
    {
      title: "3. Legal Bases (India & General)",
      blocks: [
        {
          type: "p",
          text: "We process personal data based on: (a) your consent when you sign up and use features that need birth data or photos; (b) performance of our contract with you to provide the Service; (c) legitimate interests such as security and product improvement, where not overridden by your rights; and (d) legal obligations (e.g. tax and payment records).",
        },
      ],
    },
    {
      title: "4. Third-Party Service Providers",
      blocks: [
        { type: "p", text: "We share the minimum necessary data with trusted processors who help us operate the Service:" },
        { type: "bullet", text: "Google Sign-In / Google Play services — authentication and app distribution (subject to Google's policies)." },
        { type: "bullet", text: `${LEGAL_META.paymentProcessor} — payment collection via UPI, cards, and net banking (PCI-DSS compliant).` },
        { type: "bullet", text: "Cloud hosting & database providers — encrypted storage of account and report data, primarily in India where practicable." },
        { type: "bullet", text: "Expo / push notification infrastructure — delivery of notification tokens only; message content is composed by us." },
        { type: "bullet", text: "Cloud computation providers — encrypted hosting and processing of chart data and report generation; no sale of your identity to advertisers." },
        { type: "p", text: "Each provider is bound by contract to protect data and use it only for the stated purpose. Their own privacy policies also apply." },
      ],
    },
    {
      title: "5. Photos, Biometrics & Sensitive Data",
      blocks: [
        {
          type: "p",
          text: "Face Reading and Vastu features require you to upload photos. These are used solely to generate your requested report. We do not use Face Reading photos for unrelated advertising or sale to third parties. Face geometry may be analysed algorithmically; we do not claim government-ID-level biometric verification.",
        },
        {
          type: "callout",
          tone: "warn",
          text: "Do not upload photos of other people without their consent. Do not upload illegal or explicit content.",
        },
      ],
    },
    {
      title: "6. Data Retention",
      blocks: [
        {
          type: "p",
          text: "We keep your account and profile data while your account is active. If you request account deletion, we delete or anonymise personal data within 30 days, except where we must retain records for legal, tax, or dispute resolution (e.g. payment invoices up to 7 years under Indian law). Server logs and backups may persist briefly before rotation.",
        },
        {
          type: "p",
          text: "Reports saved locally in “My Reports” on your device remain under your control until you delete the app or clear app data.",
        },
      ],
    },
    {
      title: "7. Security",
      blocks: [
        { type: "bullet", text: "TLS encryption for data in transit." },
        { type: "bullet", text: "Hashed passwords and per-user API keys for authenticated requests." },
        { type: "bullet", text: "Restricted access to production systems for authorised personnel only." },
        { type: "p", text: "No method of transmission over the Internet is 100% secure; we cannot guarantee absolute security." },
      ],
    },
    {
      title: "8. Your Rights",
      blocks: [
        { type: "p", text: "Subject to applicable law, you may:" },
        { type: "bullet", text: "Access and review personal data we hold about you." },
        { type: "bullet", text: "Correct inaccurate birth or profile information in the app." },
        { type: "bullet", text: "Withdraw consent for optional processing (e.g. notifications)." },
        { type: "bullet", text: "Request deletion of your account and associated server-side data." },
        { type: "bullet", text: "Lodge a complaint with the Data Protection Board of India if you believe your rights are violated." },
        {
          type: "p",
          text: `Contact us at ${LEGAL_META.supportEmail} to exercise these rights. We respond within 30 days.`,
        },
      ],
    },
    {
      title: "9. Children",
      blocks: [
        {
          type: "p",
          text: "The Service is not directed to children under 13. We do not knowingly collect data from children under 13. Users aged 13–17 should use the Service only with parent or guardian consent. Contact us if you believe a child has provided data without consent.",
        },
      ],
    },
    {
      title: "10. International Transfers",
      blocks: [
        {
          type: "p",
          text: "The Service is operated from India. If you access it from outside India, your data may be processed in India or where our subprocessors operate, under safeguards consistent with this Policy.",
        },
      ],
    },
    {
      title: "11. Changes to This Policy",
      blocks: [
        {
          type: "p",
          text: "We may update this Policy from time to time. The “Last updated” date will change accordingly. Material changes will be notified in-app or by email where required.",
        },
      ],
    },
    {
      title: "12. Contact & Grievance Officer",
      blocks: [
        { type: "bullet", text: `Email: ${LEGAL_META.supportEmail}` },
        { type: "bullet", text: `Website: ${LEGAL_META.website}` },
        {
          type: "bullet",
          text: `${LEGAL_META.grievanceOfficer}: contact ${LEGAL_META.supportEmail}. We acknowledge privacy complaints within ${LEGAL_META.grievanceResponseDays} days and work to resolve them promptly.`,
        },
      ],
    },
  ],
};

// ─── Terms of Service ─────────────────────────────────────────────────────────

export const termsOfServiceDoc: LegalDoc = {
  title: "Terms of Service",
  subtitle: "Rules for using Cosmic Lens",
  intro:
    `These Terms of Service ("Terms") are a binding agreement between you and ${LEGAL_META.operator} for use of the ${LEGAL_META.appName} application and related services (the "Service"). If you do not agree, do not use the Service.`,
  sections: [
    {
      title: "1. Eligibility",
      blocks: [
        { type: "bullet", text: "You must be at least 13 years old (18+ recommended for independent purchases)." },
        { type: "bullet", text: "If you are under 18, you confirm you have parent/guardian permission to use the Service and make purchases." },
        { type: "bullet", text: "You agree that birth details and other information you provide are accurate to the best of your knowledge." },
      ],
    },
    {
      title: "2. Description of the Service",
      blocks: [
        {
          type: "p",
          text: "Cosmic Lens provides digital astrology, numerology, Vastu, Panchang, Muhurat, compatibility, and related wellness/spiritual content, including but not limited to:",
        },
        { type: "bullet", text: "Vedic kundli, dasha, dosha, planet positions, and transits" },
        { type: "bullet", text: "Kundli Milan (marriage compatibility), Love Reality, and couple reports" },
        { type: "bullet", text: "Numerology (Life Mastery and related reports)" },
        { type: "bullet", text: "Face Reading PRO (photo-based reports)" },
        { type: "bullet", text: "Free Vastu compass & guides; AstroVastu PRO (room photo and floor-plan scans); Business Vastu" },
        { type: "bullet", text: "Panchang, Muhurat, health/wealth/career insights, six-month timelines, Cosmic Portrait" },
        { type: "bullet", text: "“Ask” / Jyotish Q&A powered by our structured astrology engine (rule-based chart analysis, not AI)" },
        { type: "bullet", text: "Subscription plans and one-time digital report purchases" },
        {
          type: "p",
          text: "Calculations are performed using rule-based astronomical and astrological computation methods. Some astronomical data, timezone data, or calculation libraries may be provided by third-party open-source or licensed components.",
        },
        {
          type: "callout",
          tone: "warn",
          text: "All astrological content is interpretive and for personal insight and entertainment. It is not professional medical, legal, financial, or psychological advice.",
        },
      ],
    },
    {
      title: "3. Account & Security",
      blocks: [
        { type: "bullet", text: "You are responsible for safeguarding your login credentials." },
        { type: "bullet", text: "You may not share, sell, or transfer your account." },
        { type: "bullet", text: "Notify us promptly of unauthorised access at " + LEGAL_META.supportEmail + "." },
        { type: "bullet", text: "We may suspend or terminate accounts for fraud, abuse, chargebacks without contact, or violation of these Terms." },
      ],
    },
    {
      title: "4. Subscription Plans (Recurring)",
      blocks: [
        { type: "p", text: "Optional auto-renewing subscriptions may include:" },
        { type: "bullet", text: "7-day trial (introductory, one-time per user where offered) — from ₹1" },
        { type: "bullet", text: "Basic — ₹199/month or ₹1,799/year (features as shown in-app)" },
        { type: "bullet", text: "Pro — ₹499/month (features as shown in-app; monthly billing)" },
        {
          type: "p",
          text: "Subscriptions renew automatically unless cancelled at least 24 hours before the end of the current billing period. Manage or cancel via Profile → Subscription or by emailing support. After cancellation, access continues until the period ends; no further charges apply.",
        },
      ],
    },
    {
      title: "5. One-Time Digital Purchases (Non-Recurring)",
      blocks: [
        { type: "p", text: "The following are one-time charges unless stated otherwise in-app. Prices are in Indian Rupees (₹) and may include GST:" },
        { type: "bullet", text: "Face Reading PRO report — ₹299 per unlock (per eligible session/parameters)" },
        { type: "bullet", text: "Life Mastery / Numerology report — price shown at checkout" },
        { type: "bullet", text: "Couple / compatibility reports — price shown at checkout" },
        { type: "bullet", text: "AstroVastu room photo scans — ₹99 (1 room), ₹249 (3 rooms), ₹399 (5 rooms)" },
        { type: "bullet", text: "AstroVastu full floor-plan scans — Home ₹799 · Shop ₹1,499 · Office ₹2,499 · Factory ₹4,999" },
        { type: "bullet", text: "Other premium unlocks as displayed before payment" },
        {
          type: "p",
          text: "One-time purchases grant access to the described digital deliverable. They do not auto-renew. Entitlements are tied to your account and, where applicable, to specific report parameters or property names shown at purchase.",
        },
      ],
    },
    {
      title: "6. Payments",
      blocks: [
        {
          type: "p",
          text: `All payments are processed by ${LEGAL_META.paymentProcessor}. By paying, you also agree to Razorpay's applicable terms. We are a merchant of digital services; your bank/UPI statement may show our business name or Razorpay as payment facilitator.`,
        },
        { type: "bullet", text: "Prices shown in-app are final unless a technical error is confirmed." },
        { type: "bullet", text: "Failed payments are not charged; pending authorisations reverse per RBI timelines (typically 5–7 business days)." },
      ],
    },
    {
      title: "7. Digital Delivery",
      blocks: [
        {
          type: "p",
          text: "Digital reports and premium features are delivered in-app (and optionally as downloadable PDFs) after successful payment and processing. Delivery times are usually immediate but may take longer during high load or maintenance.",
        },
      ],
    },
    {
      title: "8. Refunds",
      blocks: [
        {
          type: "p",
          text: "Refunds are governed by our Refund & Cancellation Policy (linked in About). In summary: digital goods are generally non-refundable once successfully delivered, except for duplicate charges, technical non-delivery, or other cases described in that policy.",
        },
      ],
    },
    {
      title: "9. Acceptable Use",
      blocks: [
        { type: "p", text: "You agree NOT to:" },
        { type: "bullet", text: "Use the Service for illegal, harmful, or fraudulent purposes." },
        { type: "bullet", text: "Scrape, reverse-engineer, or overload our servers." },
        { type: "bullet", text: "Use bots to abuse free tiers or trials." },
        { type: "bullet", text: "Upload others' photos or data without consent." },
        { type: "bullet", text: "Resell or republish our reports commercially without written permission." },
      ],
    },
    {
      title: "10. Intellectual Property",
      blocks: [
        {
          type: "p",
          text: "The app, branding, software, text, and report formats are owned by Cosmic Lens or licensors. You receive a limited, personal, non-transferable licence to use the Service and download reports for personal use only.",
        },
      ],
    },
    {
      title: "11. Disclaimers & Limitation of Liability",
      blocks: [
        {
          type: "p",
          text: 'The Service is provided "as is" without warranties of accuracy, fitness for a particular purpose, or uninterrupted availability. We do not guarantee that predictions will occur.',
        },
        {
          type: "p",
          text: "To the maximum extent permitted by law, our total liability for any claim is limited to the amount you paid us for the specific product giving rise to the claim in the 12 months before the claim, or ₹1,000, whichever is greater. We are not liable for indirect or consequential damages.",
        },
      ],
    },
    {
      title: "12. Termination",
      blocks: [
        {
          type: "p",
          text: "You may stop using the Service at any time. We may terminate or suspend access for breach of these Terms. Provisions that by nature should survive (payment disputes, liability limits, governing law) will survive.",
        },
      ],
    },
    {
      title: "13. Governing Law & Disputes",
      blocks: [
        {
          type: "p",
          text: "These Terms are governed by the laws of India. Courts in India shall have exclusive jurisdiction, subject to applicable consumer protection laws that may give you rights in your place of residence.",
        },
      ],
    },
    {
      title: "14. Changes & Contact",
      blocks: [
        { type: "p", text: "We may update these Terms; continued use after notice constitutes acceptance where permitted by law." },
        { type: "bullet", text: `Support: ${LEGAL_META.supportEmail}` },
        { type: "bullet", text: `Website: ${LEGAL_META.website}` },
      ],
    },
  ],
};

// ─── Refund & Cancellation ────────────────────────────────────────────────────

export const refundPolicyDoc: LegalDoc = {
  title: "Refund & Cancellation Policy",
  subtitle: "Subscriptions, one-time purchases & how to get help",
  intro:
    `This policy explains how to cancel subscriptions, when refunds are available for purchases made in ${LEGAL_META.appName}, and how to contact us. It applies to all payments processed via ${LEGAL_META.paymentProcessor}.`,
  topCallout: {
    tone: "info",
    text: "Please use the free trial (where offered) and review the product description before paying. One-time digital reports are delivered immediately after payment.",
  },
  sections: [
    {
      title: "1. Subscription Cancellation",
      blocks: [
        { type: "p", text: "Monthly and yearly subscriptions renew automatically until cancelled." },
        { type: "bullet", text: "Cancel in-app: Profile → Subscription → Cancel (or equivalent control)." },
        { type: "bullet", text: `Or email ${LEGAL_META.supportEmail} from your registered email with your account mobile/email.` },
        {
          type: "p",
          text: "After cancellation, premium access continues until the end of the current paid period. No further renewals will be charged. Cancelling does not automatically refund the current period unless a refund exception below applies.",
        },
      ],
    },
    {
      title: "2. One-Time Purchases (No Auto-Renewal)",
      blocks: [
        { type: "p", text: "The following are charged once only — they do not renew:" },
        { type: "bullet", text: "Face Reading PRO (₹299), Numerology / Life Mastery reports, Couple reports" },
        { type: "bullet", text: "AstroVastu room credits (₹99 / ₹249 / ₹399) and floor-plan unlocks (₹799–₹4,999)" },
        { type: "bullet", text: "Other one-time unlocks shown at checkout" },
        {
          type: "p",
          text: "Once the digital report is generated, downloaded, or marked as delivered in your account, the purchase is considered fulfilled. Refunds for change of mind are generally not provided for fulfilled digital goods, consistent with applicable consumer and RBI guidelines for digital products.",
        },
      ],
    },
    {
      title: "3. When We Grant Refunds",
      blocks: [
        { type: "p", text: "We will approve a full or partial refund (to the original payment method via Razorpay) when:" },
        { type: "bullet", text: "Duplicate charge — you were billed twice for the same order (we refund the duplicate)." },
        { type: "bullet", text: "Payment succeeded but the product was not activated and we cannot fix it within 72 hours." },
        { type: "bullet", text: "Technical failure — you could not access a paid report despite successful payment, and our support confirms the failure on our side." },
        { type: "bullet", text: "Unauthorized transaction — reported promptly with evidence; account may be secured pending review." },
        {
          type: "bullet",
          text: "First-time subscription refund — within 7 days of first paid subscription charge, if you used fewer than 5 premium features and contact us in good faith (one-time courtesy per user, at our discretion).",
        },
      ],
    },
    {
      title: "4. When Refunds Are Not Granted",
      blocks: [
        { type: "bullet", text: "You changed your mind after a report was successfully generated or downloaded." },
        { type: "bullet", text: "You disagree with astrological interpretation or prediction outcome (see Disclaimer)." },
        { type: "bullet", text: "Incorrect birth data entered by you (reports are based on data you provide)." },
        { type: "bullet", text: "You forgot to cancel before subscription renewal — we will cancel future renewals but typically do not refund the current period." },
        { type: "bullet", text: "Request made more than 30 days after payment (except where law requires otherwise)." },
        { type: "bullet", text: "Abuse of refund policy, repeated false claims, or chargeback fraud." },
      ],
    },
    {
      title: "5. How to Request a Refund",
      blocks: [
        { type: "p", text: `Email ${LEGAL_META.supportEmail} with:` },
        { type: "bullet", text: "Registered email or mobile number" },
        { type: "bullet", text: "Razorpay order ID / payment reference (from payment confirmation or Profile → payment history)" },
        { type: "bullet", text: "Product name (e.g. Face Reading PRO, Pro monthly, AstroVastu floor plan)" },
        { type: "bullet", text: "Brief reason and screenshots if applicable" },
        {
          type: "p",
          text: "We acknowledge requests within 3 business days. Approved refunds are initiated to your original payment method within 5–10 business days (bank/UPI processing times may vary).",
        },
      ],
    },
    {
      title: "6. Failed & Pending Payments",
      blocks: [
        {
          type: "p",
          text: "If payment fails, you are not charged. If your bank shows a pending debit, it usually auto-reverses within 5–7 business days per RBI rules. Contact your bank if it persists beyond 10 business days; we can share transaction references to assist.",
        },
      ],
    },
    {
      title: "7. Chargebacks",
      blocks: [
        {
          type: "callout",
          tone: "warn",
          text: "Please contact us before raising a bank chargeback. Unresolved chargebacks may lead to account suspension. We prefer to resolve issues directly and quickly.",
        },
      ],
    },
    {
      title: "8. Contact",
      blocks: [
        { type: "bullet", text: `Email: ${LEGAL_META.supportEmail}` },
        { type: "bullet", text: "Subject: Refund Request — [Order ID]" },
        { type: "bullet", text: `Website: ${LEGAL_META.website}` },
      ],
    },
  ],
};

// ─── Astrology Disclaimer ─────────────────────────────────────────────────────

export const disclaimerDoc: LegalDoc = {
  title: "Astrology & Wellness Disclaimer",
  subtitle: "Important limitations of Cosmic Lens content",
  intro:
    `Please read this disclaimer carefully before using ${LEGAL_META.appName}. By using the Service, you acknowledge that astrological, numerological, Vastu, and related outputs are interpretive and not guaranteed facts.`,
  topCallout: {
    tone: "warn",
    text: "Cosmic Lens is for spiritual exploration, self-reflection, cultural tradition, and entertainment. It is not a substitute for professional medical, legal, financial, or mental-health advice.",
  },
  sections: [
    {
      title: "1. Nature of Astrology & Related Disciplines",
      blocks: [
        {
          type: "p",
          text: "Vedic astrology (Jyotish), numerology, Vastu Shastra, Panchang, and Muhurat are traditional systems. Results depend on classical rules, astronomical calculations (including Lahiri ayanamsa where stated), and interpretation produced by Cosmic Lens's structured astrology engine (rule-based software coding — not artificial intelligence). Some astronomical data or calculation libraries may be provided by third-party open-source or licensed components. Results are not scientifically proven to predict specific future events.",
        },
      ],
    },
    {
      title: "2. No Guaranteed Outcomes",
      blocks: [
        {
          type: "p",
          text: "No score, dasha period, remedy, muhurat, compatibility percentage, Face Reading trait, or Vastu direction guarantee marriage, health, wealth, pregnancy, legal victory, or any particular result. Life outcomes depend on many factors including your choices, skills, environment, and chance.",
        },
      ],
    },
    {
      title: "3. Not Professional Advice",
      blocks: [
        { type: "p", text: "Always consult qualified professionals for important decisions:" },
        { type: "bullet", text: "Health — registered doctor; do not delay treatment based on app content." },
        { type: "bullet", text: "Mental health / crisis — licensed counsellor or psychiatrist; India: emergency 112, iCall 9152987821." },
        { type: "bullet", text: "Legal matters — advocate or qualified legal professional." },
        { type: "bullet", text: "Investments — SEBI-registered advisor; app content is not investment advice." },
        { type: "bullet", text: "Relationships — open communication and consent matter more than compatibility scores alone." },
      ],
    },
    {
      title: "4. Rule-Based Engine Output",
      blocks: [
        {
          type: "p",
          text: "“Ask” answers, report narratives, Vastu scans, Face Reading analysis, and other summaries are produced by Cosmic Lens's structured astrology engine — deterministic and rule-based software built on classical Jyotish principles, not artificial intelligence or chatbots. Output may contain errors, omissions, or culturally sensitive phrasing. It is not reviewed by a named human astrologer unless explicitly stated.",
        },
      ],
    },
    {
      title: "5. Birth Data & Photos",
      blocks: [
        {
          type: "p",
          text: "Kundli accuracy depends on correct date, time, and place of birth. Even a few minutes' error can change ascendant or divisional charts. Face Reading and Vastu scans depend on photo quality, lighting, and premises layout. Poor inputs produce poor outputs.",
        },
      ],
    },
    {
      title: "6. Remedies, Gemstones & Rituals",
      blocks: [
        {
          type: "p",
          text: "Suggested mantras, donations, fasting, gemstones, or rituals are drawn from tradition. We do not guarantee results. Consult a qualified guru or astrologer before adopting intensive remedies, especially gemstones and beeja mantras. Purchase gems only from trusted sources.",
        },
      ],
    },
    {
      title: "7. Vastu & Construction",
      blocks: [
        {
          type: "p",
          text: "Vastu suggestions are general guidance. Structural changes, demolition, or major construction should involve licensed architects and engineers and comply with local building laws.",
        },
      ],
    },
    {
      title: "8. Emergency",
      blocks: [
        {
          type: "callout",
          tone: "danger",
          text: "In a medical emergency or if you have thoughts of self-harm, contact local emergency services immediately. Do not rely on this app for crisis support.",
        },
      ],
    },
    {
      title: "9. Acceptance",
      blocks: [
        {
          type: "p",
          text: "By continuing to use Cosmic Lens, you confirm that you have read this disclaimer, understand its limitations, and will use the Service responsibly.",
        },
      ],
    },
  ],
};
