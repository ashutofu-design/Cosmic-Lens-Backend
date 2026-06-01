import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { LEGAL_META, termsOfServiceDoc } from "@/lib/legalPolicies";

export default function TermsOfServiceScreen() {
  return (
    <LegalScreen
      title={termsOfServiceDoc.title}
      subtitle={termsOfServiceDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <LegalPolicyBody doc={termsOfServiceDoc} />
    </LegalScreen>
  );
}
