import React from "react";
import LegalScreen, { Section, P, Bullet, Strong, Callout } from "@/components/LegalScreen";

export default function TermsScreen() {
  return (
    <LegalScreen
      title="Terms of Service"
      subtitle="Rules for using Cosmic Lens"
      lastUpdated="17 April 2026"
    >
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
        <P>Please review our separate <Strong>Refund &amp; Cancellation Policy</Strong>
        for full details. In summary, all sales are generally final, but refunds
        may be granted for technical failures, double-charges, or unused service
        within 7 days of payment.</P>
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
    </LegalScreen>
  );
}
