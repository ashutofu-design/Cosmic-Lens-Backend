import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { LEGAL_META, disclaimerDoc } from "@/lib/legalPolicies";

export default function DisclaimerScreen() {
  return (
    <LegalScreen
      title={disclaimerDoc.title}
      subtitle={disclaimerDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <FadeInView delay={staggerDelay(0)}>
        <LegalPolicyBody doc={disclaimerDoc} />
      </FadeInView>
    </LegalScreen>
  );
}
