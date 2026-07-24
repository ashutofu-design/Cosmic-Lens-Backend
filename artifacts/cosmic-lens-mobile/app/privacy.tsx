import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { LEGAL_META, privacyPolicyDoc } from "@/lib/legalPolicies";

export default function PrivacyPolicyScreen() {
  return (
    <LegalScreen
      title={privacyPolicyDoc.title}
      subtitle={privacyPolicyDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <FadeInView delay={staggerDelay(0)}>
        <LegalPolicyBody doc={privacyPolicyDoc} />
      </FadeInView>
    </LegalScreen>
  );
}
