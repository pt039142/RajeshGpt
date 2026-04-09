import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

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
    .replace(/â‚¹/g, "Rs. ")
    .replace(/â‰¤/g, "<=")
    .replace(/â‰¥/g, ">=")
    .trim();
}

async function safeJson(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return { raw: text };
  }
}

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [query, setQuery] = useState("");
  const [validateBeforeSend, setValidateBeforeSend] = useState(true);
  const [showCitations, setShowCitations] = useState(true);
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

  async function bootstrap() {
    await checkHealth();
    await loadDocuments();
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
    } catch (error) {
      setBackendOnline(false);
      setHealth(null);
      setNotice({
        type: "warning",
        title: "Backend offline",
        body: "The React UI loaded, but the API is not reachable right now.",
      });
    }
  }

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (!response.ok) {
        throw new Error("Could not load documents.");
      }
      const data = await response.json();
      const mapped = (data.data || []).map((doc, index) => ({
        id: doc.doc_id || String(doc.id || index + 1),
        backendId: doc.doc_id || String(doc.id || index + 1),
        name: doc.name,
        chunkCount: doc.chunk_count,
        uploaded: true,
      }));
      setDocuments(mapped);
    } catch {
      setDocuments([]);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) {
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

      const uploadedDoc = {
        id: data.data?.doc_id || String(data.data?.id ?? Date.now()),
        backendId: data.data?.doc_id || String(data.data?.id ?? Date.now()),
        name: data.data?.filename || file.name,
        chunkCount: data.data?.pages || 0,
        uploaded: true,
      };

      setDocuments((current) => {
        const next = [uploadedDoc, ...current.filter((item) => item.name !== uploadedDoc.name)];
        return next;
      });
      setSelectedDocs((current) => Array.from(new Set([uploadedDoc.id, ...current])));
      setNotice({
        type: "success",
        title: "Document uploaded",
        body: `${uploadedDoc.name} is ready for document-backed responses.`,
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
      const response = await fetch(`${API_BASE}/documents/${encodeURIComponent(document.backendId)}`, {
        method: "DELETE",
      });
      const data = await safeJson(response);

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.message || "Delete failed.");
      }

      setDocuments((current) => current.filter((item) => item.backendId !== document.backendId));
      setSelectedDocs((current) => current.filter((item) => item !== document.id));
      setNotice({
        type: "success",
        title: "Document removed",
        body: `${document.name} was removed from the uploaded document list.`,
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
          document_ids: selectedDocs,
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
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
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
                  key={`${doc.backendId}-${doc.id}`}
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
              <p className="tiny-copy">No PDFs uploaded yet.</p>
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
                    You can ask general finance and accounting questions even without uploading
                    a PDF, and use uploaded documents when you want grounded answers.
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
