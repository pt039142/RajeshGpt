import { useEffect, useRef, useState } from "react";
import {
  deleteCachedDocument,
  getCachedDocumentsByIds,
  listCachedDocuments,
  saveCachedDocument,
} from "./storage";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const MESSAGE_STORAGE_KEY = "rajeshgpt.messages";
const SELECTED_DOCS_STORAGE_KEY = "rajeshgpt.selected-docs";
const VALIDATE_STORAGE_KEY = "rajeshgpt.validate-before-send";
const CITATIONS_STORAGE_KEY = "rajeshgpt.show-citations";

const samplePrompts = [
  "Summarize Section 80C deductions for a salaried taxpayer.",
  "What documents should a CA collect before ITR filing review?",
  "Explain TDS applicability on professional fees in simple terms.",
  "Explain working capital in simple finance language.",
];

function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

function formatScope(scope) {
  return (scope || "unknown").replace(/_/g, " ");
}

function normalizeText(value) {
  return String(value ?? "")
    .replace(/Ã¢â€šÂ¹/g, "Rs. ")
    .replace(/Ã¢â€°Â¤/g, "<=")
    .replace(/Ã¢â€°Â¥/g, ">=")
    .trim();
}

function readStoredJson(key, fallbackValue) {
  try {
    const rawValue = window.localStorage.getItem(key);
    return rawValue ? JSON.parse(rawValue) : fallbackValue;
  } catch {
    return fallbackValue;
  }
}

function readStoredBoolean(key, fallbackValue) {
  try {
    const rawValue = window.localStorage.getItem(key);
    return rawValue === null ? fallbackValue : rawValue === "true";
  } catch {
    return fallbackValue;
  }
}

function summarizeDocument(document) {
  return {
    id: document.id,
    backendId: document.backendId || document.id,
    name: document.name,
    chunkCount: document.chunkCount || 0,
    pages: document.pages || 0,
    uploadedAt: document.uploadedAt,
    uploaded: true,
  };
}

async function safeJson(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return { raw: text };
  }
}

