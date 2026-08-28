/**
 * Public website legal text (Privacy + Terms).
 * Kept in sync with artifacts/cosmic-lens-mobile/lib/legalPolicies.ts
 */

export const LEGAL_META = {
  lastUpdated: "28 August 2026",
  appName: "Cosmic Lens",
  operator: "Cosmic Lens",
  country: "India",
  supportEmail: "supportcosmiclens@gmail.com",
  website: "https://admin.coosmic.icu",
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

export const privacyPolicyDoc: LegalDoc = {
  title: "Privacy Policy",
  subtitle: "How we collect, use, and protect your information",
  intro:
    `${LEGAL_META.operator} ("we", "us", "our") operates the ${LEGAL_META.appName} mobile application, website at ${LEGAL_META.website}, and related services (the "Service"), available on Android, iOS, and web. This Privacy Policy explains what personal data we collect, why we collect it, how long we keep it, whom we share it with, and your rights under applicable law, including India's Digital Personal Data Protection Act, 2023 (DPDP Act). By creating an account or using the Service, you agree to this Policy.`,
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
          text: "User-generated & computed content — kundli charts, dasha timelines, dosha reports, numerology inputs, compatibility (Kundli Milan) parameters, Jyotish Q&A history, AstroVastu / Business Vastu scan inputs, Face Reading photos, floor-plan and room photos, generated PDF reports, and items saved to “My Reports” on your device.",
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
        {
          type: "bullet",
          text: "Instagram interactions — if you comment or direct-message our official Instagram business account (@astro_super_science) to request free reel answers, we receive data from Meta Platforms (Instagram) such as your Instagram-scoped user ID, username (when permitted by Meta), comment or message text, media/reel identifiers, and whether you follow our account. We do not receive or store your Instagram password.",
        },
      ],
    },
    {
      title: "2. How We Use Your Information",
      blocks: [
        { type: "bullet", text: "Create and maintain your account and saved profiles." },
        { type: "bullet", text: "Compute and display astrological, numerological, Vastu, Panchang, Muhurat, and related reports you request." },
        { type: "bullet", text: "Process one-time purchases, Cosmic Packs, and other payments through Razorpay." },
        { type: "bullet", text: "Deliver digital reports (including PDF downloads) and restore entitlements after payment." },
        { type: "bullet", text: "Enforce fair-use limits (e.g. daily Jyotish question quotas by plan)." },
        { type: "bullet", text: "Send optional reminders (horoscope, Panchang, Muhurat) if you opt in — you can disable notifications in device or app settings." },
        { type: "bullet", text: "Detect fraud, abuse, and security incidents; comply with law and valid government requests." },
        { type: "bullet", text: "Improve the Service through aggregated, non-identifying analytics." },
        {
          type: "bullet",
          text: "Instagram free answers — verify that you follow our Instagram account before sending unlock codes via Instagram direct message, match your comment or message to pre-published answers, and deliver the corresponding answer inside the Cosmic Lens app when you enter a valid unlock code.",
        },
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
        {
          type: "bullet",
          text: "Meta Platforms (Instagram / Facebook) — when you interact with our Instagram business account, we use Meta's Instagram APIs to receive comments and messages, verify follow status, and send automated direct messages (e.g. unlock codes). Data is processed according to Meta's terms and privacy policies.",
        },
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
          text: "Face Reading and Vastu features require you to upload photos. These are used solely to generate your requested report. We do not use Face Reading photos for unrelated advertising or sale to third parties.",
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
          text: "We keep your account and profile data while your account is active. If you request account deletion, we delete or anonymise personal data within 30 days, except where we must retain records for legal, tax, or dispute resolution. Instagram unlock codes and related logs are kept only as long as needed for security and abuse prevention.",
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
        { type: "p", text: "Subject to applicable law, you may access, correct, delete, or withdraw consent for optional processing. Contact us at " + LEGAL_META.supportEmail + ". We respond within 30 days." },
      ],
    },
    {
      title: "9. Children",
      blocks: [
        {
          type: "p",
          text: "The Service is not directed to children under 13. Users aged 13–17 should use the Service only with parent or guardian consent.",
        },
      ],
    },
    {
      title: "10. Changes to This Policy",
      blocks: [
        {
          type: "p",
          text: "We may update this Policy from time to time. The “Last updated” date will change accordingly. Material changes will be notified in-app or by email where required.",
        },
      ],
    },
    {
      title: "11. Contact & Grievance Officer",
      blocks: [
        { type: "bullet", text: `Email: ${LEGAL_META.supportEmail}` },
        { type: "bullet", text: `Website: ${LEGAL_META.website}` },
        {
          type: "bullet",
          text: `${LEGAL_META.grievanceOfficer}: contact ${LEGAL_META.supportEmail}. We acknowledge privacy complaints within ${LEGAL_META.grievanceResponseDays} days.`,
        },
      ],
    },
  ],
};

export const termsOfServiceDoc: LegalDoc = {
  title: "Terms of Service",
  subtitle: "Rules for using Cosmic Lens",
  intro:
    `These Terms of Service ("Terms") are a binding agreement between you and ${LEGAL_META.operator} for use of the ${LEGAL_META.appName} application, website, and related services (the "Service"). If you do not agree, do not use the Service.`,
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
          text: "Cosmic Lens provides digital astrology, numerology, Vastu, Panchang, Muhurat, compatibility, Cosmic Intelligence Q&A, and related spiritual guidance content via mobile and web.",
        },
        {
          type: "bullet",
          text: "Free Instagram Answers — you may comment or message our official Instagram account with keywords shown in reels; after verified follow, we may send a one-time unlock code via Instagram DM to access the matching pre-written answer inside the app.",
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
        { type: "bullet", text: "Notify us promptly of unauthorised access at " + LEGAL_META.supportEmail + "." },
      ],
    },
    {
      title: "4. Payments & Digital Products",
      blocks: [
        {
          type: "p",
          text: `Paid products are processed by ${LEGAL_META.paymentProcessor}. Prices are shown in INR at checkout. Digital goods are delivered in-app after successful payment.`,
        },
      ],
    },
    {
      title: "5. Acceptable Use",
      blocks: [
        { type: "p", text: "You agree NOT to abuse free tiers, scrape our servers, upload others' data without consent, or resell our reports commercially without permission." },
      ],
    },
    {
      title: "6. Disclaimers & Liability",
      blocks: [
        {
          type: "p",
          text: 'The Service is provided "as is" without warranties of accuracy or uninterrupted availability. To the maximum extent permitted by law, our liability is limited to the amount you paid for the specific product giving rise to the claim in the prior 12 months, or ₹1,000, whichever is greater.',
        },
      ],
    },
    {
      title: "7. Governing Law",
      blocks: [
        { type: "p", text: "These Terms are governed by the laws of India. Courts in India shall have exclusive jurisdiction, subject to applicable consumer protection laws." },
      ],
    },
    {
      title: "8. Contact",
      blocks: [
        { type: "bullet", text: `Support: ${LEGAL_META.supportEmail}` },
        { type: "bullet", text: `Website: ${LEGAL_META.website}` },
        { type: "bullet", text: `Privacy Policy: ${LEGAL_META.website}/privacy` },
      ],
    },
  ],
};
