import { useEffect } from "react";
import { SiteChrome } from "./SiteChrome";
import { LegalPolicyView } from "./LegalPolicyView";
import { LEGAL_META, termsOfServiceDoc } from "./legalPolicies";

export function TermsPage() {
  useEffect(() => {
    document.title = "Terms of Service — Cosmic Lens";
  }, []);

  return (
    <SiteChrome active="home">
      <main className="legal-page">
        <div className="site-wrap">
          <LegalPolicyView doc={termsOfServiceDoc} lastUpdated={LEGAL_META.lastUpdated} />
        </div>
      </main>
    </SiteChrome>
  );
}
