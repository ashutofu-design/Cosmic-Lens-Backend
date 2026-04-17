import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import LegalScreen, { Section, P, Bullet, Strong, Callout } from "@/components/LegalScreen";
import { useC } from "@/context/ThemeContext";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

function DocHeading({ icon, title }: { icon: keyof typeof Feather.glyphMap; title: string }) {
  const C = useC();
  const accent = C.isDark ? "#f59e0b" : "#7C3AED";
  return (
    <View style={d.wrap}>
      <View style={[d.line, { backgroundColor: C.border }]} />
      <View style={[d.pill, { backgroundColor: C.bgCard, borderColor: accent + "55" }]}>
        <Feather name={icon} size={14} color={accent} />
        <Text style={[d.title, { color: C.text }]}>{title}</Text>
      </View>
      <View style={[d.line, { backgroundColor: C.border }]} />
    </View>
  );
}

export default function LegalAndPoliciesScreen() {
  return (
    <LegalScreen
      title="Legal & Policies"
      subtitle="Privacy, terms, refunds & disclaimer"
      lastUpdated="17 April 2026"
    >
      {/* ═══════════════════════ PRIVACY POLICY ═══════════════════════ */}
      <DocHeading icon="shield" title="Privacy Policy" />

      <P>
        Cosmic Lens (“we”, “us”, “our”) respects your privacy. This Privacy Policy
        explains what personal information we collect when you use our mobile
        application and related services (the “Service”), how we use it, and the
        choices you have. By using Cosmic Lens you agree to the practices
        described below.
      </P>

      <Callout tone="info">
        We do <Strong>not</Strong> sell your personal data. We do not share your
        kundli, birth details, or chat history with advertisers.
      </Callout>

      <Section title="1. Information We Collect">
        <P><Strong>(a) Account information</Strong> — name, email address, mobile
        number (if you sign up with phone), Google account ID (if you use Google
        Sign-In). Stored securely with hashed passwords (scrypt).</P>

        <P><Strong>(b) Birth & profile data</Strong> — full name, date of birth,
        time of birth, place of birth, gender, and language preference. This is
        the minimum required to compute your Vedic kundli.</P>

        <P><Strong>(c) Generated content</Strong> — your kundli charts, dashas,
        compatibility reports, AI question/answer history, and saved profiles.</P>

        <P><Strong>(d) Payment information</Strong> — handled entirely by our
        payment processor Cashfree Payments. We only store the order ID, plan,
        amount, and success/failure status. We never store card numbers, UPI
        PINs, CVVs, or banking credentials.</P>

        <P><Strong>(e) Device & technical information</Strong> — device model, OS
        version, app version, language, time zone, and crash logs. Used purely
        for diagnostics.</P>
      </Section>

      <Section title="2. How We Use Your Information">
        <Bullet>To create and maintain your account.</Bullet>
        <Bullet>To compute your kundli, dashas, doshas, compatibility, and other astrological reports.</Bullet>
        <Bullet>To provide AI-based answers to your questions using only your kundli data — not your identity.</Bullet>
        <Bullet>To process subscription payments through Cashfree.</Bullet>
        <Bullet>To enforce daily question limits and fair-usage rules.</Bullet>
        <Bullet>To send you optional notifications (daily horoscope, panchang, muhurat reminders) — you can disable these in Settings.</Bullet>
        <Bullet>To prevent fraud, debug crashes, and improve service quality.</Bullet>
        <Bullet>To comply with legal obligations.</Bullet>
      </Section>

      <Section title="3. Third-Party Services">
        <P>We share the minimum necessary data with these trusted partners:</P>
        <Bullet><Strong>Google Sign-In</Strong> — verifies your identity if you choose Google login. We receive your name, email, and Google ID.</Bullet>
        <Bullet><Strong>Cashfree Payments (India)</Strong> — processes UPI, card, and net-banking transactions. PCI-DSS Level 1 compliant.</Bullet>
        <Bullet><Strong>Expo / Google Play Services</Strong> — push notification delivery only. No content is read by them.</Bullet>
        <Bullet><Strong>Cloud hosting (Replit / AWS)</Strong> — encrypted database storage in India region where possible.</Bullet>
        <P>These services have their own privacy policies which we encourage you to read.</P>
      </Section>

      <Section title="4. Data Retention">
        <P>We retain your account and kundli data for as long as your account is
        active. If you delete your account (see Section 7) we permanently erase
        your personal data within <Strong>30 days</Strong>, except where retention
        is legally required (e.g. tax invoices for 7 years under Indian law).</P>
      </Section>

      <Section title="5. Data Security">
        <Bullet>All API traffic is encrypted with TLS 1.2+.</Bullet>
        <Bullet>Passwords are hashed with scrypt (never stored in plain text).</Bullet>
        <Bullet>API access requires a per-user API key validated on every request.</Bullet>
        <Bullet>Database backups are encrypted at rest.</Bullet>
        <Bullet>Access to production data is restricted to authorised engineers.</Bullet>
      </Section>

      <Section title="6. Your Rights">
        <P>Under the Digital Personal Data Protection Act, 2023 (India) and
        comparable laws, you have the right to:</P>
        <Bullet>Access the personal data we hold about you.</Bullet>
        <Bullet>Correct inaccurate or outdated information.</Bullet>
        <Bullet>Withdraw consent and delete your account.</Bullet>
        <Bullet>Receive an export of your kundli data in JSON format.</Bullet>
        <Bullet>Lodge a complaint with the Data Protection Board of India.</Bullet>
        <P>To exercise any of these rights, email us at <Strong>support@cosmiclens.app</Strong>.</P>
      </Section>

      <Section title="7. Account Deletion">
        <P>You can delete your account at any time from{" "}
        <Strong>Profile → Delete Account</Strong>. Deletion is permanent and
        removes all profiles, kundlis, chat history, and personal data within
        30 days.</P>
      </Section>

      <Section title="8. Children">
        <P>Cosmic Lens is not directed to children under 13. We do not knowingly
        collect personal data from children. If you believe a child has created
        an account, please contact us and we will delete it promptly.</P>
      </Section>

      <Section title="9. International Users">
        <P>Cosmic Lens is operated from India. If you access the Service from
        outside India, your information will be transferred to and processed in
        India where data-protection laws may differ from your country.</P>
      </Section>

      <Section title="10. Changes to This Policy">
        <P>We may update this Privacy Policy from time to time. The “Last updated”
        date at the top will reflect the most recent changes. Material changes
        will be communicated in-app at least 7 days in advance.</P>
      </Section>

      <Section title="11. Contact Us">
        <P>For privacy-related questions, requests, or grievances:</P>
        <Bullet>Email: <Strong>support@cosmiclens.app</Strong></Bullet>
        <Bullet>Grievance Officer: Available within 30 days of complaint receipt</Bullet>
      </Section>

      {/* ═══════════════════════ TERMS OF SERVICE ═══════════════════════ */}
      <DocHeading icon="file-text" title="Terms of Service" />

      <P>
        These Terms of Service (“Terms”) govern your access to and use of the
        Cosmic Lens mobile application and related services (the “Service”). By
        creating an account, downloading, or using the Service, you accept these
        Terms. If you do not agree, please do not use the Service.
      </P>

      <Section title="1. Eligibility">
        <Bullet>You must be at least 13 years old to use Cosmic Lens.</Bullet>
        <Bullet>If you are under 18, you must have permission from a parent or guardian.</Bullet>
        <Bullet>You confirm that the information you provide (name, date, time, place of birth) is true and accurate. Inaccurate birth data will produce inaccurate astrological results.</Bullet>
      </Section>

      <Section title="2. Account & Security">
        <Bullet>You are responsible for keeping your login credentials safe.</Bullet>
        <Bullet>You may not share your account or use someone else’s account.</Bullet>
        <Bullet>Notify us immediately of any unauthorised access.</Bullet>
        <Bullet>We reserve the right to suspend accounts engaged in fraud, abuse, or violation of these Terms.</Bullet>
      </Section>

      <Section title="3. The Service">
        <P>Cosmic Lens provides Vedic-astrology computations including kundli,
        dashas, doshas, marriage compatibility, panchang, muhurat, numerology,
        vastu, lucky elements, and AI-based question answering. Calculations
        follow traditional Vedic principles (Lahiri ayanamsa) using accurate
        ephemeris data.</P>
      </Section>

      <Section title="4. Subscription Plans">
        <P>Cosmic Lens offers the following plans:</P>
        <Bullet><Strong>Free</Strong> — limited features, 1 AI question/day</Bullet>
        <Bullet><Strong>7-day Free Trial</Strong> — Basic features for new users, one-time only, no payment required</Bullet>
        <Bullet><Strong>Basic</Strong> — ₹199/month or ₹1,799/year, includes 10 AI questions/day and basic analysis</Bullet>
        <Bullet><Strong>Pro</Strong> — ₹399/month or ₹2,999/year, includes unlimited AI questions, full deep analysis, 6-month timeline, karmic insights, PDF reports</Bullet>
        <P>Subscriptions auto-renew at the end of each billing period unless
        cancelled at least 24 hours before renewal. You can cancel any time
        from <Strong>Profile → Subscription → Cancel</Strong> or by contacting
        support.</P>
      </Section>

      <Section title="5. Payments">
        <P>Payments are processed by Cashfree Payments. By making a purchase you
        agree to Cashfree’s terms in addition to ours. All prices are in Indian
        Rupees (₹) and inclusive of applicable GST.</P>
      </Section>

      <Section title="6. Refund Policy">
        <P>Please review our <Strong>Refund &amp; Cancellation</Strong> section
        below for full details. In summary, all sales are generally final, but
        refunds may be granted for technical failures, double-charges, or
        unused service within 7 days of payment.</P>
      </Section>

      <Section title="7. User Conduct — You agree NOT to">
        <Bullet>Use the Service for any illegal or fraudulent purpose.</Bullet>
        <Bullet>Reverse-engineer, decompile, or scrape the Service.</Bullet>
        <Bullet>Use bots, scripts, or automated tools to abuse free or trial features.</Bullet>
        <Bullet>Resell, sublicense, or republish content from the Service.</Bullet>
        <Bullet>Submit false birth data on behalf of another person without consent.</Bullet>
        <Bullet>Harass, threaten, or impersonate others.</Bullet>
      </Section>

      <Section title="8. Intellectual Property">
        <P>All content, design, code, branding, algorithms, and computed reports
        in the Service are the intellectual property of Cosmic Lens or its
        licensors. You receive a limited, non-exclusive, non-transferable licence
        to use the Service for personal, non-commercial purposes only.</P>
      </Section>

      <Section title="9. AI-Generated Answers">
        <P>The “Ask” feature uses rule-based and generative analysis of your
        kundli. AI answers are produced by software and may contain errors,
        ambiguities, or contradictions. They are <Strong>not</Strong> a
        substitute for professional advice.</P>
      </Section>

      <Section title="10. No Professional Advice">
        <Callout tone="warn">
          Cosmic Lens is for <Strong>spiritual and entertainment purposes only</Strong>.
          Astrological insights are <Strong>not</Strong> a substitute for
          professional medical, legal, financial, psychological, or relationship
          advice. Always consult qualified professionals for important life
          decisions.
        </Callout>
      </Section>

      <Section title="11. Disclaimers">
        <P>The Service is provided “as is” and “as available” without warranties
        of any kind, express or implied. We do not guarantee that astrological
        predictions will come true, that the Service will be error-free, or
        that it will be available at all times. Past performance of any
        prediction does not indicate future results.</P>
      </Section>

      <Section title="12. Limitation of Liability">
        <P>To the maximum extent permitted by law, Cosmic Lens, its officers,
        employees, and partners shall not be liable for any indirect, incidental,
        consequential, or punitive damages arising from your use of the Service.
        Our total liability for any claim is limited to the amount you paid us
        in the 12 months preceding the claim, or ₹1,000, whichever is greater.</P>
      </Section>

      <Section title="13. Termination">
        <P>You may stop using the Service at any time by deleting your account.
        We may suspend or terminate your access immediately if you violate these
        Terms or engage in conduct harmful to other users or the Service.</P>
      </Section>

      <Section title="14. Changes to Terms">
        <P>We may update these Terms periodically. Continued use of the Service
        after changes become effective constitutes acceptance of the new Terms.
        Material changes will be notified in-app at least 7 days in advance.</P>
      </Section>

      <Section title="15. Governing Law & Jurisdiction">
        <P>These Terms are governed by the laws of India. Any disputes arising
        out of or related to these Terms or the Service shall be subject to the
        exclusive jurisdiction of the courts in <Strong>your registered city</Strong>,
        India.</P>
      </Section>

      <Section title="16. Contact">
        <P>For questions about these Terms, email{" "}
        <Strong>support@cosmiclens.app</Strong>.</P>
      </Section>

      {/* ═══════════════════════ REFUND & CANCELLATION ═══════════════════════ */}
      <DocHeading icon="rotate-ccw" title="Refund & Cancellation" />

      <P>
        At Cosmic Lens we want every member to have a great experience. This
        policy explains when subscription fees are refundable and how to cancel
        your subscription.
      </P>

      <Callout tone="info">
        Use the <Strong>7-day Free Trial</Strong> before subscribing — it lets
        you experience Basic features at no cost so you can decide before
        paying.
      </Callout>

      <Section title="1. Subscription Cancellation">
        <P>You can cancel your monthly or yearly subscription at any time:</P>
        <Bullet>Open <Strong>Profile → Subscription</Strong> and tap “Cancel Subscription”.</Bullet>
        <Bullet>Or email <Strong>support@cosmiclens.app</Strong> from your registered email.</Bullet>
        <P>After cancellation, you keep premium access until the end of the
        current billing period. No further charges will be made.</P>
      </Section>

      <Section title="2. When Refunds Are Granted">
        <P>We will issue a full or pro-rated refund in these situations:</P>
        <Bullet><Strong>Double charge / duplicate payment</Strong> — full refund of the duplicate amount, processed within 5–7 business days.</Bullet>
        <Bullet><Strong>Payment succeeded but plan not activated</Strong> — full refund or manual plan activation, your choice.</Bullet>
        <Bullet><Strong>Technical failure preventing access</Strong> for more than 72 hours — pro-rated refund for unused days.</Bullet>
        <Bullet><Strong>Cancellation within 7 days of first paid subscription</Strong> if you have used <Strong>fewer than 5 paid features</Strong> — full refund (one-time per user).</Bullet>
      </Section>

      <Section title="3. When Refunds Are NOT Granted">
        <Bullet>Change of mind after the 7-day window.</Bullet>
        <Bullet>Astrological prediction did not come true — predictions are interpretive guidance, not guarantees (see Disclaimer).</Bullet>
        <Bullet>You forgot to cancel before auto-renewal — but we will cancel future renewals immediately on request.</Bullet>
        <Bullet>Partial-month refunds for monthly plans cancelled mid-cycle.</Bullet>
        <Bullet>Refunds for the Free or Trial plans (no payment was made).</Bullet>
        <Bullet>Refunds requested more than 30 days after payment.</Bullet>
      </Section>

      <Section title="4. How to Request a Refund">
        <P>Email <Strong>support@cosmiclens.app</Strong> with:</P>
        <Bullet>Your registered email address or mobile number</Bullet>
        <Bullet>The order ID (visible in Profile → Subscription → Payment History)</Bullet>
        <Bullet>Reason for the refund request</Bullet>
        <P>We respond to all refund requests within <Strong>3 business days</Strong>.
        Approved refunds are processed by Cashfree to your original payment
        method within <Strong>5–10 business days</Strong>.</P>
      </Section>

      <Section title="5. Failed Payments">
        <P>If a payment fails, no charge is made. If your bank shows a
        “pending” charge, it is automatically reversed within 5–7 business days
        per RBI guidelines. You do not need to contact us for these.</P>
      </Section>

      <Section title="6. Subscription Auto-Renewal">
        <P>Monthly and yearly plans renew automatically. We will send a
        reminder via email or in-app notification before each renewal. To stop
        renewal, simply cancel before the renewal date — no action will be
        charged.</P>
      </Section>

      <Section title="7. Chargebacks">
        <P>If you initiate a chargeback through your bank instead of contacting
        us first, your account will be suspended pending investigation. We
        always prefer to resolve issues directly — please email us first.</P>
      </Section>

      <Section title="8. Contact for Refunds">
        <Bullet>Email: <Strong>support@cosmiclens.app</Strong></Bullet>
        <Bullet>Subject line: “Refund Request — [Order ID]”</Bullet>
        <Bullet>Response time: within 3 business days</Bullet>
      </Section>

      {/* ═══════════════════════ ASTROLOGY DISCLAIMER ═══════════════════════ */}
      <DocHeading icon="alert-triangle" title="Astrology Disclaimer" />

      <Callout tone="warn">
        Cosmic Lens is intended for <Strong>spiritual exploration, self-reflection,
        and entertainment purposes only</Strong>. It is not a substitute for
        professional medical, legal, financial, psychological, or relationship
        advice.
      </Callout>

      <Section title="1. Nature of Astrology">
        <P>Vedic astrology (Jyotish) is an ancient art and philosophical
        tradition. The interpretations, predictions, dashas, doshas, muhurats,
        and remedies provided in Cosmic Lens reflect classical principles and
        modern algorithmic analysis. They are interpretive in nature and
        <Strong> not scientifically verifiable</Strong>.</P>
      </Section>

      <Section title="2. No Guaranteed Outcomes">
        <P>No astrological prediction or insight is guaranteed to come true.
        Outcomes in life depend on many factors — your free will, choices,
        actions, environment, and circumstances — that astrology cannot fully
        capture.</P>
      </Section>

      <Section title="3. Not a Substitute for Professionals">
        <P>Cosmic Lens content must <Strong>never</Strong> be used as the sole
        basis for important life decisions. Always consult appropriately
        qualified professionals:</P>
        <Bullet><Strong>Health concerns</Strong> — see a registered medical doctor. Do not stop or alter medication based on astrological readings.</Bullet>
        <Bullet><Strong>Mental health</Strong> — speak to a licensed psychologist or psychiatrist. If you are in crisis, call iCall (India) at 9152987821 or your local helpline.</Bullet>
        <Bullet><Strong>Legal matters</Strong> — consult a qualified lawyer.</Bullet>
        <Bullet><Strong>Financial / investment decisions</Strong> — consult a SEBI-registered investment advisor.</Bullet>
        <Bullet><Strong>Relationship & marriage</Strong> — consult a counsellor; compatibility scores should never replace open communication and consent.</Bullet>
      </Section>

      <Section title="4. AI-Generated Content">
        <P>The “Ask” feature uses automated software (rule-based and AI) to
        analyse your kundli. Answers are generated by code and may contain
        errors, omissions, contradictions, or culturally inappropriate phrasing.
        They are not endorsed by any individual astrologer.</P>
      </Section>

      <Section title="5. Remedies">
        <P>Suggested remedies (mantras, gemstones, donations, fasting, pujas)
        are drawn from classical texts. We do not guarantee any specific result
        from following them. <Strong>Consult a qualified Vedic astrologer or
        guru before adopting any remedy</Strong>, especially gemstones and
        mantras with seed-syllables (beej mantras).</P>
      </Section>

      <Section title="6. Birth-Data Accuracy">
        <P>Astrological calculations are highly sensitive to your time and
        place of birth. Even a 4-minute error in birth time can change your
        ascendant. We recommend verifying your birth time from a hospital
        record or birth certificate. Inaccurate input will produce inaccurate
        results.</P>
      </Section>

      <Section title="7. Cultural & Regional Differences">
        <P>Cosmic Lens uses traditional Vedic (Lahiri / Chitrapaksha) ayanamsa.
        Western, Tropical, KP, Krishnamurti, and Tantric astrologers may use
        different systems and arrive at different conclusions. None of these
        systems is “wrong” — they are different lenses.</P>
      </Section>

      <Section title="8. Emergency Situations">
        <Callout tone="danger">
          If you are experiencing a medical emergency or thoughts of self-harm,
          <Strong> please call your local emergency services immediately</Strong>.
          Do not rely on this app for crisis support. India: 112 (emergency),
          iCall 9152987821 (mental health).
        </Callout>
      </Section>

      <Section title="9. Acceptance">
        <P>By using Cosmic Lens you acknowledge that you have read and
        understood this disclaimer and agree to use the Service responsibly.</P>
      </Section>
    </LegalScreen>
  );
}

const d = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 32,
    marginBottom: 4,
  },
  line: {
    flex: 1,
    height: 1,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
  },
  title: {
    fontSize: 14,
    fontFamily: F.bold,
    letterSpacing: 0.2,
  },
});
