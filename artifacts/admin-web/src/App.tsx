import { AskQuestionDetailPage } from "./AskQuestionDetailPage";
import { AskLlmContextPanel, AnswerPathBadge, parseAskLlmContext } from "./AskLlmContextPanel";
import { CopyTextButton } from "./CopyTextButton";
import { ViewQuestionButton } from "./ViewQuestionButton";
import { QuestionLangBadge } from "./QuestionLangBadge";
import { Fragment, useCallback, useEffect, useState } from "react";
import {
  type AdminStats,
  type AdminTransaction,
  type AdminUser,
  type Dashboard,
  type LoginActivityItem,
  type UserDetail,
  deleteAdminProfile,
  deleteGmailAccount,
  deleteLegacyKundli,
  deleteUser,
  type GmailProfileSimple,
  downloadCsv,
  fetchDashboard,
  fetchGmailProfiles,
  fetchLoginActivity,
  fetchPdfGenerations,
  type PdfGenerationItem,
  fetchAskQuestions,
  type AskQuestionItem,
  fetchStats,
  type GmailProfilesResponse,
  fetchTransactions,
  fetchUserDetail,
  fetchUserAskProfile,
  type UserAskProfileData,
  fetchUsers,
  fetchLoveRealityOrders,
  type LoveRealityOrderItem,
  fetchBusinessVastuOrders,
  fetchBusinessVastuOrderDetail,
  type BusinessVastuOrderItem,
  type BusinessVastuOrderDetail,
  formatDate,
  formatInr,
  profileBirthFields,
  resetKundliQuota,
  setUserPro,
} from "./api";

type Tab = "dashboard" | "transactions" | "users" | "logins" | "pdfcosts" | "askqa" | "lrorders" | "bvorders";

const NAV_ITEMS: { id: Tab; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "◈" },
  { id: "transactions", label: "Transactions", icon: "₹" },
  { id: "users", label: "Users", icon: "◎" },
  { id: "logins", label: "Gmail logins", icon: "✉" },
  { id: "lrorders", label: "Love Reality", icon: "♡" },
  { id: "bvorders", label: "Business Vastu", icon: "⌂" },
  { id: "pdfcosts", label: "PDF AI costs", icon: "◫" },
  { id: "askqa", label: "Ask Q&A", icon: "?" },
];

