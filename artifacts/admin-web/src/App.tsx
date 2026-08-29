import { AskQuestionDetailPage } from "./AskQuestionDetailPage";
import { InstagramAnswersPage } from "./InstagramAnswersPage";
import { CopyTextButton } from "./CopyTextButton";
import { PalmistryAnalysisWorkspace } from "./PalmistryAnalysisWorkspace";
import { ViewQuestionButton } from "./ViewQuestionButton";
import { QuestionLangBadge } from "./QuestionLangBadge";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import "./index.css";
import { isAdminRoute } from "./routePath";
import {
  syncV3PendingAlarm,
  alertNewV3Requests,
  playV3RingTone,
  showV3DesktopNotification,
} from "./v3IncomingAlert";
import { V3_CHAT_TEMPLATES } from "./v3ChatTemplates";
import { V3KundliModal } from "./V3KundliModal";
import { V3PositionsPanel } from "./V3PositionsPanel";
import type { AdminChartPayload } from "./v3KundliPack";
import { resyncPushSubscription } from "./adminPush";
import {
  type AdminStats,
  type AdminTransaction,
  type AdminUser,
  type Dashboard,
  type LoginActivityItem,
  type UserDetail,
  deleteGmailAccount,
  deleteUser,
  downloadCsv,
  fetchDashboard,
  fetchLoginActivity,
  fetchAskQuestions,
  fetchAskQuestionDetail,
  type AskQuestionItem,
  fetchTransactions,
  fetchUserDetail,
  fetchAdminUserChart,
  fetchUserAskProfile,
  lookupUser,
  lookupOrder,
  type OrderLookupResult,
  type UserAskProfileData,
  fetchUsers,
  fetchLifeMapOrders,
  fetchLifeMapOrderMedia,
  fetchBusinessVastuMedia,
  fetchPalmistryExport,
  deliverLifeMapOrder,
  deleteLifeMapOrder,
  acceptLifeMapOrder,
  unacceptLifeMapOrder,
  type LifeMapOrderItem,
  type LifeMapPersonBrief,
  type LifeMapSection,
  fetchBirthTimeRectificationOrders,
  fetchBirthTimeRectificationOrderDetail,
  type BirthTimeRectificationOrderItem,
  type BirthTimeRectificationOrderDetail,
  fetchV3LiveSessions,
  acceptV3LiveSession,
  rejectV3LiveSession,
  fetchV3ChatMessages,
  sendV3ChatMessage,
  setV3AdminTyping,
  extendV3LiveSession,
  endV3LiveSession,
  fetchV3ChatSettings,
  setV3ChatEnabled,
  type V3LiveSessionItem,
  type V3ChatMessage,
  fetchSupportThreads,
  fetchSupportMessages,
  sendSupportMessage,
  setSupportAdminTyping,
  closeSupportThread,
  type SupportThreadItem,
  type SupportMessage,
  formatDate,
  formatInr,
  profileBirthFields,
  getApiBase,
  adminLogin,
  adminLogout,
  hasAdminToken,
} from "./api";

function loginMethodLabel(method?: string): string {
  if (method === "phone") return "Phone";
  if (method === "gmail") return "Gmail";
  return method || "—";
}

function loginRowId(row: LoginActivityItem): string {
  return (
    row.login_id ||
    row.email ||
    row.phone ||
    (row.user_id ? `user #${row.user_id}` : "this entry")
  );
}

type Tab =
  | "dashboard"
  | "transactions"
  | "users"
  | "logins"
  | "lifemap"
  | "orderlookup"
  | "askqa"
  | "instagram"
  | "btorders"
  | "v3live"
  | "support";

const NAV_ITEMS: { id: Tab; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "◈" },
  { id: "transactions", label: "Transactions", icon: "₹" },
  { id: "users", label: "Users", icon: "◎" },
  { id: "logins", label: "Login", icon: "↪" },
  { id: "lifemap", label: "PDF Requests", icon: "📄" },
  { id: "orderlookup", label: "Order lookup", icon: "#" },
  { id: "btorders", label: "Birth Time Rectify", icon: "◷" },
  { id: "v3live", label: "V3 Live Chats", icon: "⚡" },
  { id: "support", label: "Support", icon: "💬" },
  { id: "askqa", label: "Ask Q&A", icon: "?" },
  { id: "instagram", label: "Instagram Auto", icon: "▶" },
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
    title: "Login",
    subtitle: "Phone OTP and Gmail sign-in history.",
  },
  lifemap: {
    title: "PDF Requests",
    subtitle:
      "Har request: user name, user ID, aur report ke saare details (numerology / photos / couple).",
  },
  orderlookup: {
    title: "Order lookup",
    subtitle: "Enter Order ID — see if the order is pending or successfully delivered.",
  },
  btorders: {
    title: "Birth Time Rectification",
    subtitle: "User life-event forms for minute-accurate birth time correction.",
  },
  v3live: {
    title: "V3 Live Chats",
    subtitle: "FIFO queue — Accept queue head to notify user; timer starts when they Accept.",
  },
  support: {
    title: "Help & Support",
    subtitle: "Persistent user inbox — text + screenshots, no timer.",
  },
  askqa: {
    title: "Ask Q&A",
    subtitle: "User questions with answers, tokens, and LLM chart context.",
  },
  instagram: {
    title: "Instagram Automations",
    subtitle: "User DM exact word → saved auto-reply. Key: video number + trigger text.",
  },
};

function formatDuration(totalSeconds: number | undefined) {
  const seconds = Math.max(0, Number(totalSeconds || 0));
  const totalMinutes = Math.round(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}

function lifeMapPublicId(row: LifeMapOrderItem): string {
  const cosmo = (row.cosmo_user_id || "").trim();
  if (cosmo) return cosmo;
  return row.user_id ? `#${row.user_id}` : "—";
}

function isLifeMapVideoOrder(row: LifeMapOrderItem): boolean {
  const deliverable = String(row.deliverable || "").toLowerCase();
  const plan = String(row.plan || "").toLowerCase();
  // Explicit product type wins — don't hide PDF box just because contact_method is whatsapp.
  if (deliverable === "video" || plan === "vip") return true;
  if (deliverable === "report" || plan === "pdf") return false;
  if (row.kind === "palmistry" && /pdf/i.test(String(row.label || ""))) return false;
  return String(row.contact_method || "").toLowerCase() === "whatsapp";
}

function lifeMapProductLabel(row: LifeMapOrderItem): string {
  if (isLifeMapVideoOrder(row)) {
    if (row.kind === "palmistry") {
      return "Palmistry Personalized Video (WhatsApp · no PDF/report)";
    }
    return `${row.label || "Pro"} · Personalized Video (WhatsApp · no PDF/report)`;
  }
  if (row.kind === "palmistry") {
    return row.label?.includes("PDF")
      ? row.label
      : "Palmistry Pro Report (PDF)";
  }
  return row.label || "PDF";
}

function lifeMapDeliveryLabel(row: LifeMapOrderItem): string {
  if (row.urgent) {
    return "⚡ Priority — deliver within 12 hours";
  }
  return "📦 Standard — 4–6 business days";
}

function lifeMapAmountLabel(row: LifeMapOrderItem): string {
  let amount = Number(row.amount_inr);
  // Palmistry: if server did not persist amount, show expected plan total so admin never sees blank.
  if ((!Number.isFinite(amount) || amount <= 0) && row.kind === "palmistry") {
    const video = isLifeMapVideoOrder(row);
    const base = video ? 2999 : 1499;
    const fee = row.urgent ? 299 : 0;
    amount = base + fee;
    if (row.urgent && fee > 0) {
      return `₹${amount} est. (incl. Priority ₹${fee})`;
    }
    return `₹${amount} est.`;
  }
  // Numerology: same — bypass / old orders often stored amount_inr=null.
  if ((!Number.isFinite(amount) || amount <= 0) && row.kind === "numerology_pro") {
    const video = isLifeMapVideoOrder(row);
    const base = video ? 799 : 299;
    const fee = row.urgent ? (video ? 299 : 149) : 0;
    amount = base + fee;
    if (row.urgent && fee > 0) {
      return `₹${amount} est. (incl. Priority ₹${fee})`;
    }
    return `₹${amount} est.`;
  }
  if (!Number.isFinite(amount) || amount <= 0) return "—";
  const fee = Number(row.priority_fee_inr);
  if (row.urgent && Number.isFinite(fee) && fee > 0) {
    return `₹${amount} (incl. Priority ₹${fee})`;
  }
  return `₹${amount}`;
}

function hasBirthDetails(person?: LifeMapPersonBrief | null): boolean {
  if (!person) return false;
  return Boolean(
    person.name ||
      person.dob ||
      person.tob ||
      person.place ||
      person.mobile ||
      person.gender,
  );
}

function LifeMapPersonCard({
  person,
  heading,
}: {
  person: LifeMapPersonBrief;
  heading: string;
}) {
  const rows: [string, string][] = [
    ["Name", person.name || "—"],
    ["DOB", person.dob || "—"],
    ["Time of birth", person.tob || "—"],
    ["Place", person.place || "—"],
  ];
  if (person.gender) rows.push(["Gender", person.gender]);
  if (person.mobile) rows.push(["Mobile", person.mobile]);
  if (person.lat != null && String(person.lat) !== "") {
    rows.push(["Latitude", String(person.lat)]);
  }
  if (person.lon != null && String(person.lon) !== "") {
    rows.push(["Longitude", String(person.lon)]);
  }
  if (person.tz) rows.push(["Timezone", person.tz]);
  return (
    <div className="lifemap-person">
      <strong>{heading}</strong>
      {rows.map(([k, v]) => (
        <div key={k}>
          {k}: {v}
        </div>
      ))}
    </div>
  );
}

function LifeMapMediaPreview({
  media,
  loading,
  alt,
  empty,
}: {
  media?: { url: string; mime: string };
  loading?: boolean;
  alt: string;
  empty?: string;
}) {
  if (media) {
    if (media.mime.includes("pdf")) {
      return (
        <div
          style={{
            marginTop: 8,
            borderRadius: 10,
            border: "1px solid rgba(245, 158, 11, 0.55)",
            background: "rgba(245, 158, 11, 0.10)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 8,
              padding: "8px 10px",
              borderBottom: "1px solid rgba(245, 158, 11, 0.35)",
            }}
          >
            <strong style={{ fontSize: 12 }}>PDF box</strong>
            <a className="link-btn" href={media.url} target="_blank" rel="noreferrer">
              Open ↗
            </a>
          </div>
          <iframe
            title={alt || "PDF preview"}
            src={media.url}
            style={{
              width: "100%",
              height: 420,
              border: 0,
              background: "#0b0b12",
            }}
          />
        </div>
      );
    }
    return (
      <a href={media.url} target="_blank" rel="noreferrer">
        <img className="lifemap-room-thumb" src={media.url} alt={alt} />
      </a>
    );
  }
  if (loading) return <div className="detail-muted">Loading photo…</div>;
  return <div className="detail-muted">{empty || "No photo on file"}</div>;
}

/** Always-visible founder PDF paste box — page-wise editor + optional image. */
function LifeMapPdfDeliverBox({
  row,
  draftKey,
  publicId,
  accepted,
  busy,
  delivering,
  pages,
  pageImages,
  attachUser,
  onPagesChange,
  onPageImagesChange,
  onAttachChange,
  onDeliver,
}: {
  row: LifeMapOrderItem;
  draftKey: string;
  publicId: string;
  accepted: boolean;
  busy: boolean;
  delivering: boolean;
  pages: string[];
  pageImages: (string | null)[];
  attachUser: string;
  onPagesChange: (pages: string[]) => void;
  onPageImagesChange: (images: (string | null)[]) => void;
  onAttachChange: (v: string) => void;
  onDeliver: () => void;
}) {
  const delivered = String(row.status || "").toLowerCase() === "delivered";
  const needsUserAttach =
    row.kind === "palmistry" && (!row.user_id || Number(row.user_id) === 0);
  const safePages = pages.length ? pages : [""];
  const safeImages =
    pageImages.length >= safePages.length
      ? pageImages
      : [...pageImages, ...Array(safePages.length - pageImages.length).fill(null)];
  const [activeIdx, setActiveIdx] = useState(0);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const textRef = useRef<HTMLTextAreaElement | null>(null);
  const idx = Math.min(activeIdx, safePages.length - 1);

  useEffect(() => {
    if (activeIdx > safePages.length - 1) setActiveIdx(Math.max(0, safePages.length - 1));
  }, [activeIdx, safePages.length]);

  const syncImagesLen = (nextPages: string[], images: (string | null)[]) => {
    const next = images.slice(0, nextPages.length);
    while (next.length < nextPages.length) next.push(null);
    return next;
  };

  const setPageText = (text: string) => {
    const next = [...safePages];
    next[idx] = text;
    onPagesChange(next);
  };

  const setPageImage = (dataUrl: string | null) => {
    const next = syncImagesLen(safePages, [...safeImages]);
    next[idx] = dataUrl;
    onPageImagesChange(next);
  };

  const addPage = () => {
    const next = [...safePages, ""];
    onPagesChange(next);
    onPageImagesChange(syncImagesLen(next, safeImages));
    setActiveIdx(next.length - 1);
  };

  const deletePage = () => {
    if (safePages.length <= 1) {
      onPagesChange([""]);
      onPageImagesChange([null]);
      setActiveIdx(0);
      return;
    }
    if (!window.confirm(`Page ${idx + 1} delete karein?`)) return;
    const next = safePages.filter((_, i) => i !== idx);
    const nextImgs = safeImages.filter((_, i) => i !== idx);
    onPagesChange(next.length ? next : [""]);
    onPageImagesChange(syncImagesLen(next.length ? next : [""], nextImgs));
    setActiveIdx(Math.max(0, idx - 1));
  };

  const onPickImage = (file: File | null) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      window.alert("Sirf image file (PNG/JPG/WebP) choose karo.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      window.alert("Image 5MB se chhoti honi chahiye.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : null;
      setPageImage(result);
    };
    reader.readAsDataURL(file);
  };

  /** Wrap current textarea selection with markers (bold / italic / …). */
  const wrapSelection = (before: string, after: string, placeholder = "text") => {
    const el = textRef.current;
    const value = safePages[idx] || "";
    if (!el) {
      setPageText(`${value}${before}${placeholder}${after}`);
      return;
    }
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    const selected = value.slice(start, end) || placeholder;
    const next = value.slice(0, start) + before + selected + after + value.slice(end);
    setPageText(next);
    requestAnimationFrame(() => {
      const pos = start + before.length + selected.length + after.length;
      el.focus();
      el.setSelectionRange(start + before.length, start + before.length + selected.length);
      void pos;
    });
  };

  const insertBulletLine = () => {
    const el = textRef.current;
    const value = safePages[idx] || "";
    if (!el) {
      setPageText(value ? `${value}\n- ` : "- ");
      return;
    }
    const start = el.selectionStart ?? value.length;
    const lineStart = value.lastIndexOf("\n", Math.max(0, start - 1)) + 1;
    const next = value.slice(0, lineStart) + "- " + value.slice(lineStart);
    setPageText(next);
    requestAnimationFrame(() => {
      el.focus();
      const caret = lineStart + 2 + (start - lineStart);
      el.setSelectionRange(caret, caret);
    });
  };

  const totalChars = safePages.reduce((n, p) => n + p.trim().length, 0);
  const hasAnyImage = safeImages.some((x) => Boolean(x));
  const canDeliver = busy ? false : totalChars >= 40 || hasAnyImage;

  return (
    <div
      style={{
        flex: "1 1 320px",
        minWidth: 260,
        width: "100%",
        marginTop: 12,
        padding: 10,
        borderRadius: 10,
        border: "1px solid rgba(245, 158, 11, 0.55)",
        background: "rgba(245, 158, 11, 0.12)",
      }}
    >
      <div style={{ fontWeight: 800, fontSize: 12, marginBottom: 6 }}>PDF box</div>
      {!accepted ? (
        <p className="detail-muted" style={{ margin: 0, fontSize: 12 }}>
          Pehle <strong>Approve</strong> karo — phir yahan paste unlock. Send pe PDF{" "}
          {publicId} ke My Reports mein jayegi.
        </p>
      ) : delivered ? (
        <p className="detail-muted" style={{ margin: 0, fontSize: 12 }}>
          Delivered — My Reports mein PDF hai.
        </p>
      ) : (
        <>
          <p className="detail-muted" style={{ margin: "0 0 8px", fontSize: 12 }}>
            Har admin page → PDF page. Text / image dono usi page pe jayenge.{" "}
            <strong>Add image</strong> current page ke liye.
          </p>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 6,
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            {safePages.map((_, i) => (
              <button
                key={`${draftKey}-p${i}`}
                type="button"
                className={i === idx ? "primary" : undefined}
                style={{
                  fontSize: 12,
                  padding: "4px 10px",
                  borderRadius: 8,
                  border:
                    i === idx
                      ? "1px solid rgba(245,158,11,0.9)"
                      : "1px solid rgba(255,255,255,0.2)",
                  background:
                    i === idx ? "rgba(245,158,11,0.35)" : "rgba(0,0,0,0.25)",
                  color: "inherit",
                  cursor: "pointer",
                  fontWeight: i === idx ? 800 : 600,
                }}
                disabled={busy}
                onClick={() => setActiveIdx(i)}
              >
                Page {i + 1}
                {safeImages[i] ? " 🖼" : ""}
              </button>
            ))}
            <button
              type="button"
              disabled={busy}
              onClick={addPage}
              style={{
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 8,
                border: "1px solid rgba(34,197,94,0.55)",
                background: "rgba(34,197,94,0.15)",
                color: "inherit",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              + Add page
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
              style={{
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 8,
                border: "1px solid rgba(96,165,250,0.65)",
                background: "rgba(96,165,250,0.15)",
                color: "inherit",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              + Add image
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0] || null;
                onPickImage(f);
                e.target.value = "";
              }}
            />
            <button
              type="button"
              disabled={busy}
              onClick={deletePage}
              style={{
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 8,
                border: "1px solid rgba(239,68,68,0.55)",
                background: "rgba(239,68,68,0.12)",
                color: "inherit",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              Delete page
            </button>
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 4 }}>
            Editing Page {idx + 1} of {safePages.length}
          </div>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 6,
              marginBottom: 8,
              alignItems: "center",
            }}
          >
            {(
              [
                { label: "B", title: "Bold", run: () => wrapSelection("**", "**") },
                { label: "I", title: "Italic", run: () => wrapSelection("*", "*") },
                { label: "U", title: "Underline", run: () => wrapSelection("__", "__") },
                {
                  label: "Gold",
                  title: "Champagne gold highlight",
                  run: () => wrapSelection("{{", "}}"),
                },
                { label: "• List", title: "Bullet line", run: insertBulletLine },
              ] as const
            ).map((btn) => (
              <button
                key={btn.label}
                type="button"
                title={btn.title}
                disabled={busy}
                onClick={btn.run}
                style={{
                  fontSize: 12,
                  fontWeight: btn.label === "B" ? 800 : btn.label === "I" ? 600 : 700,
                  fontStyle: btn.label === "I" ? "italic" : "normal",
                  textDecoration: btn.label === "U" ? "underline" : "none",
                  padding: "4px 10px",
                  borderRadius: 8,
                  border: "1px solid rgba(201,168,106,0.45)",
                  background: "rgba(0,0,0,0.35)",
                  color: btn.label === "Gold" ? "#C9A86A" : "inherit",
                  cursor: "pointer",
                }}
              >
                {btn.label}
              </button>
            ))}
            <span className="detail-muted" style={{ fontSize: 11 }}>
              Select word → click format
            </span>
          </div>
          {safeImages[idx] ? (
            <div
              style={{
                marginBottom: 8,
                padding: 8,
                borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.15)",
                background: "rgba(0,0,0,0.25)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 6,
                  fontSize: 11,
                }}
              >
                <span>Page {idx + 1} image (PDF me isi page pe)</span>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => setPageImage(null)}
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 6,
                    border: "1px solid rgba(239,68,68,0.5)",
                    background: "transparent",
                    color: "inherit",
                    cursor: "pointer",
                  }}
                >
                  Remove image
                </button>
              </div>
              <img
                src={safeImages[idx] || ""}
                alt={`Page ${idx + 1}`}
                style={{
                  maxWidth: "100%",
                  maxHeight: 160,
                  objectFit: "contain",
                  borderRadius: 6,
                  display: "block",
                }}
              />
            </div>
          ) : null}
          <textarea
            ref={textRef}
            rows={8}
            style={{
              width: "100%",
              boxSizing: "border-box",
              fontSize: 13,
              lineHeight: 1.45,
              minHeight: 140,
              borderRadius: 8,
              padding: 8,
              border: "1px solid rgba(255,255,255,0.15)",
              background: "rgba(0,0,0,0.35)",
              color: "inherit",
              resize: "vertical",
            }}
            placeholder={`Page ${idx + 1} — text paste karo. Bold: **word** · Underline: __word__ · Gold: {{word}}`}
            value={safePages[idx] || ""}
            onChange={(e) => setPageText(e.target.value)}
            disabled={busy}
          />
          {needsUserAttach ? (
            <div style={{ marginTop: 8 }}>
              <label
                style={{
                  display: "block",
                  fontSize: 11,
                  fontWeight: 700,
                  marginBottom: 4,
                  color: "rgba(245, 158, 11, 0.95)",
                }}
              >
                User missing — My Reports ke liye User # ya COSMO id
              </label>
              <input
                type="text"
                placeholder="e.g. 42 or COSMO142"
                value={attachUser}
                onChange={(e) => onAttachChange(e.target.value)}
                disabled={busy}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  fontSize: 13,
                  borderRadius: 8,
                  padding: "6px 8px",
                  border: "1px solid rgba(245, 158, 11, 0.45)",
                  background: "rgba(0,0,0,0.35)",
                  color: "inherit",
                }}
              />
            </div>
          ) : null}
          <button
            type="button"
            className="primary"
            style={{ marginTop: 8 }}
            disabled={!canDeliver}
            onClick={onDeliver}
          >
            {delivering
              ? "PDF ban raha hai…"
              : `PDF banao (${safePages.length} page) → My Reports (${publicId})`}
          </button>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(() => hasAdminToken());

  useEffect(() => {
    if (!isAdminRoute()) window.location.replace("/");
  }, []);

  if (!isAdminRoute()) return null;
  if (!authed) return <AdminLogin onSuccess={() => setAuthed(true)} />;
  return <AdminPanel />;
}

