import React from "react";
import LegalScreen, { Section, P, Bullet, Strong, Callout } from "@/components/LegalScreen";

export default function PrivacyPolicyScreen() {
  return (
    <LegalScreen
      title="Privacy Policy"
      subtitle="How we collect, use & protect your data"
      lastUpdated="17 April 2026"
    >
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
    </LegalScreen>
  );
}
