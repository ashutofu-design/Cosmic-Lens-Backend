import React from "react";
import LegalScreen, { Section, P, Bullet, Strong, Callout } from "@/components/LegalScreen";

export default function RefundPolicyScreen() {
  return (
    <LegalScreen
      title="Refund & Cancellation Policy"
      subtitle="When refunds are granted"
      lastUpdated="17 April 2026"
    >
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
    </LegalScreen>
  );
}