function AdminLogin({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mpin, setMpin] = useState("");
  const [enrollCode, setEnrollCode] = useState("");
  const [showEnroll, setShowEnroll] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await adminLogin(username.trim(), password, mpin.trim(), {
        enrollCode: enrollCode.trim(),
      });
      onSuccess();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Login failed";
      if (msg === "PANEL_LOCKED") {
        setError(
          "Panel locked. Pehle Help & Support pe jao — “locate” 3 baar, phir “For” 3 baar tap karo, uske baad yahan login karo.",
        );
      } else if (msg === "ENROLL_CODE_REQUIRED" || msg === "DEVICE_NOT_ALLOWED") {
        setShowEnroll(true);
        setError("Yeh device allowed nahi hai. Pehli baar enroll code daalo.");
      } else {
        setError(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100dvh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        background: "#080a12",
      }}
    >
      <form
        onSubmit={onSubmit}
        className="card"
        style={{
          width: "100%",
          maxWidth: 360,
          display: "flex",
          flexDirection: "column",
          gap: 12,
          padding: 24,
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 4 }}>
          <div style={{ fontSize: 28 }} aria-hidden>
            ✦
          </div>
          <h2 style={{ margin: "6px 0 2px" }}>Cosmic Admin</h2>
          <div className="detail-muted" style={{ fontSize: 13 }}>
            Login required
          </div>
        </div>
        {error ? <div className="error">{error}</div> : null}
        <a
          href="/help-support"
          className="detail-muted"
          style={{ fontSize: 13, textAlign: "center" }}
        >
          Panel locked? Help &amp; Support → locate ×3, then For ×3
        </a>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
          Username
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            required
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
          MPIN
          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={8}
            value={mpin}
            onChange={(e) => setMpin(e.target.value.replace(/\D/g, ""))}
            autoComplete="off"
            required
          />
        </label>
        {showEnroll ? (
          <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
            Device enroll code (sirf nayi device par)
            <input
              type="password"
              value={enrollCode}
              onChange={(e) => setEnrollCode(e.target.value)}
              autoComplete="off"
              placeholder="ADMIN_ENROLL_CODE"
            />
          </label>
        ) : null}
        <button
          type="submit"
          className="primary"
          disabled={busy || !username.trim() || !password || !mpin.trim()}
        >
          {busy ? "Checking…" : "Login"}
        </button>
      </form>
    </div>
  );
}

/** Background badge polling — slower + pauses when tab hidden to reduce VPS load. */
const ADMIN_BG_POLL_MS = 12_000;
const ADMIN_TAB_POLL_MS = 12_000;
const ADMIN_CHAT_POLL_MS = 3_000;
const V3_TIMER_TICK_MS = 5_000;

function adminPollVisible(): boolean {
  return typeof document === "undefined" || document.visibilityState === "visible";
}

