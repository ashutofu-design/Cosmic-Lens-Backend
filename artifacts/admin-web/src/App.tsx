import { Fragment, useCallback, useEffect, useState } from "react";
import {
  type AdminUser,
  type Dashboard,
  type UserDetail,
  deleteUser,
  type AdminTransaction,
  fetchDashboard,
  fetchTransactions,
  fetchUserDetail,
  fetchUsers,
  formatDate,
  formatInr,
  profileBirthFields,
} from "./api";

export default function App() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [detailUserId, setDetailUserId] = useState<number | null>(null);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [txPage, setTxPage] = useState(1);
  const [txPages, setTxPages] = useState(1);
  const [txTotal, setTxTotal] = useState(0);
  const [transactions, setTransactions] = useState<AdminTransaction[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, u, tx] = await Promise.all([
        fetchDashboard(),
        fetchUsers(page, search),
        fetchTransactions(txPage),
      ]);
      setDash(d);
      setUsers(u.users);
      setPages(u.pages);
      setTotal(u.total);
      setTransactions(tx.transactions);
      setTxPages(tx.pages);
      setTxTotal(tx.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [page, search, txPage]);

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
      const d = await fetchUserDetail(user.id);
      setDetail(d);
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "Failed to load details");
    } finally {
      setDetailLoading(false);
    }
  }

  async function onDelete(user: AdminUser) {
    const ok = window.confirm(
      `Delete user #${user.id} (${user.name || user.phone})? This cannot be undone.`,
    );
    if (!ok) return;
    setDeletingId(user.id);
    try {
      await deleteUser(user.id);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Cosmic Lens Admin</h1>
        <p>
          Local dashboard — connects to VPS API. Set <code>VITE_ADMIN_SECRET</code> in{" "}
          <code>.env</code> (same as server <code>ADMIN_SECRET</code>).
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      {loading && !dash ? (
        <p style={{ marginTop: 24, color: "var(--muted)" }}>Loading…</p>
      ) : null}

      {dash ? (
        <>
          <div className="grid stats">
            <div className="card">
              <h3>Total users</h3>
              <div className="value">{dash.total_users}</div>
            </div>
            <div className="card">
              <h3>Today</h3>
              <div className="value">{formatInr(dash.payments.today_inr)}</div>
            </div>
            <div className="card">
              <h3>This week</h3>
              <div className="value">{formatInr(dash.payments.week_inr)}</div>
            </div>
            <div className="card">
              <h3>This month</h3>
              <div className="value">{formatInr(dash.payments.month_inr)}</div>
            </div>
            <div className="card">
              <h3>Lifetime</h3>
              <div className="value">{formatInr(dash.payments.lifetime_inr)}</div>
            </div>
            <div className="card">
              <h3>Reports generated</h3>
              <div className="value">{dash.reports.total_generated}</div>
            </div>
          </div>

          <section className="section">
            <h2>Reports sold (PDF cache)</h2>
            <div className="two-col">
              <div className="card">
                {dash.reports.highest ? (
                  <p>
                    <strong>Highest:</strong> {dash.reports.highest.label} (
                    {dash.reports.highest.count})
                  </p>
                ) : null}
                {dash.reports.lowest && dash.reports.by_kind.length > 1 ? (
                  <p>
                    <strong>Lowest:</strong> {dash.reports.lowest.label} (
                    {dash.reports.lowest.count})
                  </p>
                ) : null}
                <ul className="product-list">
                  {dash.reports.by_kind.map((r) => (
                    <li key={r.kind}>
                      <span>{r.label}</span>
                      <span>{r.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card">
                <h3 style={{ marginTop: 0 }}>Paid products (DB)</h3>
                <ul className="product-list">
                  {dash.purchases_by_product.length === 0 ? (
                    <li>No paid couple/report orders yet</li>
                  ) : (
                    dash.purchases_by_product.map((p) => (
                      <li key={p.key}>
                        <span>{p.label}</span>
                        <span>{p.count}×</span>
                      </li>
                    ))
                  )}
                </ul>
                <h3>AstroVastu purchases</h3>
                <ul className="product-list">
                  {dash.astrovastu_purchases.length === 0 ? (
                    <li>No AstroVastu payments yet</li>
                  ) : (
                    dash.astrovastu_purchases.map((p) => (
                      <li key={p.sku}>
                        <span>{p.label}</span>
                        <span>{p.count}×</span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
          </section>

          <section className="section card placeholder">
            <h2>Subscriptions</h2>
            <p>{dash.subscriptions.message}</p>
            <ul className="product-list">
              {Object.entries(dash.subscriptions.plan_counts).map(([plan, n]) => (
                <li key={plan}>
                  <span className="badge">{plan}</span>
                  <span>{n} users</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="section">
            <h2>Transaction history ({txTotal})</h2>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 12px" }}>
              Kis user ne kya purchase kiya — server database se (paid orders).
            </p>
            <div className="card" style={{ padding: 0, overflow: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>When (IST)</th>
                    <th>User</th>
                    <th>Email</th>
                    <th>Item</th>
                    <th>₹</th>
                    <th>Order ID</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ padding: 16, color: "var(--muted)" }}>
                        No paid transactions yet
                      </td>
                    </tr>
                  ) : (
                    transactions.map((row) => (
                      <tr key={row.id}>
                        <td>{formatDate(row.paid_at)}</td>
                        <td>
                          #{row.user_id} {row.user_name || "—"}
                        </td>
                        <td>{row.user_email || "—"}</td>
                        <td>
                          {row.title}
                          {row.subtitle ? (
                            <span style={{ color: "var(--muted)", fontSize: "0.8em" }}>
                              {" "}
                              · {row.subtitle}
                            </span>
                          ) : null}
                        </td>
                        <td>{row.amount_inr > 0 ? formatInr(row.amount_inr) : "—"}</td>
                        <td style={{ fontSize: "0.75rem", maxWidth: 140, wordBreak: "break-all" }}>
                          {row.order_id || "—"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="pager" style={{ marginTop: 12 }}>
              <button
                type="button"
                disabled={txPage <= 1 || loading}
                onClick={() => setTxPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {txPage} / {txPages}
              </span>
              <button
                type="button"
                disabled={txPage >= txPages || loading}
                onClick={() => setTxPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </section>
        </>
      ) : null}

      <section className="section">
        <h2>Users ({total})</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 8px" }}>
          Kundli count = active profiles only (deleted profiles are not counted).
        </p>
        <div className="toolbar">
          <input
            type="search"
            placeholder="Search name, email or phone…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(1);
                setSearch(searchInput);
              }
            }}
          />
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
          <button type="button" onClick={load} disabled={loading}>
            Refresh
          </button>
        </div>

        <div className="card" style={{ padding: 0, overflow: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Gmail / Email</th>
                <th>Last login (IST)</th>
                <th>Plan</th>
                <th>Kundlis</th>
                <th>Love PDF</th>
                <th>Milan PDF</th>
                <th>Face</th>
                <th>Num.</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <Fragment key={u.id}>
                  <tr>
                    <td>{u.id}</td>
                    <td>{u.name || "—"}</td>
                    <td>{u.email || u.phone || "—"}</td>
                    <td>{formatDate(u.last_login)}</td>
                    <td>
                      <span className="badge">{u.plan}</span>
                    </td>
                    <td>{u.kundli_profiles_count}</td>
                    <td>{u.purchases.love_compatibility_pdf}</td>
                    <td>{u.purchases.milan_pro_pdf}</td>
                    <td>{u.purchases.face_reading_pro}</td>
                    <td>{u.purchases.life_mastery_pdf}</td>
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
                    <tr key={`${u.id}-detail`} className="detail-row">
                      <td colSpan={11}>
                        {detailLoading ? (
                          <p className="detail-muted">Loading kundli details…</p>
                        ) : detailError ? (
                          <p className="detail-error">{detailError}</p>
                        ) : detail ? (
                          <div className="user-detail-panel">
                            <div className="detail-account">
                              <p>
                                <strong>Account:</strong> {detail.user.email || detail.user.phone || "—"}{" "}
                                · Plan: {detail.user.plan}
                              </p>
                              <p className="detail-muted">
                                Joined: {formatDate(detail.user.created_at)} · Last login:{" "}
                                {formatDate(detail.user.last_login)}
                              </p>
                            </div>
                            {(detail.recent_logins ?? []).length > 0 ? (
                              <>
                                <p className="detail-summary">Recent Gmail logins</p>
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
                              <strong>{detail.kundli_profiles.active_count}</strong> active
                              profile(s)
                              {detail.kundli_profiles.deleted_count > 0
                                ? ` · ${detail.kundli_profiles.deleted_count} in trash`
                                : ""}
                            </p>
                            {detail.kundli_profiles.profiles.length === 0 &&
                            !detail.legacy_kundli ? (
                              <p className="detail-muted">
                                Abhi server par koi kundli / janam data save nahi hai. User ko app
                                mein kundli banani hogi — phir cloud sync hone par yahan DOB, time
                                aur place dikhega.
                              </p>
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
                                      <td>
                                        {b.place || "—"}
                                        {b.lat != null && b.lon != null ? (
                                          <span className="detail-muted">
                                            {" "}
                                            ({b.lat}, {b.lon})
                                          </span>
                                        ) : null}
                                      </td>
                                      <td>{b.has_chart ? "✓" : "—"}</td>
                                    </tr>
                                    );
                                  })}
                                  {detail.legacy_kundli ? (
                                    <tr>
                                      <td>
                                        {detail.legacy_kundli.name || "—"}
                                        <span className="badge" style={{ marginLeft: 6 }}>
                                          legacy
                                        </span>
                                      </td>
                                      <td>Self</td>
                                      <td>{detail.legacy_kundli.dob || "—"}</td>
                                      <td>{detail.legacy_kundli.tob || "—"}</td>
                                      <td>{detail.legacy_kundli.place || "—"}</td>
                                      <td>{detail.legacy_kundli.has_chart ? "✓" : "—"}</td>
                                    </tr>
                                  ) : null}
                                </tbody>
                              </table>
                            )}
                          </div>
                        ) : (
                          <p className="detail-error">
                            Details load nahi hue. API restart / git pull check karein, phir Refresh.
                          </p>
                        )}
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>

        <div className="pager">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span>
            Page {page} / {pages || 1}
          </span>
          <button
            type="button"
            disabled={page >= pages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </section>
    </div>
  );
}
