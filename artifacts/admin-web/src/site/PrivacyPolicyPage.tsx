import { useEffect } from "react";
import { SiteChrome } from "./SiteChrome";
import { LegalPolicyView } from "./LegalPolicyView";
import { LEGAL_META, privacyPolicyDoc } from "./legalPolicies";

export function PrivacyPolicyPage() {
  useEffect(() => {
    document.title = "Privacy Policy — Cosmic Lens";
  }, []);

  return (
    <SiteChrome active="home">
      <main className="legal-page">
        <div className="site-wrap">
          <LegalPolicyView doc={privacyPolicyDoc} lastUpdated={LEGAL_META.lastUpdated} />
        </div>
      </main>
    </SiteChrome>
  );
}