export default function AppPersisted() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState(() => readStoredJson(MESSAGE_STORAGE_KEY, []));
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState(() => readStoredJson(SELECTED_DOCS_STORAGE_KEY, []));
  const [query, setQuery] = useState("");
  const [validateBeforeSend, setValidateBeforeSend] = useState(() =>
    readStoredBoolean(VALIDATE_STORAGE_KEY, true),
  );
  const [showCitations, setShowCitations] = useState(() =>
    readStoredBoolean(CITATIONS_STORAGE_KEY, true),
  );
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    window.localStorage.setItem(MESSAGE_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    window.localStorage.setItem(SELECTED_DOCS_STORAGE_KEY, JSON.stringify(selectedDocs));
  }, [selectedDocs]);

  useEffect(() => {
    window.localStorage.setItem(VALIDATE_STORAGE_KEY, String(validateBeforeSend));
  }, [validateBeforeSend]);

  useEffect(() => {
    window.localStorage.setItem(CITATIONS_STORAGE_KEY, String(showCitations));
  }, [showCitations]);

  async function bootstrap() {
    await Promise.all([checkHealth(), loadDocuments()]);
  }

  async function checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) {
        throw new Error("Backend is unavailable.");
      }
      const data = await response.json();
      setHealth(data);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
      setHealth(null);
      setNotice({
        type: "warning",
        title: "Backend offline",
        body: "Your browser-saved documents are still available, but the API is not reachable right now.",
      });
    }
  }

  async function loadDocuments() {
    try {
      const storedDocuments = await listCachedDocuments();
      const summaries = storedDocuments.map(summarizeDocument);
      setDocuments(summaries);
      setSelectedDocs((current) =>
        current.filter((id) => summaries.some((document) => document.id === id)),
      );
    } catch (error) {
      setDocuments([]);
      setNotice({
        type: "warning",
        title: "Browser storage unavailable",
        body: error.message || "Could not read cached documents from this browser.",
      });
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    if (!backendOnline) {
      setNotice({
        type: "warning",
        title: "Backend offline",
        body: "The backend must be online to process a new PDF upload.",
      });
      event.target.value = "";
      return;
    }

    setUploading(true);
    setNotice(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await safeJson(response);

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.message || "Upload failed.");
      }

      const generatedId = data.data?.doc_id || crypto.randomUUID();
      const cachedDocument = {
        id: generatedId,
        backendId: generatedId,
        name: data.data?.filename || file.name,
        pages: data.data?.pages || 0,
        chunkCount: data.data?.chunk_count || 0,
        chunks: data.data?.chunks || [],
        uploadedAt: data.data?.uploaded_at || new Date().toISOString(),
      };

      if (!cachedDocument.chunks.length) {
        throw new Error("The backend processed the PDF but did not return searchable chunks.");
      }

      await saveCachedDocument(cachedDocument);
      await loadDocuments();
      setSelectedDocs((current) => Array.from(new Set([cachedDocument.id, ...current])));
      setNotice({
        type: "success",
        title: "Document uploaded",
        body: `${cachedDocument.name} is now stored in this browser for reuse across Render restarts.`,
      });
    } catch (error) {
      setNotice({
        type: "danger",
        title: "Upload failed",
        body: error.message,
      });
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleDeleteDocument(document) {
    setNotice(null);

    try {
      await deleteCachedDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setSelectedDocs((current) => current.filter((item) => item !== document.id));

      if (backendOnline && document.backendId) {
        try {
          await fetch(`${API_BASE}/documents/${encodeURIComponent(document.backendId)}`, {
            method: "DELETE",
          });
        } catch {
          // Browser persistence is the primary source of truth on the free tier.
        }
      }

      setNotice({
        type: "success",
        title: "Document removed",
        body: `${document.name} was removed from this browser's saved document cache.`,
      });
    } catch (error) {
      setNotice({
        type: "danger",
        title: "Unable to remove document",
        body: error.message,
      });
    }
  }

  async function validateQuery(value) {
    const response = await fetch(`${API_BASE}/query/validate?query=${encodeURIComponent(value)}`);
    const data = await safeJson(response);
    if (!response.ok || !data.success) {
      throw new Error(data.detail || data.message || "Validation failed.");
    }
    return data.validation;
  }

  async function sendQuery() {
    const trimmed = query.trim();
    if (!trimmed || loading) {
      return;
    }

    if (!backendOnline) {
      setNotice({
        type: "warning",
        title: "Backend offline",
        body: "The backend must be online to answer questions.",
      });
      return;
    }

    setNotice(null);
    let validation = null;

    try {
      if (validateBeforeSend) {
        validation = await validateQuery(trimmed);
        if (!validation.is_valid) {
          setNotice({
            type: "warning",
            title: "Query needs adjustment",
            body: validation.reason || "Please make the question more tax-specific.",
          });
          return;
        }
      }

      const selectedClientDocuments = await getCachedDocumentsByIds(selectedDocs);
      const userMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };

      setMessages((current) => [...current, userMessage]);
      setQuery("");
      setLoading(true);

      const response = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: trimmed,
          client_documents: selectedClientDocuments.map((document) => ({
            doc_id: document.id,
            name: document.name,
            pages: document.pages || 0,
            chunks: document.chunks || [],
          })),
        }),
      });
      const data = await safeJson(response);

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.message || "Query failed.");
      }

      const answer = data.data || {};
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: normalizeText(answer.response),
        confidence: answer.confidence_score ?? validation?.confidence ?? 0,
        scope: answer.scope ?? validation?.scope ?? "unknown",
        hasRisk: Boolean(answer.has_hallucination_risk),
        citations: (answer.citations || []).map((cite) => ({
          label: `${cite.document_name || "Document"}${cite.section ? ` - ${cite.section}` : ""}`,
          text: normalizeText(cite.text || ""),
        })),
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      setNotice({
        type: "danger",
        title: "Unable to generate answer",
        body: error.message,
      });
    } finally {
      setLoading(false);
    }
  }

  function handleComposerKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendQuery();
    }
  }

  function toggleDocument(id) {
    setSelectedDocs((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <div className="brand-kicker">Tax Intelligence Workspace</div>
          <h1>RajeshGPT</h1>
          <p>Private tax and finance assistance for document-backed work.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => {
            setMessages([]);
            setNotice(null);
          }}
        >
          New conversation
        </button>

        <section className="sidebar-card">
          <div className="sidebar-card-label">System</div>
          <div className="status-row">
            <span className={classNames("status-dot", backendOnline && "online")} />
            <span>{backendOnline ? "Backend connected" : "Backend offline"}</span>
          </div>
          {health ? <p className="tiny-copy">API {health.version} is operational.</p> : null}
          <p className="tiny-copy">Documents stay in this browser to survive free-tier restarts.</p>
        </section>

        <section className="sidebar-card">
          <div className="sidebar-card-label">Documents</div>
          <label className="upload-button">
            <input
              type="file"
              accept="application/pdf"
              onChange={handleUpload}
              disabled={uploading}
            />
            {uploading ? "Uploading..." : "Upload PDF"}
          </label>
          <div className="document-list">
            {documents.length ? (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className={classNames("document-pill", selectedDocs.includes(doc.id) && "active")}
                >
                  <button
                    type="button"
                    className="document-main"
                    onClick={() => toggleDocument(doc.id)}
                  >
                    <span>{doc.name}</span>
                    <span className="document-meta">{doc.chunkCount || 0}</span>
                  </button>
                  <button
                    type="button"
                    className="document-remove"
                    onClick={() => void handleDeleteDocument(doc)}
                    aria-label={`Remove ${doc.name}`}
                    title={`Remove ${doc.name}`}
                  >
                    Remove
                  </button>
                </div>
              ))
            ) : (
              <p className="tiny-copy">No PDFs saved in this browser yet.</p>
            )}
          </div>
        </section>

        <section className="sidebar-card">
          <div className="sidebar-card-label">Controls</div>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={validateBeforeSend}
              onChange={(event) => setValidateBeforeSend(event.target.checked)}
            />
            <span>Validate before sending</span>
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={showCitations}
              onChange={(event) => setShowCitations(event.target.checked)}
            />
            <span>Show citations</span>
          </label>
        </section>
      </aside>

      <main className="workspace">
        <header className="hero">
          <div>
            <div className="hero-kicker">Executive-grade tax assistance</div>
            <h2>Ask, review, validate, and document tax answers in one place.</h2>
            <p>
              Built to feel modern like ChatGPT, but focused on income tax, compliance,
              and CA workflows.
            </p>
          </div>
          <div className="hero-metrics">
            <div className="hero-metric">
              <span>Messages</span>
              <strong>{messages.length}</strong>
            </div>
            <div className="hero-metric">
              <span>Selected PDFs</span>
              <strong>{selectedDocs.length}</strong>
            </div>
            <div className="hero-metric">
              <span>Mode</span>
              <strong>{backendOnline ? "Live API" : "Offline"}</strong>
            </div>
          </div>
        </header>

        {notice ? (
          <div className={classNames("notice", notice.type)}>
            <strong>{notice.title}</strong>
            <span>{notice.body}</span>
          </div>
        ) : null}

        <section className="chat-panel">
          <div className="chat-scroll" ref={scrollRef}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-copy">
                  <h3>Start with a tax or finance prompt</h3>
                  <p>
                    Uploaded PDFs stay saved in this browser even if the free Render backend
                    sleeps, so you can continue asking document-backed questions on the same device.
                  </p>
                </div>
                <div className="sample-grid">
                  {samplePrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      className="sample-card"
                      onClick={() => setQuery(prompt)}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <article
                  key={message.id}
                  className={classNames("message-card", message.role === "assistant" && "assistant")}
                >
                  <div className="message-role">
                    {message.role === "assistant" ? "RajeshGPT" : "You"}
                  </div>
                  <div className="message-content">{message.content}</div>

                  {message.role === "assistant" ? (
                    <>
                      <div className="message-metrics">
                        <div>
                          <span>Confidence</span>
                          <strong>{Math.round((message.confidence || 0) * 100)}%</strong>
                        </div>
                        <div>
                          <span>Scope</span>
                          <strong>{formatScope(message.scope)}</strong>
                        </div>
                        <div>
                          <span>Reliability</span>
                          <strong>{message.hasRisk ? "Needs review" : "Ready to use"}</strong>
                        </div>
                      </div>

                      {showCitations && message.citations?.length ? (
                        <div className="citation-list">
                          {message.citations.map((citation, index) => (
                            <div className="citation-card" key={`${citation.label}-${index}`}>
                              <div className="citation-label">{citation.label}</div>
                              <div className="citation-text">{citation.text}</div>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </>
                  ) : null}
                </article>
              ))
            )}

            {loading ? (
              <div className="message-card assistant loading-card">
                <div className="message-role">RajeshGPT</div>
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            ) : null}
          </div>

          <div className="composer-shell">
            <div className="composer-toolbar">
              <span>{selectedDocs.length} document{selectedDocs.length === 1 ? "" : "s"} selected</span>
              <span>{validateBeforeSend ? "Validation on" : "Validation off"}</span>
            </div>
            <div className="composer">
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder="Ask about deductions, ITR review, TDS, GST, company tax, notices, accounting, finance, or CA workflow support..."
                rows={1}
              />
              <button className="primary-button send-button" type="button" onClick={() => void sendQuery()}>
                Send
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
