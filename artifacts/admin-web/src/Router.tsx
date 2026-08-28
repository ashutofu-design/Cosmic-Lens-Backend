import { lazy, Suspense, useEffect, useState } from "react";
import { isAdminRoute, routePath } from "./routePath";
import { hasValidAdminGate } from "./lib/adminGate";
import { HelpSupportPage } from "./site/HelpSupportPage";
import { PrivacyPolicyPage } from "./site/PrivacyPolicyPage";
import { PublicHomePage } from "./site/PublicHomePage";
import { TermsPage } from "./site/TermsPage";

const AdminApp = lazy(() => import("./App"));

export function Router() {
  const [path, setPath] = useState(routePath);
  const isAdmin = isAdminRoute(path);

  useEffect(() => {
    const onPop = () => setPath(routePath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    document.body.classList.toggle("admin-mode", isAdmin);
    document.body.classList.toggle("site-lock", !isAdmin);
    if (isAdmin) document.title = "Cosmic Lens · Admin";
  }, [isAdmin]);

  if (isAdmin) {
    if (!hasValidAdminGate()) {
      window.location.replace("/help-support");
      return (
        <div className="site-boot" style={{ padding: 24, textAlign: "center" }}>
          Redirecting…
        </div>
      );
    }
    return (
      <Suspense fallback={<div className="site-boot">Loading admin…</div>}>
        <AdminApp />
      </Suspense>
    );
  }

  if (path === "/help-support") {
    return <HelpSupportPage />;
  }

  if (path === "/privacy") {
    return <PrivacyPolicyPage />;
  }

  if (path === "/terms") {
    return <TermsPage />;
  }

  return <PublicHomePage />;
}