function AdminPanel() {
  const initialTab = (): Tab => {
    const t = new URLSearchParams(window.location.search).get("tab");
    return NAV_ITEMS.some((item) => item.id === t) ? (t as Tab) : "dashboard";
  };
  const [tab, setTab] = useState<Tab>(initialTab);
  const tabRef = useRef<Tab>(initialTab());
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    tabRef.current = tab;
  }, [tab]);

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("tab");
    if (t && NAV_ITEMS.some((item) => item.id === t)) {
      setTab(t as Tab);
    }
  }, []);
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
  const [userIdInput, setUserIdInput] = useState("");
  const [directLookupOpen, setDirectLookupOpen] = useState(false);
  const [planFilter, setPlanFilter] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [detailUserId, setDetailUserId] = useState<number | null>(null);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [askProfile, setAskProfile] = useState<UserAskProfileData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

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

  const [lifeMapTotal, setLifeMapTotal] = useState(0);
  const [orderLookupInput, setOrderLookupInput] = useState("");
  const [orderLookupLoading, setOrderLookupLoading] = useState(false);
  const [orderLookupError, setOrderLookupError] = useState<string | null>(null);
  const [orderLookupResult, setOrderLookupResult] = useState<OrderLookupResult | null>(null);
  const [lifeMapSections, setLifeMapSections] = useState<LifeMapSection[]>([
    { key: "love_reality_pro", title: "Love Reality Pro", orders: [], total: 0 },
    { key: "milan_pro", title: "Kundli Milan Pro", orders: [], total: 0 },
    { key: "numerology_pro", title: "Numerology Pro Report", orders: [], total: 0 },
    { key: "astrovastu_pro", title: "AstroVastu Pro Report", orders: [], total: 0 },
    { key: "business_vastu_pro", title: "Business Vastu", orders: [], total: 0 },
    { key: "palmistry", title: "Palmistry", orders: [], total: 0 },
  ]);
  const [lifeMapActive, setLifeMapActive] = useState("love_reality_pro");
  const [lifeMapError, setLifeMapError] = useState<string | null>(null);
  const [lifeMapDrafts, setLifeMapDrafts] = useState<Record<string, string[]>>({});
  const [lifeMapPageImages, setLifeMapPageImages] = useState<
    Record<string, (string | null)[]>
  >({});
  const [lifeMapAttachUser, setLifeMapAttachUser] = useState<Record<string, string>>({});
  const [lifeMapDelivering, setLifeMapDelivering] = useState<string | null>(null);
  const [lifeMapDeleting, setLifeMapDeleting] = useState<string | null>(null);
  const [lifeMapAccepting, setLifeMapAccepting] = useState<string | null>(null);
  const [lifeMapUnacceptedCount, setLifeMapUnacceptedCount] = useState(0);
  const [lifeMapMsg, setLifeMapMsg] = useState<string | null>(null);
  const [lifeMapAutoApprove, setLifeMapAutoApprove] = useState(() => {
    try {
      return window.localStorage.getItem("cosmic.admin.autoApprovePdf") === "1";
    } catch {
      return false;
    }
  });
  const [palmistryWorkspaceId, setPalmistryWorkspaceId] = useState<string | null>(null);
  const [lifeMapMedia, setLifeMapMedia] = useState<
    Record<string, { url: string; mime: string }>
  >({});
  const [lifeMapMediaLoading, setLifeMapMediaLoading] = useState<
    Record<string, boolean>
  >({});
  const lifeMapMediaInflight = useRef<Set<string>>(new Set());

  const markLifeMapMediaLoading = useCallback((key: string, on: boolean) => {
    setLifeMapMediaLoading((prev) => {
      if (on) return { ...prev, [key]: true };
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const onViewLifeMapMedia = useCallback(
    async (orderId: string) => {
      if (lifeMapMediaInflight.current.has(orderId)) return;
      lifeMapMediaInflight.current.add(orderId);
      markLifeMapMediaLoading(orderId, true);
      try {
        const media = await fetchLifeMapOrderMedia(orderId);
        setLifeMapMedia((prev) => ({ ...prev, [orderId]: media }));
      } catch (e) {
        lifeMapMediaInflight.current.delete(orderId);
        setLifeMapError(e instanceof Error ? e.message : "Media load failed");
      } finally {
        markLifeMapMediaLoading(orderId, false);
      }
    },
    [markLifeMapMediaLoading],
  );

  const onViewBusinessVastuMedia = useCallback(
    async (orderId: string, item: number | "plan") => {
      const key = `${orderId}:${item}`;
      if (lifeMapMediaInflight.current.has(key)) return;
      lifeMapMediaInflight.current.add(key);
      markLifeMapMediaLoading(key, true);
      try {
        const media = await fetchBusinessVastuMedia(orderId, item);
        setLifeMapMedia((prev) => ({ ...prev, [key]: media }));
      } catch (e) {
        lifeMapMediaInflight.current.delete(key);
        setLifeMapError(e instanceof Error ? e.message : "Media load failed");
      } finally {
        markLifeMapMediaLoading(key, false);
      }
    },
    [markLifeMapMediaLoading],
  );

  const [askQaPage, setAskQaPage] = useState(1);
  const [askQaPages, setAskQaPages] = useState(1);
  const [askQaTotal, setAskQaTotal] = useState(0);
  const [askQuestions, setAskQuestions] = useState<AskQuestionItem[]>([]);
  const [askQaEmail, setAskQaEmail] = useState("");
  const [askQaError, setAskQaError] = useState<string | null>(null);
  const [askQaViewRow, setAskQaViewRow] = useState<AskQuestionItem | null>(null);
  const [askQaDetailLoading, setAskQaDetailLoading] = useState(false);

  const [btOrdersPage, setBtOrdersPage] = useState(1);
  const [btOrdersPages, setBtOrdersPages] = useState(1);
  const [btOrdersTotal, setBtOrdersTotal] = useState(0);
  const [btOrders, setBtOrders] = useState<BirthTimeRectificationOrderItem[]>([]);
  const [btOrdersError, setBtOrdersError] = useState<string | null>(null);
  const [btDetailId, setBtDetailId] = useState<string | null>(null);
  const [btDetail, setBtDetail] = useState<BirthTimeRectificationOrderDetail | null>(null);
  const [btDetailLoading, setBtDetailLoading] = useState(false);
  const [btDrafts, setBtDrafts] = useState<Record<string, string>>({});
  const [btDelivering, setBtDelivering] = useState<string | null>(null);
  const [btDeliverMsg, setBtDeliverMsg] = useState<string | null>(null);
  const [btDeliverError, setBtDeliverError] = useState<string | null>(null);

  const [v3Page, setV3Page] = useState(1);
  const [v3Pages, setV3Pages] = useState(1);
  const [v3Total, setV3Total] = useState(0);
  const [v3Sessions, setV3Sessions] = useState<V3LiveSessionItem[]>([]);
  const [v3Error, setV3Error] = useState<string | null>(null);
  const [v3BusyId, setV3BusyId] = useState<string | null>(null);
  const [v3ChatId, setV3ChatId] = useState<string | null>(null);
  const [v3ChatSession, setV3ChatSession] = useState<V3LiveSessionItem | null>(null);
  const [v3ChatMessages, setV3ChatMessages] = useState<V3ChatMessage[]>([]);
  const [v3ChatDraft, setV3ChatDraft] = useState("");
  const [v3ChatSending, setV3ChatSending] = useState(false);
  const [v3TemplatesOpen, setV3TemplatesOpen] = useState(false);
  const [v3KundliOpen, setV3KundliOpen] = useState(false);
  const [v3PositionsOpen, setV3PositionsOpen] = useState(false);
  const [v3KundliLoading, setV3KundliLoading] = useState(false);
  const [v3KundliError, setV3KundliError] = useState<string | null>(null);
  const [v3KundliData, setV3KundliData] = useState<AdminChartPayload | null>(null);
  const [v3KundliSharing, setV3KundliSharing] = useState(false);
  const [v3ChatTick, setV3ChatTick] = useState(0);
  const [v3Enabled, setV3Enabled] = useState(false);
  const [v3SettingsBusy, setV3SettingsBusy] = useState(false);
  const [v3PendingCount, setV3PendingCount] = useState(0);
  const [v3EngineBusy, setV3EngineBusy] = useState(false);
  const [v3QueueHeadId, setV3QueueHeadId] = useState<string | null>(null);
  const [supportThreads, setSupportThreads] = useState<SupportThreadItem[]>([]);
  const [supportWaitingCount, setSupportWaitingCount] = useState(0);
  const [supportError, setSupportError] = useState<string | null>(null);
  const [supportThreadId, setSupportThreadId] = useState<string | null>(null);
  const [supportThread, setSupportThread] = useState<SupportThreadItem | null>(null);
  const [supportMessages, setSupportMessages] = useState<SupportMessage[]>([]);
  const [supportDraft, setSupportDraft] = useState("");
  const [supportSending, setSupportSending] = useState(false);
  const supportPrevWaitingRef = useRef(0);
  const lifeMapSeenOrderIdsRef = useRef<Set<string>>(new Set());
  const lifeMapPollReadyRef = useRef(false);
  const supportListRef = useRef<HTMLDivElement | null>(null);
  const v3PrevPendingRef = useRef(0);
  // Mirror of v3ChatId for the always-on poll (its closure has empty deps).
  const v3ChatIdRef = useRef<string | null>(null);
  // Live sessions already auto-opened once — don't reopen if admin closed them.
  const v3AutoOpenedLiveRef = useRef<Set<string>>(new Set());
  // Prevent double "time up" alerts when timer hits 0.
  const v3TimerEndedRef = useRef(false);
  const v3ChatListRef = useRef<HTMLDivElement | null>(null);
  // Stick to bottom while admin is at the bottom; never yank when scrolled up.
  const v3ChatStickBottomRef = useRef(true);
  // Real visible viewport height (px). Mobile browsers shrink it for URL bar /
  // keyboard; 100vh/100dvh get this wrong on several browsers, so measure it.
  const [v3ViewportH, setV3ViewportH] = useState<number | null>(null);
  // When the keyboard opens, iOS/Android scroll the page — offsetTop tracks
  // where the visible viewport starts so the overlay stays pinned (no jumping).
  const [v3ViewportTop, setV3ViewportTop] = useState(0);

  useEffect(() => {
    if (!v3ChatId) return;
    let raf = 0;
    const measure = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const vv = window.visualViewport;
        const h = Math.round(vv ? vv.height : window.innerHeight);
        const top = Math.round(vv ? vv.offsetTop : 0);
        // Ignore sub-2px jitter so the layout never "breathes" while typing.
        setV3ViewportH((prev) => (prev != null && Math.abs(prev - h) < 2 ? prev : h));
        setV3ViewportTop((prev) => (Math.abs(prev - top) < 2 ? prev : top));
        // Keyboard opened/closed → keep the conversation pinned to the bottom.
        const el = v3ChatListRef.current;
        if (el && v3ChatStickBottomRef.current) el.scrollTop = el.scrollHeight;
      });
    };
    measure();
    const vv = window.visualViewport;
    vv?.addEventListener("resize", measure);
    vv?.addEventListener("scroll", measure);
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(raf);
      vv?.removeEventListener("resize", measure);
      vv?.removeEventListener("scroll", measure);
      window.removeEventListener("resize", measure);
    };
  }, [v3ChatId]);

  const loadDashboard = useCallback(async () => {
    const d = await fetchDashboard();
    setDash(d);
    setStats({
      total_users: d.total_users,
      pro_users: d.pro_users ?? 0,
      active_today: d.active_today ?? 0,
      total_kundli: d.total_kundli ?? 0,
      payments: d.payments,
    });
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

  const loadLifeMapOrders = useCallback(async () => {
    setLifeMapError(null);
    const data = await fetchLifeMapOrders({ status: "pending" });
    const sections = Array.isArray(data.sections) ? data.sections : [];
    setLifeMapSections(sections);
    setLifeMapTotal(data.total ?? 0);
    const unaccepted =
      typeof data.unaccepted_count === "number"
        ? data.unaccepted_count
        : sections.reduce(
            (n, sec) =>
              n +
              (sec.orders || []).filter((r) => !r.admin_accepted_at).length,
            0,
          );
    setLifeMapUnacceptedCount(unaccepted);
  }, []);

  const onAcceptLifeMap = useCallback(
    async (row: LifeMapOrderItem) => {
      const key = `${row.kind}:${row.order_id}`;
      setLifeMapAccepting(key);
      setLifeMapMsg(null);
      setLifeMapError(null);
      try {
        const result = await acceptLifeMapOrder({
          kind: row.kind,
          order_id: row.order_id,
        });
        if (!result.ok) {
          throw new Error(result.error || "Accept failed");
        }
        setLifeMapMsg(
          result.already
            ? `Already accepted — #${row.order_id.slice(0, 8)}`
            : `Approved — #${row.order_id.slice(0, 8)}. Ab report deliver karo.`,
        );
        await loadLifeMapOrders();
      } catch (e) {
        setLifeMapError(e instanceof Error ? e.message : "Accept failed");
      } finally {
        setLifeMapAccepting(null);
      }
    },
    [loadLifeMapOrders],
  );

  const onUnacceptLifeMap = useCallback(
    async (row: LifeMapOrderItem) => {
      const key = `${row.kind}:${row.order_id}`;
      setLifeMapAccepting(key);
      setLifeMapMsg(null);
      setLifeMapError(null);
      try {
        const result = await unacceptLifeMapOrder({
          kind: row.kind,
          order_id: row.order_id,
        });
        if (!result.ok) {
          throw new Error(result.error || "Undo failed");
        }
        setLifeMapMsg(`Approve reset — #${row.order_id.slice(0, 8)}. Ab Approve click karo.`);
        await loadLifeMapOrders();
      } catch (e) {
        setLifeMapError(e instanceof Error ? e.message : "Undo failed");
      } finally {
        setLifeMapAccepting(null);
      }
    },
    [loadLifeMapOrders],
  );

  const lifeMapAutoApproveBusy = useRef(false);
  useEffect(() => {
    if (!lifeMapAutoApprove || lifeMapAutoApproveBusy.current) return;
    const pending = lifeMapSections.flatMap((sec) =>
      (sec.orders || []).filter((row) => !row.admin_accepted_at),
    );
    if (!pending.length) return;
    lifeMapAutoApproveBusy.current = true;
    void (async () => {
      try {
        for (const row of pending) {
          await acceptLifeMapOrder({ kind: row.kind, order_id: row.order_id });
        }
        await loadLifeMapOrders();
      } catch (e) {
        setLifeMapError(e instanceof Error ? e.message : "Auto-approve failed");
      } finally {
        lifeMapAutoApproveBusy.current = false;
      }
    })();
  }, [lifeMapAutoApprove, lifeMapSections, loadLifeMapOrders]);

  const onDeliverLifeMap = useCallback(
    async (row: LifeMapOrderItem) => {
      const key = `${row.kind}:${row.order_id}`;
      if (!row.admin_accepted_at) {
        setLifeMapMsg("Pehle Approve karo — uske baad report paste / deliver open hoga.");
        return;
      }
      const pages = (lifeMapDrafts[key] || [""]).map((p) => p || "");
      const imagesRaw = lifeMapPageImages[key] || [];
      const pageImages = pages.map((_, i) => imagesRaw[i] || null);
      const body = pages.map((p) => p.trim()).filter(Boolean).join("\n\n");
      const hasImages = pageImages.some((x) => Boolean(x));
      if (body.length < 40 && !hasImages) {
        setLifeMapMsg(
          "Report text kam se kam 40 characters hona chahiye, ya kam se kam ek image add karo.",
        );
        return;
      }
      const attach = (lifeMapAttachUser[key] || "").trim();
      const hasUser =
        Boolean(row.user_id) ||
        Boolean((row.cosmo_user_id || "").trim()) ||
        Boolean(attach);
      if (row.kind === "palmistry" && !hasUser) {
        setLifeMapError(
          "Is order pe user id nahi hai (guest upload). Neeche User # / COSMO id likho, phir PDF banao.",
        );
        return;
      }
      if (
        !window.confirm(
          `PDF ${lifeMapPublicId(row)} ke My Reports mein bhejo (${pages.length} pages) aur notification bhejein?`,
        )
      ) {
        return;
      }
      setLifeMapDelivering(key);
      setLifeMapMsg(null);
      setLifeMapError(null);
      try {
        const result = await deliverLifeMapOrder({
          kind: row.kind,
          order_id: row.order_id,
          body: body || " ",
          pages,
          page_images: pageImages,
          ...(attach ? { attach_user_id: attach } : {}),
        });
        if (!result.ok) {
          const code = result.error || "Deliver failed";
          const detail = result.detail || "";
          if (code === "missing_user_id") {
            throw new Error(
              detail ||
                "User id missing — guest upload. User # / COSMO attach karke dubara try karo.",
            );
          }
          throw new Error(detail || code);
        }
        setLifeMapDrafts((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setLifeMapPageImages((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setLifeMapAttachUser((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        const uid = lifeMapPublicId(row);
        setLifeMapMsg(
          result.notified
            ? `PDF ${uid} ke My Reports mein deliver ho gayi. Notification bhej di.`
            : `PDF ${uid} ke My Reports mein deliver ho gayi. Notification nahi gayi (push off / token missing).`,
        );
        await loadLifeMapOrders();
      } catch (e) {
        setLifeMapError(e instanceof Error ? e.message : "Deliver failed");
      } finally {
        setLifeMapDelivering(null);
      }
    },
    [lifeMapDrafts, lifeMapPageImages, lifeMapAttachUser, loadLifeMapOrders],
  );

  const onDeleteLifeMap = useCallback(
    async (row: LifeMapOrderItem) => {
      const key = `${row.kind}:${row.order_id}`;
      if (
        !window.confirm(
          `Delete this pending order?\n\n${lifeMapPublicId(row)} · ${row.user_name || row.subject || row.order_id}\n\nIt will be removed from the queue.`,
        )
      ) {
        return;
      }
      setLifeMapDeleting(key);
      setLifeMapMsg(null);
      setLifeMapError(null);
      try {
        const result = await deleteLifeMapOrder({
          kind: row.kind,
          order_id: row.order_id,
        });
        if (!result.ok) {
          throw new Error(result.error || "Delete failed");
        }
        setLifeMapDrafts((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setLifeMapMsg(`Deleted order ${String(result.order_id || row.order_id).slice(0, 8)}…`);
        await loadLifeMapOrders();
      } catch (e) {
        setLifeMapError(e instanceof Error ? e.message : "Delete failed");
      } finally {
        setLifeMapDeleting(null);
      }
    },
    [loadLifeMapOrders],
  );

  const loadAskQuestions = useCallback(async () => {
    setAskQaError(null);
    const data = await fetchAskQuestions({
      page: askQaPage,
      email: askQaEmail || undefined,
    });
    if (!Array.isArray(data.items)) {
      setAskQaError(
        "Invalid API response — rebuild admin with VITE_API_BASE in artifacts/admin-web/.env, then npm run build",
      );
      setAskQuestions([]);
      setAskQaTotal(0);
      return;
    }
    setAskQuestions(data.items);
    setAskQaPages(data.pages);
    setAskQaTotal(data.total);
  }, [askQaPage, askQaEmail]);

  const loadBirthTimeRectificationOrders = useCallback(async () => {
    setBtOrdersError(null);
    const data = await fetchBirthTimeRectificationOrders({ page: btOrdersPage });
    setBtOrders(data.orders);
    setBtOrdersPages(data.pages);
    setBtOrdersTotal(data.total);
  }, [btOrdersPage]);

  const loadV3LiveSessions = useCallback(async () => {
    setV3Error(null);
    const [data, settings] = await Promise.all([
      fetchV3LiveSessions({ page: v3Page }),
      fetchV3ChatSettings(),
    ]);
    setV3Sessions(data.sessions);
    setV3Pages(data.pages);
    setV3Total(data.total);
    setV3Enabled(settings.enabled);
    setV3EngineBusy(Boolean(data.engine_busy));
    setV3QueueHeadId(data.queue_head_id ? String(data.queue_head_id) : null);
    if (typeof data.queued_count === "number") {
      setV3PendingCount(data.queued_count);
    }
  }, [v3Page]);

  const loadSupportThreads = useCallback(async () => {
    setSupportError(null);
    const data = await fetchSupportThreads({ page: 1 });
    const rows = Array.isArray(data.threads) ? data.threads : [];
    setSupportThreads(rows);
    const waiting =
      typeof data.waiting_admin_count === "number"
        ? data.waiting_admin_count
        : rows.filter((r) => (r.unread_admin || 0) > 0).length;
    setSupportWaitingCount(waiting);
  }, []);

  const refreshSupportChat = useCallback(async (threadId: string) => {
    try {
      const data = await fetchSupportMessages(threadId);
      setSupportMessages(Array.isArray(data.messages) ? data.messages : []);
      if (data.thread) setSupportThread(data.thread);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Support chat load failed";
      if (msg === "not_found" || /HTTP 404/.test(msg)) {
        setSupportThreadId((cur) => (cur === threadId ? null : cur));
        setSupportThread((cur) => (cur?.thread_id === threadId ? null : cur));
        setSupportMessages([]);
        void loadSupportThreads();
        return;
      }
      setSupportError(msg);
    }
  }, [loadSupportThreads]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "dashboard") await loadDashboard();
      else if (tab === "transactions") await loadTransactions();
      else if (tab === "users") await loadUsers();
      else if (tab === "logins") await loadLogins();
      else if (tab === "lifemap") await loadLifeMapOrders();
      else if (tab === "askqa") await loadAskQuestions();
      else if (tab === "btorders") await loadBirthTimeRectificationOrders();
      else if (tab === "v3live") await loadV3LiveSessions();
      else if (tab === "support") await loadSupportThreads();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load";
      if (tab === "askqa") setAskQaError(msg);
      else if (tab === "lifemap") setLifeMapError(msg);
      else if (tab === "btorders") setBtOrdersError(msg);
      else if (tab === "v3live")
        setV3Error(
          msg === "Unauthorized"
            ? "Unauthorized — admin panel login se session token lo (POST /api/admin/login). Server ADMIN_SECRET configured hona chahiye."
            : msg,
        );
      else if (tab === "support") setSupportError(msg);
      else setError(msg);
    } finally {
      setLoading(false);
    }
  }, [tab, loadDashboard, loadTransactions, loadUsers, loadLogins, loadLifeMapOrders, loadAskQuestions, loadBirthTimeRectificationOrders, loadV3LiveSessions, loadSupportThreads]);

  useEffect(() => {
    load();
  }, [load]);

  // Auto-refresh V3 list while on that tab (background poll handles badges elsewhere).
  useEffect(() => {
    if (tab !== "v3live") return;
    if (!adminPollVisible()) return;
    void loadV3LiveSessions().catch(() => {});
    const t = window.setInterval(() => {
      if (!adminPollVisible()) return;
      void loadV3LiveSessions().catch(() => {});
    }, ADMIN_TAB_POLL_MS);
    return () => window.clearInterval(t);
  }, [tab, loadV3LiveSessions]);

  // Auto-refresh PDF request queue while on that tab.
  useEffect(() => {
    if (tab !== "lifemap") return;
    if (!adminPollVisible()) return;
    void loadLifeMapOrders().catch(() => {});
    const t = window.setInterval(() => {
      if (!adminPollVisible()) return;
      void loadLifeMapOrders().catch(() => {});
    }, ADMIN_TAB_POLL_MS);
    return () => window.clearInterval(t);
  }, [tab, loadLifeMapOrders]);

  // Auto-refresh Support inbox list while on that tab.
  useEffect(() => {
    if (tab !== "support") return;
    if (!adminPollVisible()) return;
    void loadSupportThreads().catch(() => {});
    const t = window.setInterval(() => {
      if (!adminPollVisible()) return;
      void loadSupportThreads().catch(() => {});
    }, ADMIN_TAB_POLL_MS);
    return () => window.clearInterval(t);
  }, [tab, loadSupportThreads]);

  useEffect(() => {
    if (!supportThreadId) return;
    void refreshSupportChat(supportThreadId);
    const poll = setInterval(() => void refreshSupportChat(supportThreadId), ADMIN_CHAT_POLL_MS);
    return () => clearInterval(poll);
  }, [supportThreadId, refreshSupportChat]);

  useEffect(() => {
    const el = supportListRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [supportMessages]);

  useEffect(() => {
    if (!supportThreadId || supportThread?.status === "closed") return;
    const composing = supportDraft.trim().length > 0;
    if (!composing) {
      void setSupportAdminTyping(supportThreadId, false).catch(() => {});
      return;
    }
    void setSupportAdminTyping(supportThreadId, true).catch(() => {});
    const beat = setInterval(() => {
      void setSupportAdminTyping(supportThreadId, true).catch(() => {});
    }, 2500);
    return () => {
      clearInterval(beat);
      void setSupportAdminTyping(supportThreadId, false).catch(() => {});
    };
  }, [supportThreadId, supportDraft, supportThread?.status]);

  // Keep a ref in sync so the always-on poll below can see the open chat.
  useEffect(() => {
    v3ChatIdRef.current = v3ChatId;
    if (!v3ChatId) {
      setV3TemplatesOpen(false);
      setV3KundliOpen(false);
      setV3PositionsOpen(false);
      setV3KundliData(null);
      setV3KundliError(null);
    } else {
      v3TimerEndedRef.current = false;
    }
  }, [v3ChatId]);

  // Drop cached kundli when the open live chat switches to another user.
  useEffect(() => {
    const uid = v3ChatSession?.user_id;
    if (v3KundliData?.ok && uid != null && v3KundliData.user_id !== uid) {
      setV3KundliData(null);
      setV3KundliError(null);
    }
  }, [v3ChatSession?.user_id, v3KundliData?.ok, v3KundliData?.user_id]);

  // Local countdown: the moment remaining hits 0, close chat for admin
  // instantly (don't wait for the 2s messages poll).
  useEffect(() => {
    if (!v3ChatId || !v3ChatSession) return;
    if (v3ChatSession.status !== "accepted") return;
    if (!v3ChatSession.expires_at || v3TimerEndedRef.current) return;
    void v3ChatTick;
    const rem = Math.floor(
      (new Date(v3ChatSession.expires_at).getTime() - Date.now()) / 1000,
    );
    if (rem > 0) return;
    v3TimerEndedRef.current = true;
    setV3ChatId(null);
    setV3ChatSession(null);
    setV3ChatMessages([]);
    setV3TemplatesOpen(false);
    setV3KundliOpen(false);
    setV3PositionsOpen(false);
    setV3KundliData(null);
    setV3KundliError(null);
    alert("Time up — live session ended. Chat is closed.");
    void loadV3LiveSessions().catch(() => {});
  }, [v3ChatId, v3ChatSession, v3ChatTick, loadV3LiveSessions]);

  // Background watch for queued V3 count (sidebar badge + sound/desktop alert)
  // + auto-open the live chat panel the moment a user Accepts.
  useEffect(() => {
    let cancelled = false;
    void resyncPushSubscription().catch(() => {});
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
      void Notification.requestPermission().catch(() => {});
    }
    const pollPending = async () => {
      if (!adminPollVisible()) return;
      const activeTab = tabRef.current;

      // V3 badge + auto-open (skip when v3 tab already refreshes the full list).
      if (activeTab !== "v3live") {
        try {
          const data = await fetchV3LiveSessions({ page: 1 });
          if (cancelled) return;
          const rows = Array.isArray(data.sessions) ? data.sessions : [];
          const queuedRows = rows.filter(
            (r) => r.status === "queued" || r.status === "pending",
          );
          const count =
            typeof data.queued_count === "number"
              ? data.queued_count
              : queuedRows.length;
          setV3PendingCount(count);
          setV3EngineBusy(Boolean(data.engine_busy));
          setV3QueueHeadId(data.queue_head_id ? String(data.queue_head_id) : null);
          if (count > v3PrevPendingRef.current) {
            const sample =
              queuedRows[0]?.user_name || queuedRows[0]?.user_email || undefined;
            alertNewV3Requests(count - v3PrevPendingRef.current, sample);
          }
          v3PrevPendingRef.current = count;
          syncV3PendingAlarm(data.engine_busy ? 0 : count);

          const live = rows.find((r) => r.status === "accepted");
          if (
            live &&
            !v3ChatIdRef.current &&
            !v3AutoOpenedLiveRef.current.has(live.session_id)
          ) {
            v3AutoOpenedLiveRef.current.add(live.session_id);
            setTab("v3live");
            setV3ChatSession(live);
            setV3ChatMessages([]);
            setV3ChatId(live.session_id);
            playV3RingTone(2);
            showV3DesktopNotification({
              title: "V3 chat LIVE",
              body: `${live.user_name || live.user_email || "User"} ne Accept kar diya — timer chal raha hai, chat shuru karo!`,
            });
          }
        } catch {
          /* keep watching */
        }
      }

      // Support inbox badge (skip when support tab polls the full list).
      if (activeTab !== "support") {
        try {
          const sdata = await fetchSupportThreads({ page: 1, status: "open" });
          if (cancelled) return;
          const srows = Array.isArray(sdata.threads) ? sdata.threads : [];
          const waiting =
            typeof sdata.waiting_admin_count === "number"
              ? sdata.waiting_admin_count
              : srows.filter((r) => (r.unread_admin || 0) > 0).length;
          setSupportWaitingCount(waiting);
          if (waiting > supportPrevWaitingRef.current) {
            playV3RingTone(2);
            showV3DesktopNotification({
              title: "Help & Support",
              body: "New user message in Support inbox.",
            });
          }
          supportPrevWaitingRef.current = waiting;
        } catch {
          /* keep watching */
        }
      }

      // PDF Requests badge — lightweight summary (skip on lifemap tab).
      if (activeTab !== "lifemap") {
        try {
          const lm = await fetchLifeMapOrders({ status: "pending", summary: true });
          if (cancelled) return;
          const unaccepted =
            typeof lm.unaccepted_count === "number" ? lm.unaccepted_count : 0;
          setLifeMapUnacceptedCount(unaccepted);

          const pendingIds = Array.isArray(lm.pending_ids) ? lm.pending_ids : [];
          const seen = lifeMapSeenOrderIdsRef.current;
          const fresh = pendingIds.filter((id) => !seen.has(id));
          if (lifeMapPollReadyRef.current && fresh.length > 0) {
            playV3RingTone(2);
            showV3DesktopNotification({
              title: "PDF request",
              body:
                fresh.length === 1
                  ? "Naya PDF request aaya hai"
                  : `${fresh.length} naye PDF requests`,
              tag: "pdf-request",
            });
          }
          lifeMapPollReadyRef.current = true;
          lifeMapSeenOrderIdsRef.current = new Set(pendingIds);
        } catch {
          /* keep watching */
        }
      }
    };
    void pollPending();
    const t = window.setInterval(() => void pollPending(), ADMIN_BG_POLL_MS);
    const onVis = () => {
      if (adminPollVisible()) void pollPending();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => {
      cancelled = true;
      window.clearInterval(t);
      document.removeEventListener("visibilitychange", onVis);
      syncV3PendingAlarm(0);
    };
  }, []);

  function handleAdminLogout() {
    if (!window.confirm("Logout from admin panel?")) return;
    adminLogout();
    window.location.reload();
  }

  function closeUserDetailView() {
    setDirectLookupOpen(false);
    setDetailUserId(null);
    setDetail(null);
    setAskProfile(null);
    setDetailError(null);
  }

  async function onLookupUser() {
    const value = userIdInput.trim();
    if (!value) {
      setDetailError("Enter database ID or COSMO ID.");
      return;
    }
    setDirectLookupOpen(true);
    setDetailUserId(null);
    setDetail(null);
    setAskProfile(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const d = await lookupUser(value);
      setDetail(d);
      setDetailUserId(d.user.id);
      const ap = await fetchUserAskProfile(d.user.id).catch(() => null);
      setAskProfile(ap);
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "User lookup failed");
    } finally {
      setDetailLoading(false);
    }
  }

  async function onLookupOrder() {
    const value = orderLookupInput.trim();
    if (!value) {
      setOrderLookupError("Enter Order ID (UUID, prefix, or PALM-####).");
      setOrderLookupResult(null);
      return;
    }
    setOrderLookupLoading(true);
    setOrderLookupError(null);
    setOrderLookupResult(null);
    try {
      const row = await lookupOrder(value);
      setOrderLookupResult(row);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Order lookup failed";
      if (/404|not found/i.test(msg)) {
        setOrderLookupResult({
          ok: true,
          found: false,
          error: "order_not_found",
          message: "No order found for this Order ID.",
        });
        setOrderLookupError(null);
      } else {
        setOrderLookupError(msg);
      }
    } finally {
      setOrderLookupLoading(false);
    }
  }

  async function onShowDetail(user: AdminUser) {
    setDirectLookupOpen(false);
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

  async function onDelete(user: AdminUser) {
    const label = user.email || user.name || `#${user.id}`;
    const ok = window.confirm(
      `DELETE "${label}" completely?\n\n` +
        `• Account, profiles, kundli, purchases, login history\n` +
        `• If app is open → automatic logout + local reset\n` +
        `• Cannot be undone`,
    );
    if (!ok) return;
    const typed = window.prompt(`Type DELETE to confirm permanent wipe of "${label}":`);
    if ((typed || "").trim() !== "DELETE") {
      alert("Cancelled — typed confirmation did not match DELETE.");
      return;
    }
    setDeletingId(user.id);
    try {
      await deleteUser(user.id);
      if (detailUserId === user.id) {
        setDetailUserId(null);
        setDetail(null);
        setDirectLookupOpen(false);
        setAskProfile(null);
      }
      await loadUsers();
      if (tab === "logins") await loadLogins();
      if (tab === "dashboard") await loadDashboard();
      alert(
        `Deleted ${label}.\n\nApp pe open session 20–30s me logout ho jayegi (ya app foreground aate hi).`,
      );
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  async function onDeleteGmailLogin(row: LoginActivityItem) {
    const email = (row.email || "").trim();
    const label = loginRowId(row);
    const ok = window.confirm(
      `Delete "${label}" completely?\n\nRemoves the user account, ALL profiles, kundli data, and login history. The user will be logged out on the app and must sign in again. Cannot be undone.`,
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

  async function onDeliverBtOrder(orderId: string) {
    const body = (btDrafts[orderId] || "").trim();
    if (body.length < 40) {
      setBtDeliverError("Report text kam se kam 40 characters hona chahiye.");
      return;
    }
    if (!window.confirm("Generate PDF & deliver to user's My Reports?")) return;
    setBtDelivering(orderId);
    setBtDeliverMsg(null);
    setBtDeliverError(null);
    try {
      const result = await deliverLifeMapOrder({
        kind: "birth_time_rectification",
        order_id: orderId,
        body,
      });
      if (!result.ok) {
        throw new Error(result.detail || result.error || "Deliver failed");
      }
      setBtDrafts((prev) => {
        const next = { ...prev };
        delete next[orderId];
        return next;
      });
      setBtDeliverMsg(
        `Delivered — PDF saved to My Reports (report ${result.report_id?.slice(0, 8) || "ok"}).`,
      );
      await loadBirthTimeRectificationOrders();
    } catch (e) {
      setBtDeliverError(e instanceof Error ? e.message : "Deliver failed");
    } finally {
      setBtDelivering(null);
    }
  }

  async function onShowBtDetail(orderId: string) {
    if (btDetailId === orderId) {
      setBtDetailId(null);
      setBtDetail(null);
      return;
    }
    setBtDetailId(orderId);
    setBtDetail(null);
    setBtDetailLoading(true);
    try {
      setBtDetail(await fetchBirthTimeRectificationOrderDetail(orderId));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to load order");
      setBtDetailId(null);
    } finally {
      setBtDetailLoading(false);
    }
  }

  async function onAcceptV3(sessionId: string) {
    setV3BusyId(sessionId);
    try {
      const res = await acceptV3LiveSession(sessionId);
      await loadV3LiveSessions();
      // Open panel in waiting-for-user mode — composer stays disabled until accepted.
      setV3ChatId(sessionId);
      setV3ChatSession(res.session || null);
      setV3ChatMessages([]);
      syncV3PendingAlarm(0);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Accept failed";
      alert(
        msg.includes("engine_busy") || msg.includes("409")
          ? "Engine busy — end the current live/awaiting handoff first, or Accept only the queue head (#1)."
          : msg,
      );
    } finally {
      setV3BusyId(null);
    }
  }

  async function onRejectV3(sessionId: string) {
    if (!confirm("Reject this incoming V3 live chat?")) return;
    setV3BusyId(sessionId);
    try {
      await rejectV3LiveSession(sessionId);
      await loadV3LiveSessions();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Reject failed");
    } finally {
      setV3BusyId(null);
    }
  }

  async function onToggleV3Availability(enabled: boolean) {
    setV3SettingsBusy(true);
    try {
      const result = await setV3ChatEnabled(enabled);
      setV3Enabled(result.enabled);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Could not update V3 chat availability");
    } finally {
      setV3SettingsBusy(false);
    }
  }

  const refreshV3Chat = useCallback(async (sessionId: string) => {
    try {
      const data = await fetchV3ChatMessages(sessionId);
      const next = Array.isArray(data.messages) ? data.messages : [];
      // Only replace state when something actually changed — identical polls
      // must not re-render the list (that causes scroll jumping).
      setV3ChatMessages((prev) => {
        if (
          prev.length === next.length &&
          (prev.length === 0 ||
            (prev[prev.length - 1]?.id === next[next.length - 1]?.id &&
              prev[0]?.id === next[0]?.id))
        ) {
          return prev;
        }
        return next;
      });
      if (data.session) {
        setV3ChatSession(data.session);
        const st = String(data.session.status || "");
        // Timer expired / ended on server → close overlay immediately.
        if (st === "ended" || st === "rejected") {
          if (!v3TimerEndedRef.current) {
            v3TimerEndedRef.current = true;
            setV3ChatId(null);
            setV3ChatSession(null);
            setV3ChatMessages([]);
            setV3TemplatesOpen(false);
            setV3KundliOpen(false);
            setV3PositionsOpen(false);
            alert("Time up — live session ended. Chat is closed.");
            void loadV3LiveSessions().catch(() => {});
          }
        }
      }
    } catch (e) {
      setV3Error(e instanceof Error ? e.message : "Chat load failed");
    }
  }, [loadV3LiveSessions]);

  // While the chat overlay is open, freeze the page behind it so only the
  // messages panel scrolls (no page-level bounce / jumping).
  useEffect(() => {
    if (!v3ChatId) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    v3ChatStickBottomRef.current = true;
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [v3ChatId]);

  // New message aaye to bottom pe le jao — lekin sirf tab jab admin already
  // bottom ke paas ho. Upar scroll karke purane message padh rahe ho to
  // position bilkul nahi hilegi.
  useEffect(() => {
    const el = v3ChatListRef.current;
    if (!el || !v3ChatStickBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [v3ChatMessages]);

  useEffect(() => {
    if (!v3ChatId) return;
    void refreshV3Chat(v3ChatId);
    const poll = setInterval(() => void refreshV3Chat(v3ChatId), ADMIN_CHAT_POLL_MS);
    const tick = setInterval(() => setV3ChatTick((n) => n + 1), V3_TIMER_TICK_MS);
    return () => {
      clearInterval(poll);
      clearInterval(tick);
    };
  }, [v3ChatId, refreshV3Chat]);

  // Safety net: if the messages endpoint is an older build that doesn't return
  // `session`, hydrate chat status from the 4s list poll so the composer still
  // unlocks the moment the user Accepts (awaiting_user → accepted).
  useEffect(() => {
    if (!v3ChatId) return;
    const row = v3Sessions.find((r) => r.session_id === v3ChatId);
    if (!row) return;
    setV3ChatSession((prev) =>
      !prev || prev.status !== row.status ? { ...prev, ...row } : prev,
    );
  }, [v3ChatId, v3Sessions]);

  // While admin is typing, ping typing heartbeat so the user app shows
  // "Cosmic Intelligence calculating…" (same dots as V1 Ask).
  useEffect(() => {
    if (!v3ChatId || v3ChatSession?.status !== "accepted") return;
    const composing = v3ChatDraft.trim().length > 0;
    if (!composing) {
      void setV3AdminTyping(v3ChatId, false).catch(() => {});
      return;
    }
    void setV3AdminTyping(v3ChatId, true).catch(() => {});
    const beat = setInterval(() => {
      void setV3AdminTyping(v3ChatId, true).catch(() => {});
    }, 2500);
    return () => {
      clearInterval(beat);
      void setV3AdminTyping(v3ChatId, false).catch(() => {});
    };
  }, [v3ChatId, v3ChatDraft, v3ChatSession?.status]);

  async function onSendV3Chat() {
    if (!v3ChatId) return;
    const text = v3ChatDraft.trim();
    if (!text) return;
    setV3ChatSending(true);
    try {
      // Send exactly what the admin typed — no LLM/polish/token usage.
      await sendV3ChatMessage(v3ChatId, { text });
      setV3ChatDraft("");
      v3ChatStickBottomRef.current = true;
      await refreshV3Chat(v3ChatId);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Send failed");
    } finally {
      setV3ChatSending(false);
    }
  }

  async function loadV3Kundli() {
    const uid = v3ChatSession?.user_id;
    if (!uid) {
      setV3KundliError("No user_id on this session.");
      setV3KundliData(null);
      return;
    }
    setV3KundliLoading(true);
    setV3KundliError(null);
    try {
      const data = await fetchAdminUserChart(uid);
      setV3KundliData(data);
      if (!data?.ok) {
        setV3KundliError(data?.message || data?.error || "Chart unavailable");
      }
    } catch (e) {
      setV3KundliData(null);
      setV3KundliError(e instanceof Error ? e.message : "Failed to load kundli");
    } finally {
      setV3KundliLoading(false);
    }
  }

  async function openV3Kundli() {
    setV3TemplatesOpen(false);
    setV3PositionsOpen(false);
    setV3KundliOpen(true);
    await loadV3Kundli();
  }

  async function openV3Positions() {
    setV3TemplatesOpen(false);
    setV3KundliOpen(false);
    const uid = v3ChatSession?.user_id;
    const nextOpen = !v3PositionsOpen;
    setV3PositionsOpen(nextOpen);
    if (!nextOpen) return;
    const chartMatchesUser = v3KundliData?.ok && uid != null && v3KundliData.user_id === uid;
    if (!chartMatchesUser) await loadV3Kundli();
  }

  async function shareV3KundliImageToChat(dataUrl: string) {
    if (!v3ChatId || !dataUrl.startsWith("data:image/")) return;
    if (v3ChatSession?.status !== "accepted") {
      alert("Chat must be live (accepted) before sharing kundli.");
      return;
    }
    setV3KundliSharing(true);
    try {
      await sendV3ChatMessage(v3ChatId, { data_url: dataUrl, text: "" });
      v3ChatStickBottomRef.current = true;
      await refreshV3Chat(v3ChatId);
      setV3KundliOpen(false);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Chart image share failed");
    } finally {
      setV3KundliSharing(false);
    }
  }

  async function onV3ChatImage(file: File | null) {
    if (!v3ChatId || !file) return;
    if (!file.type.startsWith("image/")) {
      alert("Please pick an image file.");
      return;
    }
    setV3ChatSending(true);
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(new Error("read failed"));
        reader.readAsDataURL(file);
      });
      await sendV3ChatMessage(v3ChatId, { data_url: dataUrl, text: "" });
      v3ChatStickBottomRef.current = true;
      await refreshV3Chat(v3ChatId);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Image send failed");
    } finally {
      setV3ChatSending(false);
    }
  }

  async function onExtendV3(seconds: number) {
    if (!v3ChatId) return;
    try {
      const res = await extendV3LiveSession(v3ChatId, seconds);
      if (!res.ok) {
        alert(res.error === "extend_cap_reached" ? "Max +3 min already used." : res.error || "Extend failed");
        return;
      }
      if (res.session) setV3ChatSession(res.session);
      await refreshV3Chat(v3ChatId);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Extend failed");
    }
  }

  async function onEndV3Chat() {
    if (!v3ChatId) return;
    const waiting = v3ChatSession?.status === "awaiting_user";
    const confirmed = window.confirm(
      waiting
        ? "Cancel this handoff? The user will lose the Accept window and the next queued request can be Accepted."
        : "End this live session permanently? The user will be disconnected and this chat cannot be resumed.",
    );
    if (!confirmed) return;
    setV3ChatSending(true);
    try {
      await endV3LiveSession(v3ChatId);
      setV3ChatId(null);
      setV3ChatSession(null);
      setV3ChatMessages([]);
      await loadV3LiveSessions();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Could not end session");
    } finally {
      setV3ChatSending(false);
    }
  }

  function formatV3Timer(session: V3LiveSessionItem | null): string {
    void v3ChatTick;
    if (session?.status === "awaiting_user") {
      const rem =
        typeof session.awaiting_user_remaining_seconds === "number"
          ? session.awaiting_user_remaining_seconds
          : session.awaiting_user_expires_at
            ? Math.max(
                0,
                Math.floor(
                  (new Date(session.awaiting_user_expires_at).getTime() - Date.now()) / 1000,
                ),
              )
            : 0;
      const m = Math.floor(rem / 60);
      const s = rem % 60;
      return `wait ${m}:${String(s).padStart(2, "0")}`;
    }
    if (!session?.expires_at) return "--:--";
    const rem = Math.max(0, Math.floor((new Date(session.expires_at).getTime() - Date.now()) / 1000));
    const m = Math.floor(rem / 60);
    const s = rem % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function v3StatusLabel(status: string): string {
    if (status === "queued" || status === "pending") return "Queued";
    if (status === "awaiting_user") return "Waiting for user";
    if (status === "accepted") return "Live";
    return status;
  }

  function v3MediaSrc(url?: string): string {
    if (!url) return "";
    if (url.startsWith("http") || url.startsWith("data:")) return url;
    return `${getApiBase()}${url.startsWith("/") ? "" : "/"}${url}`;
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
        u.email || "",
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

    const purchases =
      detail.purchase_history?.map((p) => ({
        id: p.id,
        title: p.title,
        amount: p.amount_inr,
        when: p.paid_at,
        sub: p.subtitle,
        orderId: p.order_id,
      })) ?? [];
    const usage = detail.app_usage;

    return (
      <div className="user-detail-panel">
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            alignItems: "center",
            marginBottom: 12,
            padding: "10px 12px",
            borderRadius: 10,
            border: "1px solid rgba(220,38,38,0.35)",
            background: "rgba(220,38,38,0.08)",
          }}
        >
          <div style={{ flex: 1, minWidth: 180, fontSize: 12, lineHeight: 1.4 }}>
            <strong style={{ color: "#fca5a5" }}>Danger zone</strong>
            <div className="detail-muted">
              Full wipe — profiles, kundli, history. Open app → auto logout.
            </div>
          </div>
          <button
            type="button"
            className="danger"
            disabled={deletingId === detail.user.id}
            onClick={() =>
              void onDelete({
                id: detail.user.id,
                name: detail.user.name || "",
                email: detail.user.email || "",
                plan: detail.user.plan || "free",
                plan_expiry: detail.user.plan_expiry ?? null,
                last_login: detail.user.last_login,
                created_at: detail.user.created_at,
                kundli_profiles_count: detail.profiles?.length ?? 0,
                purchases: {
                  love_compatibility_pdf: 0,
                  milan_pro_pdf: 0,
                  face_reading_pro: 0,
                  life_mastery_pdf: 0,
                  total_paid_orders: 0,
                },
                career_unlocked: !!detail.user.career_unlocked,
              })
            }
          >
            {deletingId === detail.user.id ? "Deleting…" : "Delete user forever"}
          </button>
        </div>
        <div className="detail-account">
          <p>
            <strong>{detail.user.name || "Unnamed user"}</strong> · DB #{detail.user.id}
            {detail.user.cosmo_user_id ? ` · ${detail.user.cosmo_user_id}` : ""} · Plan:{" "}
            <span className="badge">{detail.user.plan}</span>
            {detail.user.career_unlocked ? " · Career ✓" : ""}
          </p>
          <p>
            <strong>Email:</strong> {detail.user.email || "—"} · <strong>Language:</strong>{" "}
            {detail.user.preferred_language || "auto"}
          </p>
          <p className="detail-muted">
            Joined: {formatDate(detail.user.created_at)} · Last login:{" "}
            {formatDate(detail.user.last_login)} · Plan expiry:{" "}
            {formatDate(detail.user.plan_expiry)}
          </p>
          <p className="detail-muted">
            Today: {detail.user.daily_questions_used} Ask · {detail.user.daily_kundlis_used} Kundli ·{" "}
            AstroVastu credits: {detail.user.astrovastu_room_credits}
          </p>
        </div>

        {detail.pack_referral ? (
          <>
            <p className="detail-summary">Pack referrals</p>
            <div className="user-usage-grid">
              <div className="stat-card">
                <h3>Code</h3>
                <div className="value" style={{ fontSize: 18 }}>
                  {detail.pack_referral.referral_code || "—"}
                </div>
              </div>
              <div className="stat-card">
                <h3>Referrals (signed up)</h3>
                <div className="value">{detail.pack_referral.friends_signed_up ?? 0}</div>
              </div>
              <div className="stat-card">
                <h3>Converted (bought pack)</h3>
                <div className="value">{detail.pack_referral.friends_converted ?? 0}</div>
              </div>
              <div className="stat-card">
                <h3>Q earned / bonus left</h3>
                <div className="value" style={{ fontSize: 16 }}>
                  {detail.pack_referral.questions_earned ?? 0} /{" "}
                  {detail.pack_referral.bonus_questions_left ?? 0}
                </div>
              </div>
            </div>
            {detail.pack_referral.referred_by_user_id ? (
              <p className="detail-muted" style={{ marginTop: 8 }}>
                This user was referred by DB #{detail.pack_referral.referred_by_user_id} (code CL
                {detail.pack_referral.referred_by_user_id})
              </p>
            ) : (
              <p className="detail-muted" style={{ marginTop: 8 }}>
                No referral code attached on signup.
              </p>
            )}
            {(detail.pack_referral.recent_signups?.length ?? 0) > 0 ? (
              <table className="detail-table detail-table-compact" style={{ marginTop: 10 }}>
                <thead>
                  <tr>
                    <th>Friend ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Signed up</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.pack_referral.recent_signups!.map((row) => (
                    <tr key={row.user_id}>
                      <td>{row.user_id}</td>
                      <td>{row.name || "—"}</td>
                      <td>{row.email || "—"}</td>
                      <td>{formatDate(row.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
            {(detail.pack_referral.recent_conversions?.length ?? 0) > 0 ? (
              <table className="detail-table detail-table-compact" style={{ marginTop: 10 }}>
                <thead>
                  <tr>
                    <th>Buyer ID</th>
                    <th>Source</th>
                    <th>Q granted</th>
                    <th>When</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.pack_referral.recent_conversions!.map((row) => (
                    <tr key={`${row.buyer_user_id}-${row.created_at}`}>
                      <td>{row.buyer_user_id}</td>
                      <td>{row.source_kind}</td>
                      <td>{row.questions_granted}</td>
                      <td>{formatDate(row.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </>
        ) : null}

        <p className="detail-summary">App usage</p>
        {usage?.tracking_started ? (
          <>
            <div className="user-usage-grid">
              <div className="stat-card">
                <h3>Today</h3>
                <div className="value">{formatDuration(usage.today_seconds)}</div>
              </div>
              <div className="stat-card">
                <h3>7 days</h3>
                <div className="value">{formatDuration(usage.last_7_days_seconds)}</div>
              </div>
              <div className="stat-card">
                <h3>Avg active day</h3>
                <div className="value">{formatDuration(usage.avg_seconds_per_active_day)}</div>
              </div>
              <div className="stat-card">
                <h3>30-day active days</h3>
                <div className="value">{usage.active_days_last_30}</div>
              </div>
            </div>
            <table className="detail-table detail-table-compact">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Foreground time</th>
                  <th>Sessions</th>
                </tr>
              </thead>
              <tbody>
                {usage.daily.map((row) => (
                  <tr key={row.date}>
                    <td>{row.date}</td>
                    <td>{formatDuration(row.seconds)}</td>
                    <td>{row.sessions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p className="detail-muted">
            Tracking starts after the updated mobile app is deployed and this user opens it.
          </p>
        )}

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

        <p className="detail-summary">Products &amp; access</p>
        <div className="product-access-grid">
          {(detail.product_access ?? []).map((item) => (
            <div key={item.key} className="engine-outcome-box">
              <span className={item.owned ? "badge ok" : "badge"}>
                {item.owned ? "Purchased / active" : "Not purchased"}
              </span>
              <p>
                <strong>{item.label}</strong>
                {item.detail ? ` · ${item.detail}` : ""}
              </p>
            </div>
          ))}
        </div>

        {purchases.length > 0 ? (
          <>
            <p className="detail-summary">
              Purchases ({detail.purchase_summary?.total_orders ?? purchases.length}) · Total{" "}
              {formatInr(detail.purchase_summary?.total_spent_inr ?? 0)}
            </p>
            <table className="detail-table detail-table-compact">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>₹</th>
                  <th>When</th>
                  <th>Order</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((p) => (
                  <tr key={p.id}>
                    <td>
                      {p.title}
                      {p.sub ? (
                        <span className="detail-muted"> · {p.sub}</span>
                      ) : null}
                    </td>
                    <td>{p.amount > 0 ? formatInr(p.amount) : "—"}</td>
                    <td>{formatDate(p.when)}</td>
                    <td className="detail-muted">{p.orderId || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p className="detail-muted">No paid purchase found for this user.</p>
        )}

        <p className="detail-summary">
          Service queues ({detail.service_queues?.length ?? 0})
        </p>
        {(detail.service_queues ?? []).length > 0 ? (
          <table className="detail-table detail-table-compact">
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Detail</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {(detail.service_queues ?? []).map((row, i) => (
                <tr key={`${row.kind}-${row.ref || i}`}>
                  <td>{row.label}</td>
                  <td>
                    <span className={row.status === "pending" ? "badge warn" : "badge ok"}>
                      {row.status || "—"}
                    </span>
                  </td>
                  <td>
                    {row.detail || "—"}
                    {row.ref ? (
                      <div className="detail-muted">{String(row.ref).slice(0, 10)}</div>
                    ) : null}
                  </td>
                  <td>{formatDate(row.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="detail-muted">No founder / intake / V3 queue items for this user.</p>
        )}

        <p className="detail-summary">Generated reports ({detail.cached_reports?.length ?? 0})</p>
        {(detail.cached_reports ?? []).length > 0 ? (
          <table className="detail-table detail-table-compact">
            <thead>
              <tr>
                <th>Report</th>
                <th>Profile</th>
                <th>Language</th>
                <th>Generated</th>
              </tr>
            </thead>
            <tbody>
              {(detail.cached_reports ?? []).map((report) => (
                <tr key={report.id}>
                  <td>{report.report_type || report.kind || "Report"}</td>
                  <td>
                    {report.name || "—"}
                    {report.dob ? ` · ${report.dob}` : ""}
                  </td>
                  <td>{report.language || "—"}</td>
                  <td>{formatDate(report.date ?? null)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="detail-muted">No generated PDF stored for this user.</p>
        )}

        {(detail.recent_logins ?? []).length > 0 ? (
          <>
            <p className="detail-summary">Recent logins</p>
            <table className="detail-table detail-table-compact">
              <thead>
                <tr>
                  <th>When (IST)</th>
                  <th>Method</th>
                  <th>Login ID</th>
                  <th>IP</th>
                  <th>OK</th>
                </tr>
              </thead>
              <tbody>
                {(detail.recent_logins ?? []).map((row) => (
                  <tr key={row.id}>
                    <td>{formatDate(row.created_at)}</td>
                    <td>{loginMethodLabel(row.login_method)}</td>
                    <td>{row.login_id || row.email || "—"}</td>
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

  const meta = TAB_META[tab] || { title: "Cosmic Admin", subtitle: "" };
  const proxyTarget = (import.meta.env.VITE_API_PROXY_TARGET || "").trim();
  const isLocalProxy =
    import.meta.env.DEV &&
    (!proxyTarget || /^(https?:\/\/)?(127\.0\.0\.1|localhost)(:\d+)?\/?$/i.test(proxyTarget));
  const apiBaseOk =
    Boolean(getApiBase()) ||
    isLocalProxy ||
    (typeof window !== "undefined" &&
      window.location.hostname.toLowerCase().endsWith("coosmic.icu"));

  return (
    <div className={`admin-shell${mobileNavOpen ? " mobile-nav-open" : ""}`}>
      <div className="cosmic-bg" aria-hidden />
      {loading ? <div className="loading-bar" aria-hidden /> : null}

      <button
        type="button"
        className="mobile-nav-backdrop"
        aria-label="Close menu"
        onClick={() => setMobileNavOpen(false)}
      />

      <aside className="sidebar">
        <button
          type="button"
          className="sidebar-close"
          aria-label="Close menu"
          onClick={() => setMobileNavOpen(false)}
        >
          ✕
        </button>
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
              setMobileNavOpen(false);
            }}
          >
            <span className="nav-icon" aria-hidden>
              {item.icon}
            </span>
            <span>{item.label}</span>
            {item.id === "v3live" && v3PendingCount > 0 ? (
              <span
                style={{
                  marginLeft: "auto",
                  minWidth: 20,
                  height: 20,
                  padding: "0 6px",
                  borderRadius: 999,
                  background: "#ef4444",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 800,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {v3PendingCount}
              </span>
            ) : null}
            {item.id === "lifemap" && lifeMapUnacceptedCount > 0 ? (
              <span
                style={{
                  marginLeft: "auto",
                  minWidth: 20,
                  height: 20,
                  padding: "0 6px",
                  borderRadius: 999,
                  background: "#ef4444",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 800,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {lifeMapUnacceptedCount}
              </span>
            ) : null}
            {item.id === "support" && supportWaitingCount > 0 ? (
              <span
                style={{
                  marginLeft: "auto",
                  minWidth: 20,
                  height: 20,
                  padding: "0 6px",
                  borderRadius: 999,
                  background: "#3b82f6",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 800,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {supportWaitingCount}
              </span>
            ) : null}
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
          <button
            type="button"
            className="nav-item nav-refresh"
            onClick={handleAdminLogout}
          >
            <span className="nav-icon" aria-hidden>
              ⎋
            </span>
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="mobile-topbar">
          <button
            type="button"
            className="mobile-menu-btn"
            aria-label="Open menu"
            onClick={() => setMobileNavOpen(true)}
          >
            ☰
          </button>
          <span className="mobile-topbar-title">{meta.title}</span>
          <button
            type="button"
            className="mobile-logout-btn"
            aria-label="Logout"
            onClick={handleAdminLogout}
          >
            Logout
          </button>
        </header>

        <header className="top-bar">
          <div className="top-bar-head">
            <div>
              <h2>{meta.title}</h2>
              <p className="subtitle">{meta.subtitle}</p>
            </div>
            <button type="button" className="top-bar-logout" onClick={handleAdminLogout}>
              Logout
            </button>
          </div>
        </header>

      {!apiBaseOk ? (
        <div className="error">
          <strong>API not configured.</strong> Create <code>artifacts/admin-web/.env</code> with{" "}
          <code>VITE_API_BASE</code> (production) or run{" "}
          <code>.\scripts\start-admin-local.ps1</code> for local dev (proxy to{" "}
          <code>http://127.0.0.1:8080</code>). Sign in with admin username/password — do not embed{" "}
          <code>ADMIN_SECRET</code> in the frontend build.
        </div>
      ) : null}

      {error && <div className="error">{error}</div>}

      {tab === "dashboard" && dash ? (
        <>
          <div className="grid stats">
            {dash.generated_at ? (
              <p className="detail-muted" style={{ gridColumn: "1 / -1", margin: "0 0 4px" }}>
                Live from database · updated {formatDate(dash.generated_at)}
              </p>
            ) : null}
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
          </div>
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
          <h2>Login history ({loginTotal})</h2>
          <p className="detail-muted">Phone OTP and Gmail sign-in attempts.</p>
          <div className="toolbar">
            <input
              type="search"
              placeholder="Filter email or phone…"
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
                  <th>Method</th>
                  <th>Login ID</th>
                  <th>IP</th>
                  <th>User ID</th>
                  <th>Profiles</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {logins.map((row) => {
                  const rowKey = `${row.id}-${row.user_id ?? ""}-${row.email ?? ""}`;
                  const busy = deletingLoginKey === rowKey;
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
                    <td>{loginMethodLabel(row.login_method)}</td>
                    <td>{row.login_id || row.email || row.phone || "—"}</td>
                    <td>{row.ip || "—"}</td>
                    <td>{row.cosmo_user_id || "—"}</td>
                    <td>{row.user_id ? row.profile_count ?? 0 : "—"}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="danger"
                          disabled={busy || (!row.user_id && !row.email && !row.phone)}
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

      {tab === "orderlookup" ? (
        <section className="section">
          <h2>Order lookup</h2>
          <p className="detail-muted">
            Enter Order ID (full UUID, short prefix, or palmistry public id like{" "}
            <code>PALM-1001</code>). Shows whether the order is still pending or
            successfully delivered.
          </p>
          <div className="card user-id-lookup">
            <div className="toolbar">
              <input
                type="search"
                inputMode="text"
                placeholder="Enter Order ID…"
                value={orderLookupInput}
                onChange={(e) => setOrderLookupInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void onLookupOrder();
                }}
                style={{ minWidth: 280, flex: 1 }}
              />
              <button
                type="button"
                className="primary"
                disabled={orderLookupLoading}
                onClick={() => void onLookupOrder()}
              >
                {orderLookupLoading ? "Checking…" : "Check status"}
              </button>
            </div>
            {orderLookupError ? <div className="error">{orderLookupError}</div> : null}
            {orderLookupResult ? (
              <div style={{ marginTop: 16 }}>
                {!orderLookupResult.found ? (
                  <div
                    style={{
                      padding: "16px 18px",
                      borderRadius: 12,
                      border: "1px solid #94a3b855",
                      background: "rgba(148,163,184,0.12)",
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#94a3b8", letterSpacing: 0.4 }}>
                      NOT FOUND
                    </div>
                    <p className="detail-muted" style={{ margin: "8px 0 0" }}>
                      {orderLookupResult.message || "No order found for this Order ID."}
                    </p>
                  </div>
                ) : (
                  (() => {
                    const state = orderLookupResult.delivery_state || "pending";
                    const tone =
                      state === "successful"
                        ? { bg: "rgba(34,197,94,0.14)", border: "#22c55e66", color: "#4ade80", label: "SUCCESSFUL" }
                        : state === "cancelled"
                          ? { bg: "rgba(239,68,68,0.12)", border: "#ef444466", color: "#f87171", label: "CANCELLED" }
                          : { bg: "rgba(245,158,11,0.14)", border: "#f59e0b66", color: "#fbbf24", label: "PENDING" };
                    const displayId =
                      orderLookupResult.public_order_id ||
                      (orderLookupResult.order_id
                        ? orderLookupResult.order_id.slice(0, 8).toUpperCase()
                        : "—");
                    return (
                      <div
                        style={{
                          padding: "18px 20px",
                          borderRadius: 12,
                          border: `1px solid ${tone.border}`,
                          background: tone.bg,
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: 12,
                            alignItems: "center",
                            justifyContent: "space-between",
                          }}
                        >
                          <div>
                            <div
                              style={{
                                fontSize: 12,
                                fontWeight: 800,
                                letterSpacing: 1,
                                color: tone.color,
                              }}
                            >
                              {tone.label}
                            </div>
                            <div style={{ marginTop: 6, fontSize: 18, fontWeight: 700 }}>
                              {orderLookupResult.label || orderLookupResult.kind || "Order"}
                            </div>
                          </div>
                          <div style={{ fontFamily: "ui-monospace, monospace", fontSize: 14 }}>
                            {displayId}
                          </div>
                        </div>
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                            gap: 12,
                            marginTop: 16,
                            fontSize: 13,
                          }}
                        >
                          <div>
                            <div className="detail-muted">Status</div>
                            <strong>{String(orderLookupResult.status || "—")}</strong>
                          </div>
                          <div>
                            <div className="detail-muted">User</div>
                            <strong>
                              {orderLookupResult.user_name || "—"}
                              {orderLookupResult.cosmo_user_id
                                ? ` · ${orderLookupResult.cosmo_user_id}`
                                : orderLookupResult.user_id
                                  ? ` · #${orderLookupResult.user_id}`
                                  : ""}
                            </strong>
                          </div>
                          <div>
                            <div className="detail-muted">Created</div>
                            <strong>
                              {orderLookupResult.created_at
                                ? formatDate(orderLookupResult.created_at)
                                : "—"}
                            </strong>
                          </div>
                          <div>
                            <div className="detail-muted">Delivered</div>
                            <strong>
                              {orderLookupResult.delivered_at
                                ? formatDate(orderLookupResult.delivered_at)
                                : "—"}
                            </strong>
                          </div>
                          <div>
                            <div className="detail-muted">Approved</div>
                            <strong>
                              {orderLookupResult.admin_accepted ? "Yes" : "No"}
                            </strong>
                          </div>
                          {orderLookupResult.amount_inr != null ? (
                            <div>
                              <div className="detail-muted">Amount</div>
                              <strong>₹{orderLookupResult.amount_inr}</strong>
                            </div>
                          ) : null}
                          {orderLookupResult.eta_label ? (
                            <div>
                              <div className="detail-muted">ETA</div>
                              <strong>{orderLookupResult.eta_label}</strong>
                            </div>
                          ) : null}
                          <div>
                            <div className="detail-muted">Full order id</div>
                            <strong style={{ wordBreak: "break-all" }}>
                              {orderLookupResult.order_id || "—"}
                            </strong>
                          </div>
                        </div>
                      </div>
                    );
                  })()
                )}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      {tab === "lifemap" ? (
        <section className="section">
          <h2>PDF Requests ({lifeMapTotal} pending)</h2>
          <p className="detail-muted">
            User ID app wali hi hai — COSMO110, COSMO114. Birth details poori
            card pe aati hain. Approve ke baad ek box: Send PDF usi user ke My
            Reports mein deliver hota hai + unko notification.
          </p>
          {lifeMapError ? <div className="error">{lifeMapError}</div> : null}
          {lifeMapMsg ? <div className="success">{lifeMapMsg}</div> : null}
          <div className="toolbar" style={{ gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <button type="button" className="primary" onClick={load} disabled={loading}>
              Refresh
            </button>
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
              <input
                type="checkbox"
                checked={lifeMapAutoApprove}
                onChange={(e) => {
                  const on = e.target.checked;
                  setLifeMapAutoApprove(on);
                  try {
                    window.localStorage.setItem("cosmic.admin.autoApprovePdf", on ? "1" : "0");
                  } catch {
                    /* ignore */
                  }
                  setLifeMapMsg(
                    on
                      ? "Auto-approve ON — nayi PDF requests Accepted ho jayengi."
                      : "Auto-approve OFF — Accepted sirf Approve click ke baad aayega.",
                  );
                }}
              />
              Auto-approve new requests
            </label>
          </div>

          <div className="lifemap-subtabs">
            {lifeMapSections.map((sec) => (
              <button
                key={sec.key}
                type="button"
                className={
                  lifeMapActive === sec.key
                    ? "lifemap-subtab active"
                    : "lifemap-subtab"
                }
                onClick={() => setLifeMapActive(sec.key)}
              >
                {sec.title}
                <span className="lifemap-count">{sec.total}</span>
              </button>
            ))}
          </div>

          {lifeMapSections
            .filter((sec) => sec.key === lifeMapActive)
            .map((sec) => (
              <div key={sec.key} className="lifemap-bookings">
                {sec.orders.length === 0 ? (
                  <div className="card lifemap-empty">
                    No pending bookings in this queue.
                  </div>
                ) : (
                  sec.orders.map((row) => {
                    const draftKey = `${row.kind}:${row.order_id}`;
                    const busy =
                      lifeMapDelivering === draftKey ||
                      lifeMapDeleting === draftKey ||
                      lifeMapAccepting === draftKey;
                    const accepted = Boolean(row.admin_accepted_at);
                    const p1 = row.p1;
                    const p2 = row.p2;
                    const person = row.person;
                    const publicId = lifeMapPublicId(row);
                    const birth = row.birth;
                    const isVideo = isLifeMapVideoOrder(row);
                    const productLabel = lifeMapProductLabel(row);
                    return (
                      <article key={draftKey} className="card lifemap-booking">
                        <header className="lifemap-booking-head">
                          <div>
                            <h3>
                              {(row.user_name || lifeMapPublicId(row))} ne{" "}
                              {productLabel} request kiya
                            </h3>
                            <div className="detail-muted">
                              {row.subject ? `${row.subject} · ` : ""}
                              {formatDate(row.created_at)}
                              {row.lang ? ` · ${row.lang}` : ""}
                              {` · ${lifeMapDeliveryLabel(row)}`}
                              {Number(row.amount_inr) > 0 ? ` · ₹${row.amount_inr}` : ""}
                              {isVideo ? " · 🎥 no PDF/report" : ""}
                            </div>
                          </div>
                          <div className="lifemap-head-actions">
                            {accepted ? (
                              <>
                                <span className="badge ok">Accepted</span>
                                {!lifeMapAutoApprove ? (
                                  <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => void onUnacceptLifeMap(row)}
                                  >
                                    Undo
                                  </button>
                                ) : null}
                              </>
                            ) : null}
                            {!accepted ? (
                              <button
                                type="button"
                                className="primary"
                                disabled={busy}
                                onClick={() => onAcceptLifeMap(row)}
                              >
                                {lifeMapAccepting === draftKey
                                  ? "Approving…"
                                  : "Approve"}
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="danger"
                              disabled={busy}
                              onClick={() => onDeleteLifeMap(row)}
                            >
                              {lifeMapDeleting === draftKey ? "Deleting…" : "Delete"}
                            </button>
                          </div>
                        </header>

                        <div
                          className="lifemap-pay-banner"
                          style={{
                            margin: "0 0 12px",
                            padding: "12px 14px",
                            borderRadius: 12,
                            border: row.urgent
                              ? "1px solid rgba(245,158,11,0.55)"
                              : "1px solid rgba(148,163,184,0.35)",
                            background: row.urgent
                              ? "rgba(245,158,11,0.12)"
                              : "rgba(148,163,184,0.08)",
                          }}
                        >
                          <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 4 }}>
                            {lifeMapAmountLabel(row) === "—"
                              ? "Amount: not recorded"
                              : `Amount paid: ${lifeMapAmountLabel(row)}`}
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 700 }}>
                            Delivery: {row.eta_label || lifeMapDeliveryLabel(row)}
                          </div>
                          {isVideo ? (
                            <div style={{ fontSize: 12, marginTop: 4, opacity: 0.9 }}>
                              Product: Personalized Video · no PDF/report
                            </div>
                          ) : (
                            <div style={{ fontSize: 12, marginTop: 4, opacity: 0.9 }}>
                              Product: {productLabel}
                            </div>
                          )}
                        </div>

                        <div className="lifemap-block-title">Account</div>
                        <div className="lifemap-booking-meta">
                          <div>
                            <strong>User name</strong>
                            <span>{row.user_name || "—"}</span>
                          </div>
                          <div>
                            <strong>User ID</strong>
                            {row.user_id ? (
                              <button
                                type="button"
                                className="link-btn"
                                onClick={() =>
                                  openUserFromTx(row.user_id, row.cosmo_user_id || "")
                                }
                              >
                                {lifeMapPublicId(row)}
                              </button>
                            ) : (
                              <span>{lifeMapPublicId(row)}</span>
                            )}
                          </div>
                          {row.user_email ? (
                            <div>
                              <strong>Email</strong>
                              <span>{row.user_email}</span>
                            </div>
                          ) : null}
                          <div>
                            <strong>{isVideo ? "Product" : "PDF"}</strong>
                            <span>{productLabel}</span>
                          </div>
                          {isVideo ? (
                            <div>
                              <strong>Includes</strong>
                              <span>No PDF / no report — WhatsApp video only</span>
                            </div>
                          ) : null}
                          <div>
                            <strong>Order</strong>
                            <span className="mono">
                              {row.public_order_id || row.order_id.slice(0, 8)}
                            </span>
                          </div>
                          <div>
                            <strong>Amount paid</strong>
                            <span>{lifeMapAmountLabel(row)}</span>
                          </div>
                          <div>
                            <strong>Delivery</strong>
                            <span>{row.eta_label || lifeMapDeliveryLabel(row)}</span>
                          </div>
                          {row.lang &&
                          row.kind !== "astrovastu_pro" &&
                          row.kind !== "business_vastu_pro" ? (
                            <div>
                              <strong>Language</strong>
                              <span>{row.lang}</span>
                            </div>
                          ) : null}
                        </div>

                        {row.kind !== "palmistry" ? (
                          <div className="lifemap-block-title">Birth details</div>
                        ) : null}

                        {(p1 || p2) && (
                          <div className="lifemap-people">
                            {p1 ? (
                              <LifeMapPersonCard
                                person={p1}
                                heading={`Person 1 — ${p1.name || "—"}`}
                              />
                            ) : null}
                            {p2 ? (
                              <LifeMapPersonCard
                                person={p2}
                                heading={`Person 2 — ${p2.name || "—"}`}
                              />
                            ) : null}
                          </div>
                        )}

                        {person && !p1 ? (
                          <div className="lifemap-people">
                            <LifeMapPersonCard
                              person={person}
                              heading={person.name || "Birth details"}
                            />
                          </div>
                        ) : null}

                        {!p1 && !person && hasBirthDetails(birth) ? (
                          <div className="lifemap-people">
                            <LifeMapPersonCard
                              person={birth!}
                              heading={birth?.name || "Account kundli"}
                            />
                          </div>
                        ) : null}

                        {row.kind === "astrovastu_pro" ||
                        row.kind === "business_vastu_pro" ? (
                          <div className="lifemap-block-title">Uploads</div>
                        ) : null}

                        {row.kind === "astrovastu_pro" ? (
                          <div className="lifemap-people">
                            <div className="lifemap-person">
                              <strong>
                                Room —{" "}
                                {(row.room_type || row.subject || "Room").replace(
                                  /_/g,
                                  " ",
                                )}
                              </strong>
                              <div>Direction: {row.direction || "—"}</div>
                              {row.sku ? <div>SKU: {row.sku}</div> : null}
                              {row.has_image ? (
                                <LifeMapMediaPreview
                                  media={lifeMapMedia[row.order_id]}
                                  loading={Boolean(lifeMapMediaLoading[row.order_id])}
                                  alt={`${row.room_type || "Room"} photo`}
                                  empty={
                                    row.media_kind === "pdf"
                                      ? "PDF loading…"
                                      : "Photo loading…"
                                  }
                                />
                              ) : (
                                <div className="detail-muted">No photo on file</div>
                              )}
                            </div>
                          </div>
                        ) : null}

                        {row.kind === "business_vastu_pro" ? (
                          <div className="lifemap-person">
                            <strong>
                              {(row.business_type || "Business").toUpperCase()} —{" "}
                              {row.property_name || row.subject}
                            </strong>
                            <div className="lifemap-media-grid">
                              {(row.photo_rooms && row.photo_rooms.length
                                ? row.photo_rooms
                                : Array.from(
                                    { length: row.photo_count || 0 },
                                    () => ({}),
                                  )
                              ).map((room, i) => {
                                const key = `${row.order_id}:${i}`;
                                const label =
                                  (room.room_type || `Photo ${i + 1}`).replace(
                                    /_/g,
                                    " ",
                                  );
                                return (
                                  <div key={key} className="lifemap-person">
                                    <strong>{label}</strong>
                                    {room.heading_deg != null ? (
                                      <div>Heading: {room.heading_deg}°</div>
                                    ) : null}
                                    <LifeMapMediaPreview
                                      media={lifeMapMedia[key]}
                                      loading={Boolean(lifeMapMediaLoading[key])}
                                      alt={label}
                                      empty="Photo loading…"
                                    />
                                  </div>
                                );
                              })}
                              {row.has_pdf ? (
                                <div className="lifemap-person">
                                  <strong>
                                    Floor plan
                                    {row.pdf_filename ? ` — ${row.pdf_filename}` : ""}
                                  </strong>
                                  <LifeMapMediaPreview
                                    media={lifeMapMedia[`${row.order_id}:plan`]}
                                    loading={Boolean(
                                      lifeMapMediaLoading[`${row.order_id}:plan`],
                                    )}
                                    alt="Floor plan PDF"
                                    empty="PDF loading…"
                                  />
                                </div>
                              ) : null}
                            </div>
                            {!row.photo_count && !row.has_pdf ? (
                              <div className="detail-muted">No photos on file</div>
                            ) : null}
                          </div>
                        ) : null}

                        {row.kind === "palmistry" ? (
                          <div className="lifemap-person">
                            <div className="lifemap-block-title">
                              {row.has_full_extraction
                                ? "BOTH HANDS — FULL EXTRACTION"
                                : "PALM SCAN"}
                            </div>
                            <div>
                              Writing hand: {(row.writing_hand || "—").toUpperCase()}
                            </div>
                            <div>
                              Left quality:{" "}
                              {Math.round((row.left_summary?.quality_score || 0) * 100)}%
                              {" · "}
                              {row.left_summary?.validation_status || (row.left_summary?.usable ? "usable" : "retake")}
                              {typeof row.left_summary?.major_line_count === "number"
                                ? ` · lines ${row.left_summary.major_line_count}`
                                : ""}
                            </div>
                            <div>
                              Right quality:{" "}
                              {Math.round((row.right_summary?.quality_score || 0) * 100)}%
                              {" · "}
                              {row.right_summary?.validation_status || (row.right_summary?.usable ? "usable" : "retake")}
                              {typeof row.right_summary?.major_line_count === "number"
                                ? ` · lines ${row.right_summary.major_line_count}`
                                : ""}
                            </div>

                            <div
                              style={{
                                marginTop: 12,
                                display: "flex",
                                flexWrap: "wrap",
                                gap: 10,
                                alignItems: "flex-start",
                              }}
                            >
                              <button
                                type="button"
                                className="primary"
                                disabled={!accepted}
                                onClick={() => {
                                  if (!accepted) {
                                    setLifeMapMsg("Pehle Approve karo — uske baad Analysis Workspace open hoga.");
                                    return;
                                  }
                                  setPalmistryWorkspaceId(row.order_id);
                                }}
                              >
                                Open Analysis Workspace
                              </button>
                              <button
                                type="button"
                                disabled={!accepted || busy}
                                onClick={() => {
                                  if (!accepted) {
                                    setLifeMapMsg("Pehle Approve karo.");
                                    return;
                                  }
                                  void (async () => {
                                    try {
                                      const pack = await fetchPalmistryExport(row.order_id);
                                      const blob = new Blob(
                                        [JSON.stringify(pack, null, 2)],
                                        { type: "application/json" },
                                      );
                                      const url = URL.createObjectURL(blob);
                                      const a = document.createElement("a");
                                      a.href = url;
                                      a.download = `palmistry_${row.order_id.slice(0, 8)}.json`;
                                      a.click();
                                      URL.revokeObjectURL(url);
                                    } catch (e) {
                                      setLifeMapError(
                                        e instanceof Error ? e.message : "Raw JSON export failed",
                                      );
                                    }
                                  })();
                                }}
                              >
                                Raw JSON
                              </button>
                            </div>
                          </div>
                        ) : null}

                        {!isVideo ? (
                          <LifeMapPdfDeliverBox
                            row={row}
                            draftKey={draftKey}
                            publicId={publicId}
                            accepted={accepted}
                            busy={busy}
                            delivering={lifeMapDelivering === draftKey}
                            pages={lifeMapDrafts[draftKey] || [""]}
                            pageImages={lifeMapPageImages[draftKey] || []}
                            attachUser={lifeMapAttachUser[draftKey] || ""}
                            onPagesChange={(pages) =>
                              setLifeMapDrafts((prev) => ({ ...prev, [draftKey]: pages }))
                            }
                            onPageImagesChange={(images) =>
                              setLifeMapPageImages((prev) => ({
                                ...prev,
                                [draftKey]: images,
                              }))
                            }
                            onAttachChange={(v) =>
                              setLifeMapAttachUser((prev) => ({ ...prev, [draftKey]: v }))
                            }
                            onDeliver={() => onDeliverLifeMap(row)}
                          />
                        ) : null}

                        {accepted && isVideo ? (
                          <div className="lifemap-person" style={{ marginTop: 12 }}>
                            <div className="lifemap-block-title">
                              Deliver on WhatsApp
                            </div>
                            <p className="detail-muted">
                              Yeh <strong>Personalized Video Explanation</strong> order hai.
                              <strong> Koi PDF ya report include nahi hai.</strong>{" "}
                              Video seedha user ke WhatsApp par bhejo (number app me user ne diya tha).
                            </p>
                          </div>
                        ) : null}

                        {!accepted && isVideo ? (
                          <p className="detail-muted" style={{ marginTop: 12 }}>
                            Pehle <strong>Approve</strong> karo. Yeh video order hai —
                            <strong> koi PDF/report include nahi</strong>. Delivery WhatsApp par hogi.
                          </p>
                        ) : null}
                      </article>
                    );
                  })
                )}
              </div>
            ))}
        </section>
      ) : null}

      {tab === "btorders" ? (
        <section className="section">
          <h2>Birth Time Rectification ({btOrdersTotal})</h2>
          <p className="detail-muted">
            User life-event forms for minute-accurate birth time correction. Expand a row to read milestones + last-15-years notes.
          </p>
          {btOrdersError ? <div className="error">{btOrdersError}</div> : null}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Name</th>
                  <th>DOB / Time</th>
                  <th>Place</th>
                  <th>Events</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {btOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7}>No requests yet.</td>
                  </tr>
                ) : (
                  btOrders.map((row) => (
                    <Fragment key={row.order_id}>
                      <tr>
                        <td>{formatDate(row.created_at)}</td>
                        <td>
                          {row.full_name || "—"}
                          {row.user_id ? (
                            <div className="detail-muted">
                              user #{row.user_id}
                              {row.cosmo_user_id ? ` · ${row.cosmo_user_id}` : ""}
                            </div>
                          ) : null}
                        </td>
                        <td>
                          {row.dob || "—"}
                          {row.approx_tob ? (
                            <div className="detail-muted">{row.approx_tob}</div>
                          ) : null}
                        </td>
                        <td>{row.birth_place || "—"}</td>
                        <td>
                          {row.event_count}
                          {row.has_15y_notes ? " + notes" : ""}
                        </td>
                        <td>
                          <span className={row.status === "pending" ? "badge warn" : "badge ok"}>
                            {row.status}
                          </span>
                        </td>
                        <td>
                          <button
                            type="button"
                            className={btDetailId === row.order_id ? "primary" : ""}
                            onClick={() => onShowBtDetail(row.order_id)}
                          >
                            {btDetailId === row.order_id ? "Hide" : "View"}
                          </button>
                        </td>
                      </tr>
                      {btDetailId === row.order_id ? (
                        <tr className="detail-row">
                          <td colSpan={7}>
                            {btDetailLoading ? (
                              <p className="detail-muted">Loading…</p>
                            ) : btDetail ? (
                              <div className="user-detail-panel" style={{ fontSize: 13, lineHeight: 1.5 }}>
                                <p className="detail-summary" style={{ fontSize: 13 }}>
                                  <strong>{btDetail.full_name}</strong>
                                  {btDetail.gender ? ` · ${btDetail.gender}` : ""}
                                  {" · "}
                                  {btDetail.dob || "—"}
                                  {btDetail.approx_tob ? ` · ~${btDetail.approx_tob}` : ""}
                                  {" · "}
                                  {btDetail.birth_place || "—"}
                                </p>
                                {btDetail.user_email ? (
                                  <p className="detail-muted" style={{ fontSize: 12 }}>
                                    {btDetail.user_email}
                                  </p>
                                ) : null}
                                <h3 style={{ marginTop: 12, fontSize: 14 }}>Milestone events</h3>
                                {(btDetail.milestone_events ?? []).length === 0 ? (
                                  <p className="detail-muted" style={{ fontSize: 12.5 }}>
                                    No checklist events selected.
                                  </p>
                                ) : (
                                  <ul style={{ fontSize: 12.5, paddingLeft: 18, margin: "6px 0" }}>
                                    {(btDetail.milestone_events ?? []).map((ev, i) => (
                                      <li key={`${ev.id || ev.label}-${i}`}>
                                        <strong>{ev.label}</strong>
                                        {" — "}
                                        {ev.month_year || "no date"}
                                        {ev.impact ? ` · ${ev.impact}` : ""}
                                      </li>
                                    ))}
                                  </ul>
                                )}
                                <h3 style={{ marginTop: 12, fontSize: 14 }}>Last 15 years — top events</h3>
                                <pre
                                  style={{
                                    whiteSpace: "pre-wrap",
                                    wordBreak: "break-word",
                                    background: "rgba(0,0,0,0.04)",
                                    padding: 10,
                                    borderRadius: 8,
                                    fontSize: 12,
                                    lineHeight: 1.5,
                                    maxHeight: 260,
                                    overflow: "auto",
                                  }}
                                >
                                  {btDetail.last_15y_events_text?.trim() || "(empty)"}
                                </pre>

                                <h3 style={{ marginTop: 12, fontSize: 14 }}>
                                  Write report → My Reports PDF
                                </h3>
                                {btDeliverMsg ? (
                                  <p style={{ color: "#16a34a", fontSize: 12.5 }}>{btDeliverMsg}</p>
                                ) : null}
                                {btDeliverError ? (
                                  <div className="error" style={{ fontSize: 12.5 }}>{btDeliverError}</div>
                                ) : null}
                                {row.status === "delivered" ? (
                                  <p className="detail-muted" style={{ fontSize: 12.5 }}>
                                    Already delivered — PDF user ke My Reports mein hai.
                                  </p>
                                ) : (
                                  <>
                                    <textarea
                                      className="lifemap-report-input"
                                      rows={8}
                                      style={{ width: "100%", fontSize: 13, lineHeight: 1.5 }}
                                      placeholder={"## Topic One\nParagraph…\n\n## Topic Two\nParagraph… — headings se PDF auto structure hoga."}
                                      value={btDrafts[row.order_id] || ""}
                                      onChange={(e) =>
                                        setBtDrafts((prev) => ({
                                          ...prev,
                                          [row.order_id]: e.target.value,
                                        }))
                                      }
                                      disabled={btDelivering === row.order_id}
                                    />
                                    <div style={{ marginTop: 8 }}>
                                      <button
                                        type="button"
                                        className="primary"
                                        disabled={
                                          btDelivering === row.order_id ||
                                          !(btDrafts[row.order_id] || "").trim()
                                        }
                                        onClick={() => void onDeliverBtOrder(row.order_id)}
                                      >
                                        {btDelivering === row.order_id
                                          ? "Generating PDF…"
                                          : "Generate PDF & Deliver"}
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            ) : (
                              <p className="detail-muted">Could not load detail.</p>
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
          {btOrdersPages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={btOrdersPage <= 1 || loading}
                onClick={() => setBtOrdersPage((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {btOrdersPage} / {btOrdersPages}
              </span>
              <button
                type="button"
                disabled={btOrdersPage >= btOrdersPages || loading}
                onClick={() => setBtOrdersPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "v3live" ? (
        <section className="section">
          <h2>V3 Live Chats ({v3Total})</h2>
          <div
            className="card"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 16,
              flexWrap: "wrap",
              marginBottom: 12,
              borderColor: v3Enabled ? "rgba(34,197,94,.55)" : "rgba(239,68,68,.55)",
            }}
          >
            <div>
              <strong>{v3Enabled ? "V3 live chat enabled" : "V3 live chat closed"}</strong>
              <div className="detail-muted">
                {v3Enabled
                  ? "Users can place new V3 requests."
                  : "Close chat = users still join the waitlist and see “busy with another consultation” (never offline). You still get attempt alerts."}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                className={v3Enabled ? "primary" : ""}
                disabled={v3SettingsBusy || v3Enabled}
                onClick={() => void onToggleV3Availability(true)}
              >
                Enable chat
              </button>
              <button
                type="button"
                disabled={v3SettingsBusy || !v3Enabled}
                onClick={() => void onToggleV3Availability(false)}
              >
                Close chat
              </button>
            </div>
          </div>

          <p className="detail-muted">
            FIFO queue: Accept only #1 when engine is free. That notifies the user; live timer
            starts after they tap Accept & Start (2 min). Queue grows even if chat is closed.
            {v3EngineBusy ? " · Engine busy (live or waiting for user)." : ""}
            {v3PendingCount > 0 ? ` · ${v3PendingCount} queued.` : ""}
            Auto-refreshes every 4s.
          </p>
          {v3Error ? <div className="error">{v3Error}</div> : null}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>FIFO</th>
                  <th>When</th>
                  <th>User</th>
                  <th>Pack / Timer</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {v3Sessions.length === 0 ? (
                  <tr>
                    <td colSpan={7}>No incoming requests yet.</td>
                  </tr>
                ) : (
                  v3Sessions.map((row) => {
                    const queued = row.status === "queued" || row.status === "pending";
                    const isHead =
                      Boolean(row.is_queue_head) ||
                      (queued && v3QueueHeadId === row.session_id);
                    const canAccept =
                      queued && isHead && !v3EngineBusy && !loading;
                    return (
                    <tr key={row.session_id}>
                      <td>
                        {queued && row.queue_position != null ? (
                          <strong>#{row.queue_position}</strong>
                        ) : (
                          <span className="detail-muted">—</span>
                        )}
                        {isHead ? (
                          <div className="detail-muted">queue head</div>
                        ) : null}
                      </td>
                      <td>{formatDate(row.created_at)}</td>
                      <td>
                        {row.user_name || row.user_email || "—"}
                        {row.user_id ? (
                          <div className="detail-muted">
                            user #{row.user_id}
                            {row.cosmo_user_id ? ` · ${row.cosmo_user_id}` : ""}
                          </div>
                        ) : null}
                      </td>
                      <td>
                        {row.label || `${row.minutes || "—"} min`}
                        <div className="detail-muted">pack {row.pack_id || "—"}</div>
                        {row.preferred_language ? (
                          <div className="detail-muted">
                            lang{" "}
                            {row.preferred_language === "hi"
                              ? "हिंदी"
                              : row.preferred_language === "en"
                                ? "English"
                                : row.preferred_language === "hn"
                                  ? "Hinglish"
                                  : row.preferred_language}
                          </div>
                        ) : null}
                      </td>
                      <td>₹{(row.price_inr ?? 0).toLocaleString("en-IN")}</td>
                      <td>
                        <span
                          className={
                            queued
                              ? "badge warn"
                              : row.status === "awaiting_user"
                                ? "badge warn"
                                : row.status === "accepted"
                                  ? "badge ok"
                                  : "badge"
                          }
                        >
                          {v3StatusLabel(row.status)}
                        </span>
                        {row.status === "awaiting_user" &&
                        typeof row.awaiting_user_remaining_seconds === "number" ? (
                          <div className="detail-muted">
                            user Accept: {Math.max(0, Math.ceil(row.awaiting_user_remaining_seconds))}s
                          </div>
                        ) : null}
                      </td>
                      <td>
                        {queued ? (
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            <button
                              type="button"
                              className="primary"
                              disabled={!canAccept || v3BusyId === row.session_id}
                              title={
                                !isHead
                                  ? "Only queue head (#1) can be Accepted"
                                  : v3EngineBusy
                                    ? "End current live/awaiting handoff first"
                                    : "Notify user — timer starts when they Accept"
                              }
                              onClick={() => onAcceptV3(row.session_id)}
                            >
                              {v3BusyId === row.session_id ? "…" : "Accept"}
                            </button>
                            <button
                              type="button"
                              disabled={v3BusyId === row.session_id || loading}
                              onClick={() => onRejectV3(row.session_id)}
                            >
                              Reject
                            </button>
                          </div>
                        ) : row.status === "awaiting_user" || row.status === "accepted" ? (
                          <button
                            type="button"
                            className="primary"
                            onClick={() => {
                              setV3ChatId(row.session_id);
                              setV3ChatSession(row);
                              setV3ChatMessages([]);
                            }}
                          >
                            {row.status === "awaiting_user" ? "Open (waiting)" : "Open chat"}
                          </button>
                        ) : (
                          <span className="detail-muted">—</span>
                        )}
                      </td>
                    </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          {v3Pages > 1 ? (
            <div className="pager">
              <button
                type="button"
                disabled={v3Page <= 1 || loading}
                onClick={() => setV3Page((p) => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span>
                Page {v3Page} / {v3Pages}
              </span>
              <button
                type="button"
                disabled={v3Page >= v3Pages || loading}
                onClick={() => setV3Page((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}

          {v3ChatId ? createPortal(
            // Portal to <body>: parents (.section/.main-area) carry transform
            // animations which hijack position:fixed — inside them the overlay
            // grows past the phone viewport and the composer lands off-screen.
            <div
              style={{
                position: "fixed",
                // Pinned to the *visible* viewport (keyboard/URL-bar aware) —
                // the chat never slides when the browser scrolls the page.
                top: v3ViewportTop,
                left: 0,
                right: 0,
                // Measured visible viewport — URL bar / toolbars / keyboard
                // never push the composer off-screen (100vh lies on mobile).
                height: v3ViewportH ? `${v3ViewportH}px` : "100dvh",
                zIndex: 2147483000,
                background: "#080a12",
                display: "flex",
                alignItems: "stretch",
                justifyContent: "stretch",
                overscrollBehavior: "none",
                touchAction: "manipulation",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  padding: 0,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid var(--border, #2a2f3a)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 12,
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <strong>
                      {v3ChatSession?.status === "awaiting_user"
                        ? "Waiting for user Accept"
                        : "Live chat"}{" "}
                      <span className="detail-muted" style={{ fontSize: 10 }}>
                        v2
                      </span>
                    </strong>
                    <div className="detail-muted">
                      {v3ChatSession?.user_name || v3ChatSession?.user_email || "User"} ·{" "}
                      {v3ChatSession?.label || `${v3ChatSession?.minutes || "—"} min`}
                      {v3ChatSession?.preferred_language
                        ? ` · ${
                            v3ChatSession.preferred_language === "hi"
                              ? "हिंदी"
                              : v3ChatSession.preferred_language === "en"
                                ? "English"
                                : v3ChatSession.preferred_language === "hn"
                                  ? "Hinglish"
                                  : v3ChatSession.preferred_language
                          }`
                        : ""}
                    </div>
                    {v3ChatSession?.status === "awaiting_user" ? (
                      <div className="detail-muted" style={{ color: "#fbbf24", marginTop: 4 }}>
                        User notified — composer unlocks when they Accept & Start (2 min).
                      </div>
                    ) : null}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <span
                      style={{
                        fontFamily: "ui-monospace, monospace",
                        fontWeight: 700,
                        fontSize: 18,
                        color: (v3ChatSession?.remaining_seconds ?? 1) <= 60 ? "#f59e0b" : "inherit",
                      }}
                    >
                      ⏱ {formatV3Timer(v3ChatSession)}
                    </span>
                    <button
                      type="button"
                      title="Planetary positions table — Sign, Nakshatra, House, State, Status + Copy All"
                      onClick={() => void openV3Positions()}
                      style={{
                        fontWeight: 800,
                        fontSize: 13,
                        padding: "8px 14px",
                        borderRadius: 8,
                        border: "1px solid #06b6d4",
                        background: v3PositionsOpen
                          ? "linear-gradient(90deg,#0e7490,#06b6d4)"
                          : "rgba(6,182,212,0.15)",
                        color: v3PositionsOpen ? "#fff" : "#67e8f9",
                      }}
                    >
                      Position
                    </button>
                    <button
                      type="button"
                      title="Open user kundli (D1, D9, KP, dasha) — Share sends to chat"
                      onClick={() => void openV3Kundli()}
                      style={{
                        fontWeight: 900,
                        fontSize: 13,
                        padding: "8px 14px",
                        borderRadius: 8,
                        border: "1px solid #f59e0b",
                        background: "linear-gradient(90deg,#b45309,#f59e0b)",
                        color: "#fff",
                        boxShadow: "0 0 0 1px rgba(245,158,11,0.35)",
                      }}
                    >
                      ☯ Kundli
                    </button>
                    <button
                      type="button"
                      disabled={(v3ChatSession?.extend_seconds_left ?? 0) < 120}
                      title="Add +2 minutes (max +3 min total)"
                      onClick={() => void onExtendV3(120)}
                    >
                      +2 min
                    </button>
                    <button
                      type="button"
                      disabled={v3ChatSession?.status !== "accepted"}
                      title="Insert a predefined English message into the draft"
                      onClick={() => setV3TemplatesOpen((o) => !o)}
                      style={{
                        fontWeight: 700,
                        borderColor: v3TemplatesOpen ? "rgba(167,139,250,0.7)" : undefined,
                        background: v3TemplatesOpen ? "rgba(167,139,250,0.18)" : undefined,
                      }}
                    >
                      Templates
                    </button>
                    <button
                      type="button"
                      disabled={
                        v3ChatSending ||
                        (v3ChatSession?.status !== "accepted" &&
                          v3ChatSession?.status !== "awaiting_user")
                      }
                      onClick={() => void onEndV3Chat()}
                      style={{
                        background: "#dc2626",
                        borderColor: "#dc2626",
                        color: "#fff",
                        fontWeight: 700,
                      }}
                    >
                      {v3ChatSession?.status === "awaiting_user" ? "Cancel handoff" : "End session"}
                    </button>
                    <button type="button" onClick={() => setV3ChatId(null)}>
                      Back to requests
                    </button>
                  </div>
                </div>
                {(v3ChatSession?.extend_seconds_left ?? 0) <= 0 ? (
                  <div className="detail-muted" style={{ padding: "6px 16px" }}>
                    Extend cap reached (+3 min max used).
                  </div>
                ) : (
                  <div className="detail-muted" style={{ padding: "6px 16px" }}>
                    Extend left: {Math.floor((v3ChatSession?.extend_seconds_left ?? 0) / 60)} min{" "}
                    {(v3ChatSession?.extend_seconds_left ?? 0) % 60}s (max +3 min)
                  </div>
                )}
                <V3PositionsPanel
                  open={v3PositionsOpen}
                  loading={v3KundliLoading}
                  error={v3KundliError}
                  data={v3KundliData}
                  onClose={() => setV3PositionsOpen(false)}
                  onReload={() => void loadV3Kundli()}
                />
                {v3TemplatesOpen ? (
                  <div
                    style={{
                      padding: "10px 16px 12px",
                      borderBottom: "1px solid var(--border, #2a2f3a)",
                      background: "rgba(0,0,0,0.25)",
                      maxHeight: 220,
                      overflowY: "auto",
                    }}
                  >
                    <div className="detail-muted" style={{ marginBottom: 8, fontSize: 12 }}>
                      Tap a template — it fills the draft. Edit if needed, then Send.
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      <button
                        type="button"
                        disabled={!v3ChatSession?.user_id}
                        title="Open full kundli viewer"
                        onClick={() => void openV3Kundli()}
                        style={{
                          fontSize: 12,
                          fontWeight: 800,
                          borderColor: "rgba(245,158,11,0.7)",
                          background: "rgba(245,158,11,0.18)",
                          color: "#fde68a",
                        }}
                      >
                        Kundli (D1 · D9 · KP · Dasha)
                      </button>
                      {V3_CHAT_TEMPLATES.map((tpl) => (
                        <button
                          key={tpl.id}
                          type="button"
                          disabled={v3ChatSession?.status !== "accepted"}
                          title={tpl.text}
                          onClick={() => {
                            setV3ChatDraft(tpl.text);
                            setV3TemplatesOpen(false);
                          }}
                          style={{ fontSize: 12, fontWeight: 600 }}
                        >
                          {tpl.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div
                  ref={v3ChatListRef}
                  onScroll={(e) => {
                    const el = e.currentTarget;
                    v3ChatStickBottomRef.current =
                      el.scrollHeight - el.scrollTop - el.clientHeight < 48;
                  }}
                  style={{
                    flex: 1,
                    minHeight: 0,
                    overflowY: "auto",
                    overscrollBehavior: "contain",
                    WebkitOverflowScrolling: "touch",
                    padding: 16,
                    display: "flex",
                    flexDirection: "column",
                    gap: 10,
                    background: "rgba(0,0,0,0.15)",
                  }}
                >
                  {v3ChatMessages.length === 0 ? (
                    <div className="detail-muted">No messages yet. Say hello to start.</div>
                  ) : (
                    v3ChatMessages.map((m) => {
                      const mine = m.sender === "admin";
                      const sys = m.sender === "system";
                      return (
                        <div
                          key={m.id}
                          style={{
                            alignSelf: sys ? "center" : mine ? "flex-end" : "flex-start",
                            maxWidth: sys ? "90%" : "78%",
                            padding: sys ? "6px 10px" : "8px 12px",
                            borderRadius: 12,
                            background: sys
                              ? "transparent"
                              : mine
                                ? "rgba(59,130,246,0.25)"
                                : "rgba(255,255,255,0.08)",
                            border: sys ? "none" : "1px solid rgba(255,255,255,0.08)",
                            fontSize: sys ? 12 : 14,
                            opacity: sys ? 0.75 : 1,
                            textAlign: sys ? "center" : "left",
                          }}
                        >
                          {!sys ? (
                            <div className="detail-muted" style={{ fontSize: 11, marginBottom: 4 }}>
                              {mine ? "You (admin)" : "User"}
                            </div>
                          ) : null}
                          {m.text ? <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div> : null}
                          {m.image_url ? (
                            <a href={v3MediaSrc(m.image_url)} target="_blank" rel="noreferrer">
                              <img
                                src={v3MediaSrc(m.image_url)}
                                alt="chat"
                                onLoad={() => {
                                  // Image load se list ki height badhti hai —
                                  // bottom pe ho to bottom pe hi raho.
                                  const el = v3ChatListRef.current;
                                  if (el && v3ChatStickBottomRef.current) {
                                    el.scrollTop = el.scrollHeight;
                                  }
                                }}
                                style={{
                                  maxWidth: 220,
                                  maxHeight: 220,
                                  borderRadius: 8,
                                  marginTop: m.text ? 8 : 0,
                                  display: "block",
                                }}
                              />
                            </a>
                          ) : null}
                        </div>
                      );
                    })
                  )}
                </div>
                <div
                  style={{
                    padding: 12,
                    paddingBottom: "calc(12px + env(safe-area-inset-bottom, 0px))",
                    borderTop: "1px solid var(--border, #2a2f3a)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
                  <label style={{ cursor: "pointer" }} title="Send image">
                    <input
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      disabled={v3ChatSending || v3ChatSession?.status !== "accepted"}
                      onChange={(e) => {
                        const f = e.target.files?.[0] || null;
                        e.target.value = "";
                        void onV3ChatImage(f);
                      }}
                    />
                    <span className="button-like" style={{ padding: "8px 10px", display: "inline-block" }}>
                      🖼
                    </span>
                  </label>
                  <textarea
                    value={v3ChatDraft}
                    onChange={(e) => setV3ChatDraft(e.target.value)}
                    placeholder=""
                    rows={2}
                    // 16px minimum — smaller fonts make iOS zoom the whole
                    // page on focus (the "screen jumps while typing" bug).
                    style={{ flex: 1, resize: "none", fontSize: 16 }}
                    onFocus={() => {
                      const el = v3ChatListRef.current;
                      if (el && v3ChatStickBottomRef.current) el.scrollTop = el.scrollHeight;
                    }}
                    disabled={v3ChatSending || v3ChatSession?.status !== "accepted"}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void onSendV3Chat();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="primary"
                    disabled={v3ChatSending || !v3ChatDraft.trim() || v3ChatSession?.status !== "accepted"}
                    onClick={() => void onSendV3Chat()}
                    title="Send to user"
                  >
                    {v3ChatSending ? "Sending…" : "Send"}
                  </button>
                  </div>
                </div>
              </div>
            </div>,
            document.body,
          ) : null}
          <V3KundliModal
            open={v3KundliOpen}
            loading={v3KundliLoading}
            error={v3KundliError}
            data={v3KundliData}
            sharing={v3KundliSharing}
            onClose={() => setV3KundliOpen(false)}
            onReload={() => void loadV3Kundli()}
            onShareImage={(dataUrl) => void shareV3KundliImageToChat(dataUrl)}
          />
        </section>
      ) : null}

      {tab === "support" ? (
        <section className="section">
          <h2>
            Help & Support ({supportThreads.length}){" "}
            <span className="detail-muted" style={{ fontSize: 11 }}>v2</span>
          </h2>
          <p className="detail-muted">
            AI pehle is account ke hisaab se jawab deti hai (internal data nahi).
            Samajh na aaye to wait — tabhi Telegram / admin.
            30 min silence = ticket auto-delete.
            {supportWaitingCount > 0 ? ` · ${supportWaitingCount} waiting.` : ""}
          </p>
          {supportError ? <div className="error">{supportError}</div> : null}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(240px, 320px) 1fr",
              gap: 12,
              minHeight: 480,
            }}
          >
            <div className="card" style={{ padding: 0, overflow: "auto", maxHeight: "70vh" }}>
              {supportThreads.length === 0 ? (
                <div className="detail-muted" style={{ padding: 16 }}>
                  No tickets need you. AI is handling how-to chats in the app.
                </div>
              ) : (
                supportThreads.map((row) => {
                  const active = supportThreadId === row.thread_id;
                  const unread = Number(row.unread_admin || 0);
                  const needsYou = Boolean(row.escalated) || unread > 0;
                  return (
                    <button
                      key={row.thread_id}
                      type="button"
                      onClick={() => {
                        setSupportThreadId(row.thread_id);
                        setSupportThread(row);
                        setSupportMessages([]);
                        setSupportDraft("");
                      }}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        padding: "12px 14px",
                        border: "none",
                        borderBottom: "1px solid var(--border, #2a2f3a)",
                        borderRadius: 0,
                        background: active ? "rgba(59,130,246,0.18)" : "transparent",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                        <strong style={{ fontSize: 13 }}>
                          {row.user_name || row.user_email || `User #${row.user_id ?? "?"}`}
                        </strong>
                        {needsYou ? (
                          <span className="badge warn">
                            {unread > 0 ? unread : "Needs you"}
                          </span>
                        ) : row.status === "closed" ? (
                          <span className="badge">closed</span>
                        ) : row.ai_handled ? (
                          <span className="badge">AI</span>
                        ) : null}
                      </div>
                      <div className="detail-muted" style={{ fontSize: 11, marginTop: 2 }}>
                        {row.cosmo_user_id || (row.user_id != null ? `#${row.user_id}` : "") || "no profile info"}
                      </div>
                      <div className="detail-muted" style={{ fontSize: 12, marginTop: 4 }}>
                        {(row.last_message_preview || "—").slice(0, 80)}
                      </div>
                    </button>
                  );
                })
              )}
            </div>

            <div
              className="card"
              style={{
                display: "flex",
                flexDirection: "column",
                minHeight: 480,
                maxHeight: "70vh",
                padding: 0,
                overflow: "hidden",
              }}
            >
              {!supportThreadId ? (
                <div className="detail-muted" style={{ padding: 24 }}>
                  Select a conversation to reply.
                </div>
              ) : (
                <>
                  <div
                    style={{
                      padding: "12px 16px",
                      borderBottom: "1px solid var(--border, #2a2f3a)",
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 8,
                      flexWrap: "wrap",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <strong>
                        {supportThread?.user_name ||
                          supportThread?.user_email ||
                          `User #${supportThread?.user_id ?? "?"}`}
                      </strong>
                      <div className="detail-muted" style={{ fontSize: 12 }}>
                        {[
                          supportThread?.user_id != null
                            ? `ID ${supportThread.user_id}`
                            : "",
                          supportThread?.cosmo_user_id || "",
                          supportThread?.user_email || "",
                          supportThread?.status || "open",
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        type="button"
                        onClick={() => {
                          if (
                            !window.confirm(
                              "Close this ticket? Chat, photos, and all support data will be permanently deleted. The user will start a new empty chat.",
                            )
                          )
                            return;
                          void closeSupportThread(supportThreadId).then(() => {
                            setSupportThreadId(null);
                            setSupportThread(null);
                            setSupportMessages([]);
                            void loadSupportThreads();
                          });
                        }}
                        style={{ background: "#dc2626", borderColor: "#dc2626", color: "#fff" }}
                      >
                        Close & delete
                      </button>
                    </div>
                  </div>
                  <div
                    ref={supportListRef}
                    style={{
                      flex: 1,
                      minHeight: 0,
                      overflowY: "auto",
                      padding: 16,
                      display: "flex",
                      flexDirection: "column",
                      gap: 10,
                      background: "rgba(0,0,0,0.15)",
                    }}
                  >
                    {supportMessages.length === 0 ? (
                      <div className="detail-muted">No messages yet.</div>
                    ) : (
                      supportMessages.map((m) => {
                        const mine = m.sender === "admin";
                        const sys = m.sender === "system";
                        const bot = m.sender === "bot";
                        const who = mine ? "You (support)" : bot ? "AI" : "User";
                        const src = m.image_url
                          ? m.image_url.startsWith("http") || m.image_url.startsWith("data:")
                            ? m.image_url
                            : `${getApiBase()}${m.image_url.startsWith("/") ? "" : "/"}${m.image_url}`
                          : "";
                        return (
                          <div
                            key={m.id}
                            style={{
                              alignSelf: sys ? "center" : mine ? "flex-end" : "flex-start",
                              maxWidth: sys ? "90%" : "78%",
                              padding: sys ? "6px 10px" : "8px 12px",
                              borderRadius: 12,
                              background: sys
                                ? "transparent"
                                : mine
                                  ? "rgba(59,130,246,0.25)"
                                  : bot
                                    ? "rgba(14,165,233,0.18)"
                                    : "rgba(255,255,255,0.08)",
                              border: sys ? "none" : "1px solid rgba(255,255,255,0.08)",
                              fontSize: sys ? 12 : 14,
                              opacity: sys ? 0.75 : 1,
                              textAlign: sys ? "center" : "left",
                            }}
                          >
                            {!sys ? (
                              <div className="detail-muted" style={{ fontSize: 11, marginBottom: 4 }}>
                                {who}
                              </div>
                            ) : null}
                            {m.text ? (
                              <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
                            ) : null}
                            {src ? (
                              <a href={src} target="_blank" rel="noreferrer">
                                <img
                                  src={src}
                                  alt="support"
                                  style={{
                                    maxWidth: 220,
                                    maxHeight: 220,
                                    borderRadius: 8,
                                    marginTop: m.text ? 8 : 0,
                                    display: "block",
                                  }}
                                />
                              </a>
                            ) : null}
                          </div>
                        );
                      })
                    )}
                  </div>
                  <div
                    style={{
                      padding: 12,
                      borderTop: "1px solid var(--border, #2a2f3a)",
                      display: "flex",
                      gap: 8,
                      alignItems: "flex-end",
                    }}
                  >
                    <label style={{ cursor: "pointer" }} title="Send image">
                      <input
                        type="file"
                        accept="image/*"
                        style={{ display: "none" }}
                        disabled={
                          supportSending || supportThread?.status === "closed"
                        }
                        onChange={(e) => {
                          const f = e.target.files?.[0] || null;
                          e.target.value = "";
                          if (!f || !supportThreadId) return;
                          if (!f.type.startsWith("image/")) {
                            alert("Please pick an image file.");
                            return;
                          }
                          setSupportSending(true);
                          const reader = new FileReader();
                          reader.onload = () => {
                            void sendSupportMessage(supportThreadId, {
                              data_url: String(reader.result || ""),
                              text: "",
                            })
                              .then(() => refreshSupportChat(supportThreadId))
                              .then(() => loadSupportThreads())
                              .catch((err) =>
                                alert(err instanceof Error ? err.message : "Image failed"),
                              )
                              .finally(() => setSupportSending(false));
                          };
                          reader.onerror = () => {
                            setSupportSending(false);
                            alert("Could not read image");
                          };
                          reader.readAsDataURL(f);
                        }}
                      />
                      <span
                        className="button-like"
                        style={{ padding: "8px 10px", display: "inline-block" }}
                      >
                        🖼
                      </span>
                    </label>
                    <textarea
                      value={supportDraft}
                      onChange={(e) => setSupportDraft(e.target.value)}
                      placeholder="Reply to user…"
                      rows={2}
                      style={{ flex: 1, resize: "none", fontSize: 16 }}
                      disabled={supportSending || supportThread?.status === "closed"}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          const text = supportDraft.trim();
                          if (!text || !supportThreadId || supportSending) return;
                          setSupportSending(true);
                          void sendSupportMessage(supportThreadId, { text })
                            .then(() => {
                              setSupportDraft("");
                              return refreshSupportChat(supportThreadId);
                            })
                            .then(() => loadSupportThreads())
                            .catch((err) =>
                              alert(err instanceof Error ? err.message : "Send failed"),
                            )
                            .finally(() => setSupportSending(false));
                        }
                      }}
                    />
                    <button
                      type="button"
                      className="primary"
                      disabled={
                        supportSending ||
                        !supportDraft.trim() ||
                        supportThread?.status === "closed"
                      }
                      onClick={() => {
                        const text = supportDraft.trim();
                        if (!text || !supportThreadId) return;
                        setSupportSending(true);
                        void sendSupportMessage(supportThreadId, { text })
                          .then(() => {
                            setSupportDraft("");
                            return refreshSupportChat(supportThreadId);
                          })
                          .then(() => loadSupportThreads())
                          .catch((err) =>
                            alert(err instanceof Error ? err.message : "Send failed"),
                          )
                          .finally(() => setSupportSending(false));
                      }}
                    >
                      {supportSending ? "Sending…" : "Send"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {tab === "askqa" ? (
        askQaDetailLoading ? (
          <section className="section card">
            <p className="detail-muted">Loading question detail…</p>
          </section>
        ) : askQaViewRow ? (
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
                  <th>Question</th>
                </tr>
              </thead>
              <tbody>
                {askQuestions.length === 0 ? (
                  <tr>
                    <td colSpan={1}>No Ask questions logged yet.</td>
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
                              onClick={() => {
                                setAskQaError(null);
                                setAskQaDetailLoading(true);
                                fetchAskQuestionDetail(row.id)
                                  .then((detail) => setAskQaViewRow(detail))
                                  .catch((e) =>
                                    setAskQaError(
                                      e instanceof Error ? e.message : "Failed to load detail",
                                    ),
                                  )
                                  .finally(() => setAskQaDetailLoading(false));
                              }}
                            />
                          </div>
                        </div>
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

      {tab === "instagram" ? <InstagramAnswersPage /> : null}

      {tab === "users" ? (
        <section className="section">
          <div className="section-head users-section-head">
            {directLookupOpen || detailUserId !== null ? (
              <button type="button" className="users-back-btn" onClick={closeUserDetailView}>
                ← Back
              </button>
            ) : null}
            <h2>Users ({total})</h2>
          </div>
          <div className="card user-id-lookup">
            <h3>Complete user inspector</h3>
            <p className="detail-muted">
              Search exact database ID (for example 123) or public ID (for example COSMO123).
            </p>
            <div className="toolbar">
              <input
                type="search"
                inputMode="text"
                placeholder="Enter user ID or COSMO ID…"
                value={userIdInput}
                onChange={(e) => setUserIdInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void onLookupUser();
                }}
              />
              <button
                type="button"
                className="primary"
                disabled={detailLoading}
                onClick={() => void onLookupUser()}
              >
                {detailLoading && directLookupOpen ? "Searching…" : "Open full account"}
              </button>
              {directLookupOpen ? (
                <button type="button" onClick={closeUserDetailView}>
                  Close
                </button>
              ) : null}
            </div>
            {directLookupOpen ? renderUserDetailPanel() : null}
          </div>
          <h3 className="detail-summary">Browse all users</h3>
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
                          title="Permanently delete account — app auto-logout"
                        >
                          {deletingId === u.id ? "…" : "Delete"}
                        </button>
                      </td>
                    </tr>
                    {!directLookupOpen && detailUserId === u.id ? (
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
      {palmistryWorkspaceId ? (
        <PalmistryAnalysisWorkspace
          orderId={palmistryWorkspaceId}
          onClose={() => setPalmistryWorkspaceId(null)}
        />
      ) : null}
    </div>
  );
}
