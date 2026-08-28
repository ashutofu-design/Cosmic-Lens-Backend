import { useCallback, useEffect, useState } from "react";
import {
  createInstagramAnswer,
  deleteInstagramAnswer,
  fetchInstagramAnswer,
  fetchInstagramAnswers,
  formatDate,
  patchInstagramAnswerStatus,
  updateInstagramAnswer,
  type InstagramAnswerItem,
} from "./api";
import "./instagramAutomation.css";
import { IgAutomationPreview } from "./instagramAutomationPreview";

type ViewMode = "list" | "add" | "view" | "edit";

const TRIGGER_TYPE = "user_dm_exact" as const;

function triggerLabel() {
  return "User sends you a DM — exact word match";
}

export function InstagramAnswersPage() {
  const [mode, setMode] = useState<ViewMode>("list");
  const [items, setItems] = useState<InstagramAnswerItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [videoFilter, setVideoFilter] = useState("");
  const [questionFilter, setQuestionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "active" | "inactive">("");

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<InstagramAnswerItem | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [formVideo, setFormVideo] = useState("");
  const [formQuestion, setFormQuestion] = useState("");
  const [formAnswer, setFormAnswer] = useState("");
  const [formStatus, setFormStatus] = useState<"active" | "inactive">("active");
  const [formSaving, setFormSaving] = useState(false);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInstagramAnswers({
        page,
        video_number: videoFilter.trim() || undefined,
        question: questionFilter.trim() || undefined,
        status: statusFilter || undefined,
      });
      setItems(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load automations");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [page, videoFilter, questionFilter, statusFilter]);

  useEffect(() => {
    if (mode === "list") {
      loadList().catch(() => undefined);
    }
  }, [mode, loadList]);

  const openAdd = () => {
    setError(null);
    setMsg(null);
    setFormVideo("");
    setFormQuestion("");
    setFormAnswer("");
    setFormStatus("active");
    setSelectedId(null);
    setDetail(null);
    setMode("add");
  };

  const openView = async (id: number) => {
    setError(null);
    setMsg(null);
    setSelectedId(id);
    setDetailLoading(true);
    setMode("view");
    try {
      setDetail(await fetchInstagramAnswer(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load automation");
      setMode("list");
    } finally {
      setDetailLoading(false);
    }
  };

  const openEdit = async (id: number) => {
    setError(null);
    setMsg(null);
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const row = await fetchInstagramAnswer(id);
      setDetail(row);
      setFormVideo(String(row.video_number));
      setFormQuestion(row.question);
      setFormAnswer(row.answer || "");
      setFormStatus(row.status === "inactive" ? "inactive" : "active");
      setMode("edit");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load automation");
      setMode("list");
    } finally {
      setDetailLoading(false);
    }
  };

  const backToList = () => {
    setMode("list");
    setSelectedId(null);
    setDetail(null);
    setError(null);
  };

  const onSubmitForm = async () => {
    setFormSaving(true);
    setError(null);
    setMsg(null);
    try {
      const video_number = parseInt(formVideo.trim(), 10);
      if (!Number.isFinite(video_number) || video_number <= 0) {
        throw new Error("Video number must be a positive integer.");
      }
      if (!formQuestion.trim()) {
        throw new Error("Exact trigger words are required.");
      }
      if (!formAnswer.trim()) {
        throw new Error("Auto-reply message is required.");
      }

      if (mode === "add") {
        const row = await createInstagramAnswer({
          video_number,
          question: formQuestion,
          answer: formAnswer,
          status: formStatus,
        });
        setMsg(`Automation saved — video #${row.video_number}, trigger “${row.question}”.`);
        setMode("list");
        setPage(1);
        await loadList();
      } else if (mode === "edit" && selectedId) {
        const row = await updateInstagramAnswer(selectedId, {
          video_number,
          question: formQuestion,
          answer: formAnswer,
          status: formStatus,
        });
        setMsg(`Updated automation #${row.id}.`);
        setDetail(row);
        setMode("view");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setFormSaving(false);
    }
  };

  const onDelete = async (id: number) => {
    if (!confirm("Delete this Instagram automation permanently?")) return;
    setError(null);
    setMsg(null);
    try {
      await deleteInstagramAnswer(id);
      setMsg(`Deleted automation #${id}.`);
      if (selectedId === id) {
        backToList();
      }
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const onToggleStatus = async (row: InstagramAnswerItem) => {
    setError(null);
    setMsg(null);
    const next = row.status === "active" ? "inactive" : "active";
    try {
      const updated = await patchInstagramAnswerStatus(row.id, next);
      setMsg(`Automation #${row.id} is now ${updated.status}.`);
      if (detail?.id === row.id) {
        setDetail(updated);
      }
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Status update failed");
    }
  };

  const formPanel = (
    <div className="ig-auto-form">
      <div className="ig-auto-field">
        <label>
          Video Number
          <input
            type="number"
            min={1}
            step={1}
            value={formVideo}
            onChange={(e) => setFormVideo(e.target.value)}
            placeholder="100"
          />
          <small>Reel / video ID — part of unique key with trigger words.</small>
        </label>
      </div>

      <div className="ig-auto-field">
        <label>
          Select trigger type
          <select className="ig-auto-trigger-select" value={TRIGGER_TYPE} disabled>
            <option value={TRIGGER_TYPE}>{triggerLabel()}</option>
          </select>
          <small>User must DM the exact words below (trimmed, case-insensitive match).</small>
        </label>
      </div>

      <div className="ig-auto-field ig-auto-trigger-box">
        <label>
          When user sends exactly
          <input
            type="text"
            value={formQuestion}
            onChange={(e) => setFormQuestion(e.target.value)}
            placeholder="Sun in 11th house"
          />
          <small>No extra words, no typos — same as Instagram comment / DM text.</small>
        </label>
      </div>

      <div className="ig-auto-field ig-auto-reply-box">
        <label>
          Auto-reply message (saved text)
          <textarea
            rows={10}
            value={formAnswer}
            onChange={(e) => setFormAnswer(e.target.value)}
            placeholder="Full answer the user will see in the app — same as your Instagram auto-reply."
          />
          <small>This message is shown in the app when trigger + video number match.</small>
        </label>
      </div>

      <div className="ig-auto-field">
        <label>
          Status
          <select
            value={formStatus}
            onChange={(e) =>
              setFormStatus(e.target.value === "inactive" ? "inactive" : "active")
            }
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </label>
      </div>

      <div className="ig-auto-key-pill">
        Unique key: video #{formVideo.trim() || "—"} + exact trigger words
      </div>
    </div>
  );

  if (mode === "add" || mode === "edit") {
    return (
      <section className="section card ig-auto-page">
        <h2>{mode === "add" ? "New Instagram Automation" : `Edit Automation #${selectedId}`}</h2>
        <p className="detail-muted">
          Like Meta automation: user DM exact word → your saved reply appears in the app.
        </p>
        {error ? <div className="error">{error}</div> : null}
        <div className="ig-auto-layout">
          {formPanel}
          <IgAutomationPreview
            videoNumber={formVideo}
            triggerText={formQuestion}
            replyText={formAnswer}
          />
        </div>
        <div className="toolbar" style={{ marginTop: 16 }}>
          <button type="button" onClick={backToList} disabled={formSaving}>
            Cancel
          </button>
          <button type="button" className="primary" onClick={onSubmitForm} disabled={formSaving}>
            {formSaving ? "Saving…" : mode === "add" ? "Save automation" : "Save changes"}
          </button>
        </div>
      </section>
    );
  }

  if (mode === "view") {
    return (
      <section className="section card ig-auto-page">
        <h2>Instagram Automation #{selectedId}</h2>
        {detailLoading ? (
          <p className="detail-muted">Loading…</p>
        ) : detail ? (
          <>
            {error ? <div className="error">{error}</div> : null}
            {msg ? <div className="success">{msg}</div> : null}
            <div className="ig-auto-layout" style={{ marginTop: 12 }}>
              <div className="user-detail-panel">
                <p><strong>Video No.</strong> {detail.video_number}</p>
                <p><strong>Trigger type</strong> {triggerLabel()}</p>
                <p><strong>Status</strong>{" "}
                  <span className={detail.status === "active" ? "badge ok" : "badge warn"}>
                    {detail.status}
                  </span>
                </p>
                <p><strong>When user sends exactly</strong></p>
                <pre className="ask-answer-pre" style={{ whiteSpace: "pre-wrap", marginTop: 4 }}>
                  {detail.question}
                </pre>
                <p style={{ marginTop: 12 }}><strong>Auto-reply message</strong></p>
                <pre className="ask-answer-pre" style={{ whiteSpace: "pre-wrap", marginTop: 4 }}>
                  {detail.answer}
                </pre>
                <p className="detail-muted" style={{ marginTop: 12 }}>
                  Created {formatDate(detail.created_at)} · Updated {formatDate(detail.updated_at)}
                </p>
              </div>
              <IgAutomationPreview
                videoNumber={String(detail.video_number)}
                triggerText={detail.question}
                replyText={detail.answer || ""}
              />
            </div>
            <div className="toolbar" style={{ marginTop: 16 }}>
              <button type="button" onClick={backToList}>Back to list</button>
              <button type="button" onClick={() => openEdit(detail.id)}>Edit</button>
              <button type="button" onClick={() => onToggleStatus(detail)}>
                {detail.status === "active" ? "Deactivate" : "Activate"}
              </button>
              <button type="button" className="danger" onClick={() => onDelete(detail.id)}>
                Delete
              </button>
            </div>
          </>
        ) : (
          <p className="detail-muted">Automation not found.</p>
        )}
      </section>
    );
  }

  return (
    <section className="section card ig-auto-page">
      <h2>Instagram Automations ({total})</h2>
      <p className="detail-muted">
        DM-style rules: video number + exact user words → saved auto-reply in the app.
      </p>
      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="success">{msg}</div> : null}
      <div className="toolbar">
        <input
          type="search"
          placeholder="Video number…"
          value={videoFilter}
          onChange={(e) => {
            setVideoFilter(e.target.value);
            setPage(1);
          }}
        />
        <input
          type="search"
          placeholder="Search trigger words…"
          value={questionFilter}
          onChange={(e) => {
            setQuestionFilter(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as "" | "active" | "inactive");
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button type="button" onClick={() => loadList()} disabled={loading}>
          Refresh
        </button>
        <button type="button" className="primary" onClick={openAdd}>
          Add automation
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Video</th>
              <th>User exact words (trigger)</th>
              <th>Auto-reply preview</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6}>{loading ? "Loading…" : "No automations yet."}</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>#{row.video_number}</td>
                  <td className="ig-auto-list-trigger">{row.question}</td>
                  <td className="ig-auto-list-reply">{row.answer_preview || "—"}</td>
                  <td>
                    <span className={row.status === "active" ? "badge ok" : "badge warn"}>
                      {row.status}
                    </span>
                  </td>
                  <td>{formatDate(row.updated_at)}</td>
                  <td>
                    <div className="ask-q-actions">
                      <button type="button" onClick={() => openView(row.id)}>View</button>
                      <button type="button" onClick={() => openEdit(row.id)}>Edit</button>
                      <button type="button" onClick={() => onToggleStatus(row)}>
                        {row.status === "active" ? "Deactivate" : "Activate"}
                      </button>
                      <button type="button" className="danger" onClick={() => onDelete(row.id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {pages > 1 ? (
        <div className="pager">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>
          <span>Page {page} / {pages}</span>
          <button
            type="button"
            disabled={page >= pages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      ) : null}
    </section>
  );
}
