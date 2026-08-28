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

type ViewMode = "list" | "add" | "view" | "edit";

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
      setError(e instanceof Error ? e.message : "Failed to load answers");
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
      setError(e instanceof Error ? e.message : "Failed to load answer");
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
      setError(e instanceof Error ? e.message : "Failed to load answer");
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
        throw new Error("Exact question is required.");
      }
      if (!formAnswer.trim()) {
        throw new Error("Answer is required.");
      }

      if (mode === "add") {
        const row = await createInstagramAnswer({
          video_number,
          question: formQuestion,
          answer: formAnswer,
          status: formStatus,
        });
        setMsg(`Created answer #${row.id} for video ${row.video_number}.`);
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
        setMsg(`Updated answer #${row.id}.`);
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
    if (!confirm("Delete this Instagram answer permanently?")) return;
    setError(null);
    setMsg(null);
    try {
      await deleteInstagramAnswer(id);
      setMsg(`Deleted answer #${id}.`);
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
      setMsg(`Answer #${row.id} is now ${updated.status}.`);
      if (detail?.id === row.id) {
        setDetail(updated);
      }
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Status update failed");
    }
  };

  if (mode === "add" || mode === "edit") {
    return (
      <section className="section card">
        <h2>{mode === "add" ? "Add Instagram Answer" : `Edit Answer #${selectedId}`}</h2>
        <p className="detail-muted">
          Unique key: video number + exact question (case-insensitive match for users).
        </p>
        {error ? <div className="error">{error}</div> : null}
        <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
          <label style={{ display: "grid", gap: 6 }}>
            Video Number
            <input
              type="number"
              min={1}
              step={1}
              value={formVideo}
              onChange={(e) => setFormVideo(e.target.value)}
              placeholder="121"
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
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
          <label style={{ display: "grid", gap: 6 }}>
            Exact Question
            <input
              type="text"
              value={formQuestion}
              onChange={(e) => setFormQuestion(e.target.value)}
              placeholder="Sun in 11th house"
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            Answer
            <textarea
              rows={12}
              value={formAnswer}
              onChange={(e) => setFormAnswer(e.target.value)}
              placeholder="Full answer text users will receive…"
            />
          </label>
        </div>
        <div className="toolbar" style={{ marginTop: 16 }}>
          <button type="button" onClick={backToList} disabled={formSaving}>
            Cancel
          </button>
          <button type="button" className="primary" onClick={onSubmitForm} disabled={formSaving}>
            {formSaving ? "Saving…" : mode === "add" ? "Create Answer" : "Save Changes"}
          </button>
        </div>
      </section>
    );
  }

  if (mode === "view") {
    return (
      <section className="section card">
        <h2>Instagram Answer #{selectedId}</h2>
        {detailLoading ? (
          <p className="detail-muted">Loading…</p>
        ) : detail ? (
          <>
            {error ? <div className="error">{error}</div> : null}
            {msg ? <div className="success">{msg}</div> : null}
            <div className="user-detail-panel" style={{ marginTop: 12 }}>
              <p><strong>Video No.</strong> {detail.video_number}</p>
              <p><strong>Status</strong>{" "}
                <span className={detail.status === "active" ? "badge ok" : "badge warn"}>
                  {detail.status}
                </span>
              </p>
              <p><strong>Question</strong> {detail.question}</p>
              <p><strong>Created</strong> {formatDate(detail.created_at)}</p>
              <p><strong>Updated</strong> {formatDate(detail.updated_at)}</p>
              <div style={{ marginTop: 12 }}>
                <strong>Answer</strong>
                <pre className="ask-answer-pre" style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>
                  {detail.answer}
                </pre>
              </div>
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
          <p className="detail-muted">Answer not found.</p>
        )}
      </section>
    );
  }

  return (
    <section className="section card">
      <h2>Instagram Answers ({total})</h2>
      <p className="detail-muted">
        Database-driven reel answers. Match key: video number + exact question (trimmed, case-insensitive).
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
          placeholder="Search question…"
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
          Add New Answer
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Video No.</th>
              <th>Question</th>
              <th>Answer Preview</th>
              <th>Status</th>
              <th>Created</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7}>{loading ? "Loading…" : "No Instagram answers yet."}</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>{row.video_number}</td>
                  <td>{row.question}</td>
                  <td className="detail-muted">{row.answer_preview || "—"}</td>
                  <td>
                    <span className={row.status === "active" ? "badge ok" : "badge warn"}>
                      {row.status}
                    </span>
                  </td>
                  <td>{formatDate(row.created_at)}</td>
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
