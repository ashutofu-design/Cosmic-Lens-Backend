import { Fragment, useCallback, useEffect, useState } from "react";
import {
  type AdminStats,
  type AdminTransaction,
  type AdminUser,
  type Dashboard,
  type LoginActivityItem,
  type UserDetail,
  deleteUser,
  downloadCsv,
  fetchDashboard,
  fetchLoginActivity,
  fetchStats,
  fetchTransactions,
  fetchUserDetail,
  fetchUsers,
  formatDate,
  formatInr,
  profileBirthFields,
  resetKundliQuota,
  setUserPro,
} from "./api";

type Tab = "dashboard" | "transactions" | "users" | "logins";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [detailUserId, setDetailUserId] = useState<number | null>(null);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const [txPage, setTxPage] = useState(1);
  const [txPages, setTxPages] = useState(1);
  const [txTotal, setTxTotal] = useState(0);
  const [transactions, setTransactions] = useState<AdminTransaction[]>([]);
  const [txEmail, setTxEmail] = useState("");
  const [txStatus, setTxStatus] = useState("paid");

  const [logins, setLogins] = useState<LoginActivityItem[]>([]);
  const [loginTotal, setLoginTotal] = useState(0);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginSuccess, setLoginSuccess] = useState("");

  const loadDashboard = useCallback(async () => {
    const [d, s] = await Promise.all([fetchDashboard(), fetchStats()]);
    setDash(d);
    setStats(s);
  }, []);

  const loadTransactions = useCallback(async () => {
    const tx = await fetchTransactions(txPage, {
      email: txEmail,
      status: txStatus,
    });
    setTransactions(tx.transactions);
    setTxPages(tx.pages);
    setTxTotal(tx.total);
  }, [txPage, txEmail, txStatus]);

  const loadUsers = useCallback(async () => {
    const u = await fetchUsers(page, search, planFilter);
    setUsers(u.users);
    setPages(u.pages);
    setTotal(u.total);
  }, [page, search, planFilter]);

  const loadLogins = useCallback(async () => {
    const r = await fetchLoginActivity({
      email: loginEmail,
      success: loginSuccess || undefined,
      limit: 200,
    });
    setLogins(r.items);
    setLoginTotal(r.total);
  }, [loginEmail, loginSuccess]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "dashboard") await loadDashboard();
      else if (tab === "transactions") await loadTransactions();
      else if (tab === "users") await loadUsers();
      else if (tab === "logins") await loadLogins();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [tab, loadDashboard, loadTransactions, loadUsers, loadLogins]);

  useEffect(() => {
    load();
  }, [load]);

  async function onShowDetail(user: AdminUser) {
    if (detailUserId === user.id) {
      setDetailUserId(null);
      setDetail(null);
      setDetailError(null);
      return;
    }
    setDetailUserId(user.id);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      setDetail(await fetchUserDetail(user.id));
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "Failed to load details");
    } finally {
      setDetailLoading(false);
    }
  }

  function openUserFromTx(userId: number, email: string) {
    setTab("users");
    setPage(1);
    setSearch(email || String(userId));
    setSearchInput(email || String(userId));
    setDetailUserId(userId);
    setDetail(null);
    setDetailLoading(true);
    fetchUserDetail(userId)
      .then(setDetail)
      .catch(() => setDetailError("Failed to load"))
      .finally(() => setDetailLoading(false));
  }

  async function onGrantPro(userId: number, enable: boolean) {
    setActionBusy(true);
    try {
      await setUserPro(userId, enable);
      if (detailUserId === userId) setDetail(await fetchUserDetail(userId));
      await loadUsers();
      alert(enable ? "Pro plan enabled" : "Reverted to free");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function onResetQuota(userId: number) {
    setActionBusy(true);
    try {
      await resetKundliQuota(userId);
      alert("Kundli quota reset for today");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function onDelete(user: AdminUser) {
    const ok = window.confirm(
      `Delete user #${user.id} (${user.name || user.email})? This cannot be undone.`,
    );
    if (!ok) return;
    setDeletingId(user.id);
    try {
      await deleteUser(user.id);
      if (detailUserId === user.id) {
        setDetailUserId(null);
        setDetail(null);
      }
      await loadUsers();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  function exportTxCsv() {
    downloadCsv(
      "transactions.csv",
      ["When", "User ID", "Name", "Email", "Item", "Status", "INR", "Order ID"],
      transactions.map((r) => [
        formatDate(r.paid_at),
        String(r.user_id),
        r.user_name,
        r.user_email,
        r.title,
        r.status,
        String(r.amount_inr),
        r.order_id,
      ]),
    );
  }

  function exportUsersCsv() {
    downloadCsv(
      "users.csv",
      ["ID", "Name", "Email", "Plan", "Last login", "Kundlis"],
      users.map((u) => [
        String(u.id),
        u.name,
        u.email || u.phone,
        u.plan,
        formatDate(u.last_login),
        String(u.kundli_profiles_count),
      ]),
    );
  }

  function renderUserDetailPanel() {
    if (detailLoading) return <p className="detail-muted">Loading…</p>;
    if (detailError) return <p className="detail-error">{detailError}</p>;
    if (!detail) return <p className="detail-error">No details</p>;

    const purchases = [
      ...(detail.couple_report_purchases ?? []).map((p) => ({
        title: p.label || p.product || "Report",
        amount: p.amount_inr,
        when: p.paid_at,
      })),
      ...(detail.astrovastu_purchases ?? []).map((p) => ({
        title: p.sku || "AstroVastu",
        amount: p.amount_inr,
        when: p.paid_at,
        sub: p.property_name,
      })),
    ];

    return (
      <div className="user-detail-panel">
        <div className="detail-account">
          <p>
            <strong>Account:</strong> {detail.user.email || detail.user.phone || "—"} · Plan:{" "}
            {detail.user.plan}
            {detail.user.career_unlocked ? " · Career ✓" : ""}
          </p>
          <p className="detail-muted">
            Joined: {formatDate(detail.user.created_at)} · Last login:{" "}
            {formatDate(detail.user.last_login)}
          </p>
          <div className="detail-actions">
            <button
              type="button"
              className="primary"
              disabled={actionBusy}
              onClick={() => onGrantPro(detail.user.id, true)}
            >
              Give Pro
            </button>
            <button
              type="button"
              disabled={actionBusy}
              onClick={() => onGrantPro(detail.user.id, false)}
            >
              Set Free
            </button>
            <button type="button" disabled={actionBusy} onClick={() => onResetQuota(detail.user.id)}>
              Reset kundli quota
            </button>
          </div>
        </div>

        {purchases.length > 0 ? (
          <>
            <p className="detail-summary">Purchases (this user)</p>
            <table className="detail-table detail-table-compact">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>₹</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((p, i) => (
                  <tr key={i}>
                    <td>
                      {p.title}
                      {"sub" in p && p.sub ? (
                        <span className="detail-muted"> · {p.sub}</span>
                      ) : null}
                    </td>
                    <td>{p.amount > 0 ? formatInr(p.amount) : "—"}</td>
                    <td>{formatDate(p.when)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}

        {(detail.recent_logins ?? []).length > 0 ? (
          <>
            <p className="detail-summary">Gmail logins</p>
            <table className="detail-table detail-table-compact">
              <thead>
                <tr>
                  <th>When (IST)</th>
                  <th>Email</th>
                  <th>IP</th>
                  <th>OK</th>
                </tr>
              </thead>
              <tbody>
                {(detail.recent_logins ?? []).map((row) => (
                  <tr key={row.id}>
                    <td>{formatDate(row.created_at)}</td>
                    <td>{row.email || "—"}</td>
                    <td>{row.ip || "—"}</td>
                    <td>{row.success ? "✓" : "✗"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}

        <p className="detail-summary">
          <strong>{detail.kundli_profiles.active_count}</strong> active profile(s)
        </p>
        {detail.kundli_profiles.profiles.length === 0 && !detail.legacy_kundli ? (
          <p className="detail-muted">No kundli on server yet.</p>
        ) : (
          <table className="detail-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Relation</th>
                <th>DOB</th>
                <th>Time</th>
                <th>Place</th>
                <th>Chart</th>
              </tr>
            </thead>
            <tbody>
              {detail.kundli_profiles.profiles.map((p, i) => {
                const b = profileBirthFields(p, detail.legacy_kundli);
                return (
                  <tr key={`p-${i}`}>
                    <td>
                      {p.name || "—"}
                      {p.is_primary ? (
                        <span className="badge" style={{ marginLeft: 6 }}>
                          primary
                        </span>
                      ) : null}
                    </td>
                    <td>{p.relation || "—"}</td>
                    <td>{b.dob || "—"}</td>
                    <td>{b.tob || "—"}</td>
                    <td>{b.place || "—"}</td>
                    <td>{b.has_chart ? "✓" : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>Cosmic Lens Admin</h1>
        <p>
          Gmail login only (no OTP). VPS API via <code>VITE_API_PROXY_TARGET</code> +{" "}
          <code>VITE_ADMIN_SECRET</code>.
        </p>
      </header>

      <nav className="tabs">
        {(
          [
            ["dashboard", "Dashboard"],
            ["transactions", "Transactions"],
            ["users", "Users"],
            ["logins", "Gmail logins"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "primary" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
        <button type="button" className="tab-refresh" onClick={load} disabled={loading}>
          Refresh
        </button>
      </nav>

      {error && <div className="error">{error}</div>}

      {tab === "dashboard" && dash ? (
        <>
          <div className="grid stats">
            <div className="card">
              <h3>Total users</h3>
              <div className="value">{dash.total_users}</div>
            </div>
            {stats ? (
              <>
                <div className="card">
                  <h3>Active today</h3>
                  <div className="value">{stats.active_today}</div>
                </div>
                <div className="card">
                  <h3>Pro users</h3>
                  <div className="value">{stats.pro_users}</div>
                </div>
              </>
            ) : null}
            <div className="card">
              <h3>Today ₹</h3>
              <div className="value">{formatInr(dash.payments.today_inr)}</div>
            </div>
            <div className="card">
              <h3>Week ₹</h3>
              <div className="value">{formatInr(dash.payments.week_inr)}</div>
            </div>
            <div className="card">
              <h3>Month ₹</h3>
              <div className="value">{formatInr(dash.payments.month_inr)}</div>
            </div>
            <div className="card">
              <h3>Lifetime ₹</h3>
              <div className="value">{formatInr(dash.payments.lifetime_inr)}</div>
            </div>
          </div>
          <section className="section card">
            <h2>Subscriptions</h2>
            <p className="detail-muted">{dash.subscriptions.message}</p>
            <ul className="product-list">
              {Object.entries(dash.subscriptions.plan_counts).map(([plan, n]) => (
                <li key={plan}>
                  <span className="badge">{plan}</span>
                  <span>{n} users</span>
                </li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {tab === "transactions" ? (
        <section className="section">
          <h2>Transactions ({txTotal})</h2>
          <div className="toolbar">
            <input
              type="search"
              placeholder="Filter by email…"
              value={txEmail}
              onChange={(e) => setTxEmail(e.target.value)}
            />
            <select
              value={txStatus}
              onChange={(e) => setTxStatus(e.target.value)}
              className="select-input"
            >
              <option value="paid">Paid only</option>
              <option value="failed">Failed / pending</option>
              <option value="all">All</option>
            </select>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setTxPage(1);
                load();
              }}
            >
              Apply
            </button>
            <button type="button" onClick={exportTxCsv} disabled={!transactions.length}>
              Export CSV
            </button>
          </div>
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>User</th>
                  <th>Email</th>
                  <th>Item</th>
                  <th>Status</th>
                  <th>₹</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((row) => (
                  <tr key={row.id}>
                    <td>{formatDate(row.paid_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="link-btn"
                        onClick={() => openUserFromTx(row.user_id, row.user_email)}
                      >
                        #{row.user_id} {row.user_name || ""}
                      </button>
                    </td>
                    <td>{row.user_email || "—"}</td>
                    <td>{row.title}</td>
                    <td>
                      <span className={row.status === "paid" ? "badge ok" : "badge warn"}>
                        {row.status}
                      </span>
                    </td>
                    <td>{row.amount_inr > 0 ? formatInr(row.amount_inr) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <button type="button" disabled={txPage <= 1} onClick={() => setTxPage((p) => p - 1)}>
              Prev
            </button>
            <span>
              Page {txPage} / {txPages}
            </span>
            <button
              type="button"
              disabled={txPage >= txPages}
              onClick={() => setTxPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </section>
      ) : null}

      {tab === "logins" ? (
        <section className="section">
          <h2>Gmail login history ({loginTotal})</h2>
          <p className="detail-muted">Google / Firebase sign-in only — OTP not shown.</p>
          <div className="toolbar">
            <input
              type="search"
              placeholder="Filter email…"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
            />
            <select
              className="select-input"
              value={loginSuccess}
              onChange={(e) => setLoginSuccess(e.target.value)}
            >
              <option value="">All</option>
              <option value="1">Success</option>
              <option value="0">Failed</option>
            </select>
            <button type="button" className="primary" onClick={load}>
              Apply
            </button>
          </div>
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When (IST)</th>
                  <th>User</th>
                  <th>Gmail</th>
                  <th>IP</th>
                  <th>OK</th>
                </tr>
              </thead>
              <tbody>
                {logins.map((row) => (
                  <tr key={row.id}>
                    <td>{formatDate(row.created_at)}</td>
                    <td>
                      {row.user_id ? (
                        <button
                          type="button"
                          className="link-btn"
                          onClick={() =>
                            openUserFromTx(row.user_id!, row.email || "")
                          }
                        >
                          #{row.user_id} {row.user_name}
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{row.email || "—"}</td>
                    <td>{row.ip || "—"}</td>
                    <td>{row.success ? "✓" : "✗"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "users" ? (
        <section className="section">
          <h2>Users ({total})</h2>
          <div className="toolbar">
            <input
              type="search"
              placeholder="Search name, email…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setPage(1);
                  setSearch(searchInput);
                }
              }}
            />
            <select
              className="select-input"
              value={planFilter}
              onChange={(e) => {
                setPlanFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All plans</option>
              <option value="free">free</option>
              <option value="trial">trial</option>
              <option value="basic">basic</option>
              <option value="pro">pro</option>
            </select>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setPage(1);
                setSearch(searchInput);
              }}
            >
              Search
            </button>
            <button type="button" onClick={exportUsersCsv} disabled={!users.length}>
              Export CSV
            </button>
          </div>
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Gmail</th>
                  <th>Last login</th>
                  <th>Plan</th>
                  <th>Kundlis</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <Fragment key={u.id}>
                    <tr>
                      <td>{u.id}</td>
                      <td>{u.name || "—"}</td>
                      <td>{u.email || "—"}</td>
                      <td>{formatDate(u.last_login)}</td>
                      <td>
                        <span className="badge">{u.plan}</span>
                      </td>
                      <td>{u.kundli_profiles_count}</td>
                      <td className="actions-cell">
                        <button
                          type="button"
                          className={detailUserId === u.id ? "primary" : ""}
                          onClick={() => onShowDetail(u)}
                        >
                          {detailUserId === u.id ? "Hide" : "Details"}
                        </button>
                        <button
                          type="button"
                          className="danger"
                          disabled={deletingId === u.id}
                          onClick={() => onDelete(u)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                    {detailUserId === u.id ? (
                      <tr className="detail-row">
                        <td colSpan={7}>{renderUserDetailPanel()}</td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Prev
            </button>
            <span>
              Page {page} / {pages || 1}
            </span>
            <button type="button" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </section>
      ) : null}

      {loading && !dash && tab === "dashboard" ? (
        <p style={{ color: "var(--muted)" }}>Loading…</p>
      ) : null}
    </div>
  );
}
