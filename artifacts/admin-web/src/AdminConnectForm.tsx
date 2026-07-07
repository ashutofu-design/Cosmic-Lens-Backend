import { useState } from "react";
import {
  DEFAULT_VPS_API,
  saveAdminSession,
  testAdminConnection,
} from "./api";

export function AdminConnectForm({ onConnected }: { onConnected: () => void }) {
  const [apiBase, setApiBase] = useState(DEFAULT_VPS_API);
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!token.trim()) {
      setError("VPS ADMIN_SECRET daalo (artifacts/api-server/.env se).");
      return;
    }
    setLoading(true);
    try {
      await testAdminConnection(apiBase, token);
      saveAdminSession(apiBase, token);
      onConnected();
    } catch (err: unknown) {
      const msg = String((err as Error)?.message || err || "");
      if (/failed to fetch|network|load failed/i.test(msg)) {
        setError(
          "VPS tak connection nahi ho paya. Hostinger Firewall mein port 80 allow karein, ya http://187.127.174.55:8080 try karein.",
        );
      } else if (/401|403|unauthorized|forbidden/i.test(msg)) {
        setError("ADMIN_SECRET galat hai — VPS .env ka ADMIN_SECRET copy karein.");
      } else {
        setError(msg || "Connect fail.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-connect-wrap">
      <form className="admin-connect-card" onSubmit={handleConnect}>
        <h2>VPS Admin Connect</h2>
        <p className="admin-connect-sub">
          Apne VPS ka real data dekho — users, payments, Ask Q&A. Secret sirf is browser mein
          save hota hai.
        </p>

        <label className="admin-connect-field">
          <span>VPS API URL</span>
          <input
            type="url"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
            placeholder="http://187.127.174.55"
          />
          <small>Pehle port 80 (nginx). Nahi chale to :8080 try karein.</small>
        </label>

        <label className="admin-connect-field">
          <span>ADMIN_SECRET</span>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="VPS artifacts/api-server/.env se"
            autoComplete="off"
          />
        </label>

        {error ? <div className="error">{error}</div> : null}

        <button type="submit" className="admin-connect-btn" disabled={loading}>
          {loading ? "Connecting…" : "Connect to VPS"}
        </button>
      </form>
    </div>
  );
}
