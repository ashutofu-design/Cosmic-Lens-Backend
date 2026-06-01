import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { LEGAL_META, disclaimerDoc } from "@/lib/legalPolicies";

export default function DisclaimerScreen() {
  return (
    <LegalScreen
      title={disclaimerDoc.title}
      subtitle={disclaimerDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <LegalPolicyBody doc={disclaimerDoc} />
    </LegalScreen>
  );
}
