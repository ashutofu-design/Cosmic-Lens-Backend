import React from "react";
import { LegalPolicyBody } from "@/components/LegalPolicyDoc";
import LegalScreen from "@/components/LegalScreen";
import { LEGAL_META, refundPolicyDoc } from "@/lib/legalPolicies";

export default function RefundPolicyScreen() {
  return (
    <LegalScreen
      title={refundPolicyDoc.title}
      subtitle={refundPolicyDoc.subtitle}
      lastUpdated={LEGAL_META.lastUpdated}
    >
      <LegalPolicyBody doc={refundPolicyDoc} />
    </LegalScreen>
  );
}
