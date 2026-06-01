import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { LEGAL_META, privacyPolicyDoc } from "@/lib/legalPolicies";

export default function PrivacyPolicyScreen() {
  return (
    <LegalScreen
      title={privacyPolicyDoc.title}
      subtitle={privacyPolicyDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <LegalPolicyBody doc={privacyPolicyDoc} />
    </LegalScreen>
  );
}