const TAB_META: Record<Tab, { title: string; subtitle: string }> = {
  dashboard: {
    title: "Command Center",
    subtitle: "Revenue, users, and subscription health at a glance.",
  },
  transactions: {
    title: "Transactions",
    subtitle: "Paid orders, plans, and one-time report purchases.",
  },
  users: {
    title: "Users",
    subtitle: "Accounts, kundli profiles, and admin actions.",
  },
  logins: {
    title: "Gmail logins",
    subtitle: "Google / Firebase sign-in history — OTP not shown.",
  },
  lrorders: {
    title: "Love Reality Orders",
    subtitle: "Founder-verified PDF queue with Telegram alerts when configured.",
  },
  bvorders: {
    title: "Business Vastu",
    subtitle: "Shop/office photos and floor plans awaiting Vastu review.",
  },
  pdfcosts: {
    title: "PDF AI costs",
    subtitle: "Exact tokens and INR per PDF generation.",
  },
  askqa: {
    title: "Ask Q&A",
    subtitle: "User questions with answers, tokens, and LLM chart context.",
  },
};

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
  const [askProfile, setAskProfile] = useState<UserAskProfileData | null>(null);
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
  const [deletingLoginKey, setDeletingLoginKey] = useState<string | null>(null);
  const [gmailProfileView, setGmailProfileView] = useState<{
    email: string;
    userId: number | null;
    userName: string;
  } | null>(null);
  const [gmailViewData, setGmailViewData] = useState<GmailProfilesResponse | null>(null);
  const [gmailProfilesLoading, setGmailProfilesLoading] = useState(false);
  const [gmailProfilesError, setGmailProfilesError] = useState<string | null>(null);
  const [deletingProfileKey, setDeletingProfileKey] = useState<string | null>(null);

  const [pdfGenPage, setPdfGenPage] = useState(1);
  const [pdfGenPages, setPdfGenPages] = useState(1);
  const [pdfGenTotal, setPdfGenTotal] = useState(0);
  const [pdfGenerations, setPdfGenerations] = useState<PdfGenerationItem[]>([]);
  const [pdfGenKind, setPdfGenKind] = useState("");
  const [pdfGenError, setPdfGenError] = useState<string | null>(null);

  const [askQaPage, setAskQaPage] = useState(1);
  const [askQaPages, setAskQaPages] = useState(1);
  const [askQaTotal, setAskQaTotal] = useState(0);
  const [askQuestions, setAskQuestions] = useState<AskQuestionItem[]>([]);
  const [askQaEmail, setAskQaEmail] = useState("");
  const [askQaError, setAskQaError] = useState<string | null>(null);
  const [askQaViewRow, setAskQaViewRow] = useState<AskQuestionItem | null>(null);

  const [lrOrdersPage, setLrOrdersPage] = useState(1);
  const [lrOrdersPages, setLrOrdersPages] = useState(1);
  const [lrOrdersTotal, setLrOrdersTotal] = useState(0);
  const [lrOrders, setLrOrders] = useState<LoveRealityOrderItem[]>([]);
  const [lrOrdersError, setLrOrdersError] = useState<string | null>(null);

  const [bvOrdersPage, setBvOrdersPage] = useState(1);
  const [bvOrdersPages, setBvOrdersPages] = useState(1);
  const [bvOrdersTotal, setBvOrdersTotal] = useState(0);
  const [bvOrders, setBvOrders] = useState<BusinessVastuOrderItem[]>([]);
  const [bvOrdersError, setBvOrdersError] = useState<string | null>(null);
  const [bvDetailId, setBvDetailId] = useState<string | null>(null);
  const [bvDetail, setBvDetail] = useState<BusinessVastuOrderDetail | null>(null);
  const [bvDetailLoading, setBvDetailLoading] = useState(false);

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

  const loadPdfGenerations = useCallback(async () => {
    setPdfGenError(null);
    const data = await fetchPdfGenerations({
      page: pdfGenPage,
      kind: pdfGenKind || undefined,
    });
    setPdfGenerations(data.items);
    setPdfGenPages(data.pages);
    setPdfGenTotal(data.total);
  }, [pdfGenPage, pdfGenKind]);

  const loadAskQuestions = useCallback(async () => {
    setAskQaError(null);
    const data = await fetchAskQuestions({
      page: askQaPage,
      email: askQaEmail || undefined,
    });
    setAskQuestions(data.items);
    setAskQaPages(data.pages);
    setAskQaTotal(data.total);
  }, [askQaPage, askQaEmail]);

  const loadLoveRealityOrders = useCallback(async () => {
    setLrOrdersError(null);
    const data = await fetchLoveRealityOrders({ page: lrOrdersPage });
    setLrOrders(data.orders);
    setLrOrdersPages(data.pages);
    setLrOrdersTotal(data.total);
  }, [lrOrdersPage]);

  const loadBusinessVastuOrders = useCallback(async () => {
    setBvOrdersError(null);
    const data = await fetchBusinessVastuOrders({ page: bvOrdersPage });
    setBvOrders(data.orders);
    setBvOrdersPages(data.pages);
    setBvOrdersTotal(data.total);
  }, [bvOrdersPage]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "dashboard") await loadDashboard();
      else if (tab === "transactions") await loadTransactions();
      else if (tab === "users") await loadUsers();
      else if (tab === "logins") await loadLogins();
      else if (tab === "pdfcosts") await loadPdfGenerations();
      else if (tab === "askqa") await loadAskQuestions();
      else if (tab === "lrorders") await loadLoveRealityOrders();
      else if (tab === "bvorders") await loadBusinessVastuOrders();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load";
      if (tab === "pdfcosts") setPdfGenError(msg);
      else if (tab === "askqa") setAskQaError(msg);
      else if (tab === "lrorders") setLrOrdersError(msg);
      else if (tab === "bvorders") setBvOrdersError(msg);
      else setError(msg);
    } finally {
      setLoading(false);
    }
  }, [tab, loadDashboard, loadTransactions, loadUsers, loadLogins, loadPdfGenerations, loadAskQuestions, loadLoveRealityOrders, loadBusinessVastuOrders]);

  useEffect(() => {
    load();
  }, [load]);

  async function onShowDetail(user: AdminUser) {
    if (detailUserId === user.id) {
      setDetailUserId(null);
      setDetail(null);
      setAskProfile(null);
      setDetailError(null);
      return;
    }
    setDetailUserId(user.id);
    setDetail(null);
    setAskProfile(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const [d, ap] = await Promise.all([
        fetchUserDetail(user.id),
        fetchUserAskProfile(user.id).catch(() => null),
      ]);
      setDetail(d);
      setAskProfile(ap);
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
    const label = user.email || user.name || `#${user.id}`;
    const ok = window.confirm(
      `Delete "${label}" completely?\n\nRemoves user account, all profiles, kundli, and Gmail login history. Cannot be undone.`,
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
      if (tab === "logins") await loadLogins();
      if (tab === "dashboard") await loadDashboard();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  async function openGmailProfilesView(row: LoginActivityItem) {
    const email = (row.email || "").trim();
    if (!email && !row.user_id) {
      alert("No Gmail on this row.");
      return;
    }
    setGmailProfileView({
      email,
      userId: row.user_id,
      userName: row.user_name || "",
    });
    setGmailViewData(null);
    setGmailProfilesLoading(true);
    setGmailProfilesError(null);
    try {
      const data = await fetchGmailProfiles({
        email,
        userId: row.user_id ?? undefined,
      });
      setGmailViewData(data);
      setGmailProfileView({
        email: data.email || email,
        userId: data.user_id,
        userName: data.user_name || row.user_name || "",
      });
    } catch (e) {
      setGmailProfilesError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setGmailProfilesLoading(false);
    }
  }

  function closeGmailProfilesView() {
    setGmailProfileView(null);
    setGmailViewData(null);
    setGmailProfilesError(null);
    setDeletingProfileKey(null);
  }

  async function reloadGmailView() {
    if (!gmailProfileView) return;
    const data = await fetchGmailProfiles({
      email: gmailProfileView.email,
      userId: gmailProfileView.userId ?? undefined,
    });
    setGmailViewData(data);
    if (tab === "logins") await loadLogins();
  }

  async function onDeleteAdminProfileRow(p: GmailProfileSimple) {
    const label = p.name || "this profile";
    const ok = window.confirm(
      `Delete profile "${label}" only?\n\nOther profiles and the Gmail account stay. The app will remove this profile on next sync.`,
    );
    if (!ok) return;

    const key =
      p.id != null
        ? `p-${p.id}`
        : `legacy-${gmailProfileView?.userId ?? "x"}-${p.name}`;
    setDeletingProfileKey(key);
    try {
      if (p.legacy && gmailProfileView?.userId) {
        await deleteLegacyKundli(gmailProfileView.userId);
      } else if (p.id != null) {
        await deleteAdminProfile(p.id);
      } else {
        alert("Cannot delete this row.");
        return;
      }
      await reloadGmailView();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingProfileKey(null);
    }
  }

  async function onDeleteGmailLogin(row: LoginActivityItem) {
    const email = (row.email || "").trim();
    const label = email || (row.user_id ? `user #${row.user_id}` : "this entry");
    const ok = window.confirm(
      `Delete Gmail "${label}" completely?\n\nRemoves the user account, ALL profiles, kundli data, and login history. The user will be logged out on the app and must sign in again. Cannot be undone.`,
    );
    if (!ok) return;
    const key = `${row.id}-${row.user_id ?? ""}-${email}`;
    setDeletingLoginKey(key);
    try {
      if (email) {
        await deleteGmailAccount(email);
        if (row.user_id && detailUserId === row.user_id) {
          setDetailUserId(null);
          setDetail(null);
        }
      } else if (row.user_id) {
        await deleteUser(row.user_id);
        if (detailUserId === row.user_id) {
          setDetailUserId(null);
          setDetail(null);
        }
      } else {
        alert("No user id or email on this row.");
        return;
      }
      await loadLogins();
      if (tab === "users") await loadUsers();
      if (tab === "dashboard") await loadDashboard();
      alert("Deleted.");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingLoginKey(null);
    }
  }

  async function onShowBvDetail(orderId: string) {
    if (bvDetailId === orderId) {
      setBvDetailId(null);
      setBvDetail(null);
      return;
    }
    setBvDetailId(orderId);
    setBvDetail(null);
    setBvDetailLoading(true);
    try {
      setBvDetail(await fetchBusinessVastuOrderDetail(orderId));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to load order");
      setBvDetailId(null);
    } finally {
      setBvDetailLoading(false);
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

        {askProfile && (askProfile.profile?.question_count ?? 0) > 0 ? (
          <>
            <p className="detail-summary">
              Ask mindset ({askProfile.profile.question_count} questions analysed)
            </p>
            <div className="engine-outcome-box" style={{ marginBottom: 12 }}>
              <p>
                <strong>Style:</strong> {askProfile.profile.avg_style || "—"} · avg{" "}
                {askProfile.profile.avg_word_count ?? "—"} words · emotion:{" "}
                {askProfile.profile.dominant_emotion || "—"} · top topic:{" "}
                {askProfile.profile.top_topic || "—"}
              </p>
              {(askProfile.labels ?? []).length > 0 ? (
                <p style={{ marginTop: 8 }}>
                  {(askProfile.labels ?? []).map((lb) => (
                    <span key={lb} className="badge" style={{ marginRight: 6 }}>
                      {lb}
                    </span>
                  ))}
                </p>
              ) : null}
              {askProfile.personalization_hint ? (
                <details style={{ marginTop: 8 }}>
                  <summary className="detail-muted">Personalization hint sent to Cosmo</summary>
                  <pre className="llm-context-pre" style={{ fontSize: "0.75rem" }}>
                    {askProfile.personalization_hint}
                  </pre>
                </details>
              ) : null}
            </div>
            {(askProfile.recent_signals ?? []).length > 0 ? (
              <table className="detail-table detail-table-compact">
                <thead>
                  <tr>
                    <th>When</th>
                    <th>Words</th>
                    <th>Style</th>
                    <th>Emotion</th>
                    <th>Types</th>
                    <th>Topics</th>
                  </tr>
                </thead>
                <tbody>
                  {askProfile.recent_signals.map((s, i) => (
                    <tr key={s.id ?? i}>
                      <td>{formatDate(s.created_at ?? null)}</td>
                      <td>{s.word_count ?? "—"}</td>
                      <td>{s.style || "—"}</td>
                      <td>{s.emotion || "—"}</td>
                      <td>{(s.question_types ?? []).join(", ") || "—"}</td>
                      <td>{(s.topics_detected ?? []).join(", ") || s.logged_topic || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </>
        ) : askProfile ? (
          <p className="detail-muted">No Ask questions logged yet — mindset builds after user asks.</p>
        ) : null}

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

  if (gmailProfileView) {
    const sub = gmailViewData?.subscription;
    const purchases = gmailViewData?.purchases ?? [];
    const profiles = gmailViewData?.profiles ?? [];

    return (
      <div className="admin-shell">
        <div className="cosmic-bg" aria-hidden />
        <div className="main-area gmail-standalone">
          <header className="top-bar">
            <button type="button" className="back-btn" onClick={closeGmailProfilesView}>
              ← Back to Gmail logins
            </button>
            <h2>User overview</h2>
            <p className="subtitle">
              {gmailProfileView.email}
              {gmailProfileView.userId ? ` · user #${gmailProfileView.userId}` : ""}
              {gmailProfileView.userName ? ` · ${gmailProfileView.userName}` : ""}
            </p>
          </header>

        {gmailProfilesLoading ? <p className="detail-muted">Loading…</p> : null}
        {gmailProfilesError ? <div className="error">{gmailProfilesError}</div> : null}

        {!gmailProfilesLoading && !gmailProfilesError && gmailViewData ? (
          <>
            <section className="section gmail-view-section">
              <h2>Plan &amp; purchases</h2>
              {sub ? (
                <p className="detail-summary">
                  Current plan: <strong>{sub.plan_label}</strong>
                  {sub.plan_expiry ? (
                    <>
                      {" "}
                      · expires {formatDate(sub.plan_expiry)}
                    </>
                  ) : null}
                </p>
              ) : (
                <p className="detail-muted">No linked user account.</p>
              )}

              {purchases.length === 0 ? (
                <p className="detail-muted">No paid purchases yet.</p>
              ) : (
                <div className="card" style={{ padding: 0, overflow: "auto" }}>
                  <table className="detail-table-compact">
                    <thead>
                      <tr>
                        <th>Plan / product</th>
                        <th>Amount</th>
                        <th>Paid (IST)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {purchases.map((p, i) => (
                        <tr key={`pur-${i}-${p.name}-${p.paid_at ?? ""}`}>
                          <td>{p.name}</td>
                          <td>{formatInr(p.amount_inr)}</td>
                          <td>{p.paid_at ? formatDate(p.paid_at) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="section gmail-view-section">
              <h2>
                Profiles ({profiles.length})
              </h2>
              {profiles.length === 0 ? (
                <p className="detail-muted">No profiles saved for this Gmail yet.</p>
              ) : (
                <div className="card" style={{ padding: 0, overflow: "auto" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>DOB</th>
                        <th>Birth time</th>
                        <th>Place</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {profiles.map((p, i) => {
                        const pKey =
                          p.id != null
                            ? `p-${p.id}`
                            : `legacy-${gmailViewData?.user_id ?? i}-${p.name}`;
                        const pBusy = deletingProfileKey === pKey;
                        const canDel =
                          p.id != null || (p.legacy && !!gmailViewData?.user_id);
                        return (
                        <tr key={`gp-${pKey}`}>
                          <td>{p.name || "—"}</td>
                          <td>{p.dob || "—"}</td>
                          <td>{p.tob || "—"}</td>
                          <td>{p.place || "—"}</td>
                          <td>
                            <button
                              type="button"
                              className="danger"
                              disabled={!canDel || pBusy}
                              onClick={() => onDeleteAdminProfileRow(p)}
                            >
                              {pBusy ? "…" : "Delete"}
                            </button>
                          </td>
                        </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        ) : null}
        </div>
      </div>
    );
  }

  const meta = TAB_META[tab];
  const adminSecretOk = Boolean((import.meta.env.VITE_ADMIN_SECRET || "").trim());

  return (
    <div className="admin-shell">
      <div className="cosmic-bg" aria-hidden />
      {loading ? <div className="loading-bar" aria-hidden /> : null}

      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon" aria-hidden>
            ✦
          </div>
          <div className="brand-text">
            <h1>Cosmic Lens</h1>
            <span>Admin</span>
          </div>
        </div>

        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item${tab === item.id ? " active" : ""}`}
            onClick={() => {
              setAskQaViewRow(null);
              setTab(item.id);
            }}
          >
            <span className="nav-icon" aria-hidden>
              {item.icon}
            </span>
            <span>{item.label}</span>
          </button>
        ))}

        <div className="sidebar-footer">
          <button
            type="button"
            className="nav-item nav-refresh"
            onClick={load}
            disabled={loading}
          >
            <span className="nav-icon" aria-hidden>
              ↻
            </span>
            <span>{loading ? "Refreshing…" : "Refresh"}</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="top-bar">
          <h2>{meta.title}</h2>
          <p className="subtitle">{meta.subtitle}</p>
        </header>

      {!adminSecretOk ? (
        <div className="error">
          <strong>API not configured.</strong> Create <code>artifacts/admin-web/.env</code> with{" "}
          <code>VITE_ADMIN_SECRET</code> (same as VPS <code>ADMIN_SECRET</code>). For{" "}
          <code>pnpm dev</code> set <code>VITE_API_PROXY_TARGET=http://YOUR_VPS:8080</code>. For
          static build also set <code>VITE_API_BASE=http://YOUR_VPS:8080</code>, then rebuild.
        </div>
      ) : null}

      {error && <div className="error">{error}</div>}

      {tab === "dashboard" && dash ? (
        <>
          <div className="grid stats">
            <div className="stat-card">
              <h3>Total users</h3>
              <div className="value">{dash.total_users}</div>
            </div>
            {stats ? (
              <>
                <div className="stat-card">
                  <h3>Active today</h3>
                  <div className="value">{stats.active_today}</div>
                </div>
                <div className="stat-card">
                  <h3>Pro users</h3>
                  <div className="value">{stats.pro_users}</div>
                </div>
              </>
            ) : null}
            <div className="stat-card">
              <h3>Today ₹</h3>
              <div className="value gold">{formatInr(dash.payments.today_inr)}</div>
            </div>
            <div className="stat-card">
              <h3>Week ₹</h3>
              <div className="value gold">{formatInr(dash.payments.week_inr)}</div>
            </div>
            <div className="stat-card">
              <h3>Month ₹</h3>
              <div className="value gold">{formatInr(dash.payments.month_inr)}</div>
            </div>
            <div className="stat-card">
              <h3>Lifetime ₹</h3>
              <div className="value gold">{formatInr(dash.payments.lifetime_inr)}</div>
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
                  <th>Profiles</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {logins.map((row) => {
                  const rowKey = `${row.id}-${row.user_id ?? ""}-${row.email ?? ""}`;
                  const busy = deletingLoginKey === rowKey;
                  const canView = !!(row.email?.trim() || row.user_id);
                  return (
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
                    <td>{row.user_id ? row.profile_count ?? 0 : "—"}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          disabled={!canView}
                          onClick={() => openGmailProfilesView(row)}
                        >
                          View
                        </button>
                        <button
                          type="button"
                          className="danger"
                          disabled={busy || (!row.user_id && !row.email)}
                          onClick={() => onDeleteGmailLogin(row)}
                        >
                          {busy ? "…" : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "lrorders" ? (
        <section className="section">
          <h2>Love Reality Pro orders ({lrOrdersTotal})</h2>
          <p className="detail-muted">
            Founder-verified PDF queue. You also get a Telegram/SMS alert when TELEGRAM_BOT_TOKEN is set in server .env.
          </p>
          {lrOrdersError ? <div className="error">{lrOrdersError}</div> : null}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Couple</th>
                  <th>Lang</th>
                  <th>Delivery</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Order</th>
                </tr>
              </thead>
              <tbody>
                {lrOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7}>No orders yet.</td>
                  </tr>
                ) : (
                  lrOrders.map((row) => (
                    <tr key={row.order_id}>
                      <td>{formatDate(row.created_at)}</td>
                      <td>
                        {row.p1_name} & {row.p2_name}
                        {row.user_id ? (
                          <div className="detail-muted">user #{row.user_id}</div>
                        ) : null}
                      </td>
                      <td>{row.lang}</td>
                      <td>
                        {row.contact_method === "my_reports"
                          ? "My Reports"
                          : `${row.contact_method}: ${row.contact_value}`}
                      </td>
                      <td>{row.urgent ? "⚡ 12h" : "24–48h"}</td>
                      <td>
                        <span className={row.status === "pending" ? "badge warn" : "badge ok"}>
                          {row.status}
                        </span>
                      </td>
                      <td className="detail-muted">{row.order_id.slice(0, 8)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {lrOrdersPages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={lrOrdersPage <= 1 || loading}
                onClick={() => setLrOrdersPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {lrOrdersPage} / {lrOrdersPages}
              </span>
              <button
                type="button"
                disabled={lrOrdersPage >= lrOrdersPages || loading}
                onClick={() => setLrOrdersPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "bvorders" ? (
        <section className="section">
          <h2>Business Vastu orders ({bvOrdersTotal})</h2>
          <p className="detail-muted">
            Shop/office photos and floor-plan PDFs awaiting founder Vastu review.
          </p>
          {bvOrdersError ? <div className="error">{bvOrdersError}</div> : null}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Premise</th>
                  <th>Type</th>
                  <th>Photos</th>
                  <th>PDF</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bvOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7}>No orders yet.</td>
                  </tr>
                ) : (
                  bvOrders.map((row) => (
                    <Fragment key={row.order_id}>
                      <tr>
                        <td>{formatDate(row.created_at)}</td>
                        <td>
                          {row.property_name || "—"}
                          {row.user_id ? (
                            <div className="detail-muted">
                              user #{row.user_id}
                              {row.cosmo_user_id ? ` · ${row.cosmo_user_id}` : ""}
                            </div>
                          ) : null}
                        </td>
                        <td>{row.business_type}</td>
                        <td>{row.photo_count}</td>
                        <td>{row.has_pdf ? row.pdf_filename || "yes" : "—"}</td>
                        <td>
                          <span className={row.status === "pending" ? "badge warn" : "badge ok"}>
                            {row.status}
                          </span>
                        </td>
                        <td>
                          <button
                            type="button"
                            className={bvDetailId === row.order_id ? "primary" : ""}
                            onClick={() => onShowBvDetail(row.order_id)}
                          >
                            {bvDetailId === row.order_id ? "Hide" : "View"}
                          </button>
                        </td>
                      </tr>
                      {bvDetailId === row.order_id ? (
                        <tr className="detail-row">
                          <td colSpan={7}>
                            {bvDetailLoading ? (
                              <p className="detail-muted">Loading photos…</p>
                            ) : bvDetail ? (
                              <div className="user-detail-panel">
                                <p className="detail-summary">
                                  <strong>{bvDetail.property_name}</strong> · {bvDetail.business_type}
                                </p>
                                {(bvDetail.room_photos ?? []).length > 0 ? (
                                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                                    {(bvDetail.room_photos ?? []).map((p, i) => (
                                      <div key={`${p.room_type}-${i}`} style={{ width: 140 }}>
                                        <img
                                          src={p.image_data_url}
                                          alt={p.room_type}
                                          style={{
                                            width: "100%",
                                            aspectRatio: "1",
                                            objectFit: "cover",
                                            borderRadius: 8,
                                            border: "1px solid var(--border)",
                                          }}
                                        />
                                        <p className="detail-muted" style={{ marginTop: 4, fontSize: 12 }}>
                                          {p.room_type.replace(/_/g, " ")}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="detail-muted">No room photos.</p>
                                )}
                                {bvDetail.floor_plan_upload ? (
                                  <p className="detail-muted" style={{ marginTop: 10 }}>
                                    PDF: {bvDetail.floor_plan_upload.filename || "floor plan"} · North:{" "}
                                    {bvDetail.floor_plan_upload.north_at || "top"}
                                  </p>
                                ) : null}
                              </div>
                            ) : (
                              <p className="detail-error">Could not load order.</p>
                            )}
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {bvOrdersPages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={bvOrdersPage <= 1 || loading}
                onClick={() => setBvOrdersPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {bvOrdersPage} / {bvOrdersPages}
              </span>
              <button
                type="button"
                disabled={bvOrdersPage >= bvOrdersPages || loading}
                onClick={() => setBvOrdersPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "pdfcosts" ? (
        <section className="section card">
          <h2>PDF OpenAI costs</h2>
          <p className="detail-muted">
            Exact tokens + INR per PDF. Extra/regen calls flagged so duplicate billing is visible.
          </p>
          {pdfGenError ? <div className="error">{pdfGenError}</div> : null}
          <div className="toolbar">
            <select
              value={pdfGenKind}
              onChange={(e) => {
                setPdfGenKind(e.target.value);
                setPdfGenPage(1);
              }}
            >
              <option value="">All PDF types</option>
              <option value="love_reality_pro">Love PDF</option>
              <option value="milan_pro">Milan PDF</option>
            </select>
            <button
              type="button"
              onClick={() => {
                setPdfGenError(null);
                loadPdfGenerations().catch((e) =>
                  setPdfGenError(e instanceof Error ? e.message : "Failed to load"),
                );
              }}
              disabled={loading}
            >
              Refresh
            </button>
            <span className="detail-muted">{pdfGenTotal} generations</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>PDF · cost · time</th>
                  <th>Tokens</th>
                  <th>Calls</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {pdfGenerations.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No PDF generations logged yet.</td>
                  </tr>
                ) : (
                  pdfGenerations.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <strong>{row.label}</strong>
                        {" — "}
                        <span>{formatInr(row.cost_inr)}</span>
                        {" — "}
                        <span className="detail-muted">{formatDate(row.generated_at)}</span>
                        {row.user_id ? (
                          <div className="detail-muted">user #{row.user_id}</div>
                        ) : null}
                      </td>
                      <td>
                        {row.input_tokens.toLocaleString("en-IN")} in
                        <br />
                        {row.output_tokens.toLocaleString("en-IN")} out
                        <br />
                        <span className="detail-muted">{row.model}</span>
                      </td>
                      <td>
                        {row.openai_call_count} total
                        {row.extra_calls > 0 ? (
                          <>
                            <br />
                            <span className="warn-text">{row.extra_calls} extra</span>
                          </>
                        ) : null}
                        {row.regen_count > 0 ? (
                          <>
                            <br />
                            {row.regen_count} regen
                          </>
                        ) : null}
                        {row.report_cache_hit ? (
                          <>
                            <br />
                            <span className="detail-muted">PDF cache</span>
                          </>
                        ) : null}
                        {row.polish_cache_hit ? (
                          <>
                            <br />
                            <span className="detail-muted">LLM cache</span>
                          </>
                        ) : null}
                      </td>
                      <td className="detail-muted">{row.notes}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {pdfGenPages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={pdfGenPage <= 1 || loading}
                onClick={() => setPdfGenPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {pdfGenPage} / {pdfGenPages}
              </span>
              <button
                type="button"
                disabled={pdfGenPage >= pdfGenPages || loading}
                onClick={() => setPdfGenPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "askqa" ? (
        askQaViewRow ? (
          <AskQuestionDetailPage
            row={askQaViewRow}
            onBack={() => setAskQaViewRow(null)}
          />
        ) : (
        <section className="section card">
          <h2>Ask Q&A</h2>
          <p className="detail-muted">
            User questions with full answers, OpenAI tokens, INR cost, and exact LLM chart context per Ask.
          </p>
          {askQaError ? <div className="error">{askQaError}</div> : null}
          <div className="toolbar">
            <input
              type="search"
              placeholder="Filter by user email…"
              value={askQaEmail}
              onChange={(e) => {
                setAskQaEmail(e.target.value);
                setAskQaPage(1);
              }}
            />
            <button
              type="button"
              onClick={() => {
                setAskQaError(null);
                loadAskQuestions().catch((e) =>
                  setAskQaError(e instanceof Error ? e.message : "Failed to load"),
                );
              }}
              disabled={loading}
            >
              Refresh
            </button>
            <span className="detail-muted">{askQaTotal} questions</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Question · answer · user</th>
                  <th>Tokens · cost</th>
                </tr>
              </thead>
              <tbody>
                {askQuestions.length === 0 ? (
                  <tr>
                    <td colSpan={2}>No Ask questions logged yet.</td>
                  </tr>
                ) : (
                  askQuestions.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <div className="ask-q-block">
                          <div className="ask-q-text">
                            <strong>Q:</strong> {row.question_text}
                          </div>
                          <div className="ask-q-actions">
                            <QuestionLangBadge questionText={row.question_text} compact />
                            <CopyTextButton
                              text={row.question_text}
                              label="Copy question"
                              copiedLabel="Copied"
                            />
                            <ViewQuestionButton
                              label="View"
                              onClick={() => setAskQaViewRow(row)}
                            />
                          </div>
                        </div>
                        {row.answer_text ? (
                          <>
                            <br />
                            <span className="detail-muted">
                              <strong>A:</strong> {row.answer_text}
                            </span>
                          </>
                        ) : (
                          <div className="detail-muted">No answer saved</div>
                        )}
                        <div className="detail-muted">
                          {row.user_name || row.user_email || `user #${row.user_id}`}
                          {" — "}
                          {formatDate(row.created_at)}
                          {row.topic ? ` — ${row.topic}` : ""}
                          {" — "}
                          <AnswerPathBadge
                            ctx={parseAskLlmContext(row)}
                            row={row}
                          />
                          {row.answer_source ? (
                            <>
                              {" · "}
                              <code>{row.answer_source}</code>
                            </>
                          ) : row.engine_tag ? (
                            <> — {row.engine_tag}</>
                          ) : null}
                        </div>
                        <AskLlmContextPanel
                          row={row}
                          panelId={`ask-llm-context-${row.id}`}
                        />
                      </td>
                      <td>
                        {row.total_tokens != null ? (
                          <>
                            {(row.prompt_tokens ?? 0).toLocaleString("en-IN")} in
                            <br />
                            {(row.completion_tokens ?? 0).toLocaleString("en-IN")} out
                            {row.cached_tokens ? (
                              <>
                                <br />
                                <span className="detail-muted">
                                  {row.cached_tokens.toLocaleString("en-IN")} cached
                                </span>
                              </>
                            ) : null}
                            <br />
                            <strong>{formatInr(row.cost_inr ?? 0)}</strong>
                            {row.llm_model ? (
                              <>
                                <br />
                                <span className="detail-muted">{row.llm_model}</span>
                              </>
                            ) : null}
                          </>
                        ) : (
                          <span className="detail-muted">No LLM call</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {askQaPages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={askQaPage <= 1 || loading}
                onClick={() => setAskQaPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {askQaPage} / {askQaPages}
              </span>
              <button
                type="button"
                disabled={askQaPage >= askQaPages || loading}
                onClick={() => setAskQaPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
        )
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
        <p className="detail-muted loading-shimmer" style={{ width: 120, height: 20 }}>
          Loading
        </p>
      ) : null}
      </div>
    </div>
  );
}
