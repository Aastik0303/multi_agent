import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

// ─── Icons (inline SVG so no extra deps) ─────────────────────────────────────
const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const UploadIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
  </svg>
);
const BotIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    <line x1="12" y1="15" x2="12" y2="19"/>
    <line x1="8" y1="17" x2="16" y2="17"/>
  </svg>
);
const UserIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

// ─── Agent badge colors ───────────────────────────────────────────────────────
const AGENT_COLORS = {
  "Document RAG":          { bg: "#dbeafe", text: "#1d4ed8", dot: "#3b82f6" },
  "YouTube RAG":           { bg: "#fce7f3", text: "#9d174d", dot: "#ec4899" },
  "Data Analyst":          { bg: "#d1fae5", text: "#065f46", dot: "#10b981" },
  "Code Writer":           { bg: "#ede9fe", text: "#4c1d95", dot: "#8b5cf6" },
  "Code Debugger":         { bg: "#fff7ed", text: "#9a3412", dot: "#f97316" },
  "Deep Researcher":       { bg: "#fef3c7", text: "#92400e", dot: "#f59e0b" },
  "General Chat":          { bg: "#f3f4f6", text: "#374151", dot: "#6b7280" },
  "General Chat (fallback)":{ bg: "#f3f4f6", text: "#374151", dot: "#6b7280" },
};

// ─── Simple markdown renderer (bold, code, headers) ──────────────────────────
function renderMarkdown(text) {
  const lines = text.split("\n");
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre key={i} style={{
          background: "#1e1e2e", color: "#cdd6f4", padding: "16px",
          borderRadius: "8px", overflowX: "auto", fontSize: "13px",
          lineHeight: "1.6", margin: "8px 0", fontFamily: "'Fira Code', monospace"
        }}>
          {lang && <div style={{ color: "#89b4fa", fontSize: "11px", marginBottom: "8px", textTransform: "uppercase" }}>{lang}</div>}
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
    }
    // H2
    else if (line.startsWith("## ")) {
      elements.push(<h3 key={i} style={{ margin: "16px 0 6px", fontSize: "16px", fontWeight: 700, color: "#1e293b", fontFamily: "'Playfair Display', serif" }}>{line.slice(3)}</h3>);
    }
    // H3
    else if (line.startsWith("### ")) {
      elements.push(<h4 key={i} style={{ margin: "12px 0 4px", fontSize: "14px", fontWeight: 600, color: "#334155" }}>{line.slice(4)}</h4>);
    }
    // Bullet
    else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <div key={i} style={{ display: "flex", gap: "8px", margin: "3px 0" }}>
          <span style={{ color: "#64748b", flexShrink: 0 }}>•</span>
          <span>{inlineFormat(line.slice(2))}</span>
        </div>
      );
    }
    // Numbered list
    else if (/^\d+\. /.test(line)) {
      const num = line.match(/^\d+/)[0];
      elements.push(
        <div key={i} style={{ display: "flex", gap: "8px", margin: "3px 0" }}>
          <span style={{ color: "#64748b", flexShrink: 0, minWidth: "20px" }}>{num}.</span>
          <span>{inlineFormat(line.replace(/^\d+\. /, ""))}</span>
        </div>
      );
    }
    // Empty line
    else if (line.trim() === "") {
      elements.push(<div key={i} style={{ height: "8px" }} />);
    }
    // Regular paragraph
    else {
      elements.push(<p key={i} style={{ margin: "2px 0", lineHeight: "1.7" }}>{inlineFormat(line)}</p>);
    }
    i++;
  }
  return elements;
}

function inlineFormat(text) {
  // Bold: **text**
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i} style={{ background: "#f1f5f9", padding: "1px 5px", borderRadius: "4px", fontSize: "13px", fontFamily: "monospace", color: "#7c3aed" }}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hello! I'm your **Agentic AI** assistant — powered by LangChain ReAct agents.\n\n- 📄 **Document RAG** — Upload PDF/TXT, ask questions\n- 🎬 **YouTube RAG** — Paste a URL, ask about the video\n- 📊 **Data Analyst Agent** — Upload CSV → auto charts + insights\n- 💻 **Code Writer Agent** — Write, run & verify code automatically\n- 🐛 **Code Debugger Agent** — Debug, explain & fix code\n- 🔬 **Deep Researcher Agent** — Decompose → research → synthesize\n- 💬 **General Chat** — Friendly conversation\n\nEach agent uses a **ReAct loop**: Thought → Action → Observation → Answer",
      agent_used: "General Chat"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [showUploadPanel, setShowUploadPanel] = useState(false);

  const messagesEndRef = useRef(null);
  const docInputRef = useRef(null);
  const csvInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ─── Send chat message ────────────────────────────────────────────────────
  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Server error");
      }

      const data = await res.json();
      if (!sessionId) setSessionId(data.session_id);

      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.answer,
        agent_used: data.agent_used,
        chart: data.chart || null        // base64 PNG from Data Analyst
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `❌ Error: ${err.message}`,
        agent_used: "Error"
      }]);
    } finally {
      setLoading(false);
    }
  }

  // ─── Upload document ──────────────────────────────────────────────────────
  async function uploadDocument(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadStatus({ type: "loading", text: `Uploading ${file.name}...` });

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload/document`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setUploadStatus({ type: "success", text: data.message });
      setMessages(prev => [...prev, { role: "assistant", content: data.message, agent_used: "Document RAG" }]);
    } catch (err) {
      setUploadStatus({ type: "error", text: `Upload failed: ${err.message}` });
    }
  }

  // ─── Upload CSV ───────────────────────────────────────────────────────────
  async function uploadCsv(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadStatus({ type: "loading", text: `Uploading ${file.name}...` });

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload/csv`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setUploadStatus({ type: "success", text: data.message });
      setMessages(prev => [...prev, { role: "assistant", content: data.message, agent_used: "Data Analyst" }]);
    } catch (err) {
      setUploadStatus({ type: "error", text: `Upload failed: ${err.message}` });
    }
  }

  // ─── Submit YouTube URL ───────────────────────────────────────────────────
  async function submitYoutube(e) {
    e.preventDefault();
    if (!youtubeUrl.trim()) return;
    setUploadStatus({ type: "loading", text: "Processing YouTube video..." });

    const form = new FormData();
    form.append("url", youtubeUrl.trim());

    try {
      const res = await fetch(`${API_BASE}/upload/youtube`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setUploadStatus({ type: "success", text: data.message });
      setMessages(prev => [...prev, { role: "assistant", content: data.message, agent_used: "YouTube RAG" }]);
      setYoutubeUrl("");
    } catch (err) {
      setUploadStatus({ type: "error", text: `Failed: ${err.message}` });
    }
  }

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #f8fafc 0%, #f0f4ff 50%, #fdf4ff 100%)",
      fontFamily: "'DM Sans', -apple-system, sans-serif",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "0",
    }}>
      {/* Google Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Playfair+Display:wght@700&family=Fira+Code&display=swap" rel="stylesheet" />

      {/* Header */}
      <header style={{
        width: "100%",
        background: "rgba(255,255,255,0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "36px", height: "36px", borderRadius: "10px",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", boxShadow: "0 4px 12px rgba(99,102,241,0.3)"
          }}>
            <BotIcon />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "#1e293b", fontFamily: "'Playfair Display', serif" }}>
              Multi-Agent AI
            </h1>
            <p style={{ margin: 0, fontSize: "12px", color: "#64748b" }}>7 specialized agents</p>
          </div>
        </div>
        <button
          onClick={() => setShowUploadPanel(!showUploadPanel)}
          style={{
            padding: "8px 16px", borderRadius: "8px", border: "1px solid #e2e8f0",
            background: showUploadPanel ? "#6366f1" : "white",
            color: showUploadPanel ? "white" : "#374151",
            cursor: "pointer", fontSize: "13px", fontWeight: 500,
            display: "flex", alignItems: "center", gap: "6px",
            transition: "all 0.2s"
          }}
        >
          <UploadIcon /> Upload Files
        </button>
      </header>

      {/* Upload Panel */}
      {showUploadPanel && (
        <div style={{
          width: "100%", maxWidth: "800px",
          background: "white",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          margin: "16px 24px 0",
          padding: "20px",
          boxSizing: "border-box",
          boxShadow: "0 4px 20px rgba(0,0,0,0.06)",
          animation: "slideDown 0.2s ease"
        }}>
          <h3 style={{ margin: "0 0 16px", fontSize: "14px", fontWeight: 600, color: "#374151" }}>
            📂 Upload Your Data
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
            {/* Document upload */}
            <div style={{ border: "2px dashed #e2e8f0", borderRadius: "10px", padding: "16px", textAlign: "center", cursor: "pointer" }}
              onClick={() => docInputRef.current?.click()}>
              <div style={{ fontSize: "24px", marginBottom: "8px" }}>📄</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#374151" }}>PDF or TXT</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Click to upload</div>
              <input ref={docInputRef} type="file" accept=".pdf,.txt" style={{ display: "none" }} onChange={uploadDocument} />
            </div>
            {/* CSV upload */}
            <div style={{ border: "2px dashed #e2e8f0", borderRadius: "10px", padding: "16px", textAlign: "center", cursor: "pointer" }}
              onClick={() => csvInputRef.current?.click()}>
              <div style={{ fontSize: "24px", marginBottom: "8px" }}>📊</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#374151" }}>CSV Dataset</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Click to upload</div>
              <input ref={csvInputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={uploadCsv} />
            </div>
            {/* YouTube */}
            <form onSubmit={submitYoutube} style={{ border: "2px dashed #e2e8f0", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "24px", marginBottom: "8px", textAlign: "center" }}>🎬</div>
              <input
                value={youtubeUrl}
                onChange={e => setYoutubeUrl(e.target.value)}
                placeholder="YouTube URL..."
                style={{
                  width: "100%", padding: "6px 10px", borderRadius: "6px",
                  border: "1px solid #e2e8f0", fontSize: "12px",
                  boxSizing: "border-box", marginBottom: "8px", outline: "none"
                }}
              />
              <button type="submit" style={{
                width: "100%", padding: "6px", borderRadius: "6px",
                background: "#6366f1", color: "white", border: "none",
                fontSize: "12px", fontWeight: 500, cursor: "pointer"
              }}>Process Video</button>
            </form>
          </div>

          {/* Upload status */}
          {uploadStatus && (
            <div style={{
              marginTop: "12px", padding: "10px 14px", borderRadius: "8px",
              background: uploadStatus.type === "success" ? "#f0fdf4" : uploadStatus.type === "error" ? "#fef2f2" : "#f0f4ff",
              border: `1px solid ${uploadStatus.type === "success" ? "#bbf7d0" : uploadStatus.type === "error" ? "#fecaca" : "#c7d2fe"}`,
              fontSize: "13px",
              color: uploadStatus.type === "success" ? "#166534" : uploadStatus.type === "error" ? "#991b1b" : "#4338ca"
            }}>
              {uploadStatus.type === "loading" ? "⏳ " : uploadStatus.type === "success" ? "✅ " : "❌ "}
              {uploadStatus.text}
            </div>
          )}
        </div>
      )}

      {/* Chat area */}
      <main style={{
        width: "100%", maxWidth: "800px",
        flex: 1, padding: "20px 24px 100px",
        boxSizing: "border-box",
        display: "flex", flexDirection: "column", gap: "16px"
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: "flex",
            flexDirection: msg.role === "user" ? "row-reverse" : "row",
            gap: "12px",
            alignItems: "flex-start",
            animation: "fadeUp 0.3s ease"
          }}>
            {/* Avatar */}
            <div style={{
              width: "34px", height: "34px", borderRadius: "10px", flexShrink: 0,
              background: msg.role === "user"
                ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
                : "linear-gradient(135deg, #f1f5f9, #e2e8f0)",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: msg.role === "user" ? "white" : "#64748b",
              boxShadow: msg.role === "user" ? "0 2px 8px rgba(99,102,241,0.3)" : "none"
            }}>
              {msg.role === "user" ? <UserIcon /> : <BotIcon />}
            </div>

            {/* Bubble */}
            <div style={{
              maxWidth: "75%",
              background: msg.role === "user"
                ? "linear-gradient(135deg, #6366f1, #7c3aed)"
                : "white",
              color: msg.role === "user" ? "white" : "#1e293b",
              padding: "12px 16px",
              borderRadius: msg.role === "user" ? "18px 4px 18px 18px" : "4px 18px 18px 18px",
              boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
              fontSize: "14px",
              lineHeight: "1.6",
            }}>
              {msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}

              {/* ── Chart from Data Analyst ──────────────────────────────── */}
              {msg.chart && (
                <div style={{ marginTop: "14px" }}>
                  <div style={{
                    fontSize: "11px", fontWeight: 600, color: "#10b981",
                    marginBottom: "8px", display: "flex", alignItems: "center", gap: "5px"
                  }}>
                    <span>📊</span> Visualization (generated with matplotlib)
                  </div>
                  <img
                    src={msg.chart}
                    alt="Data visualization"
                    style={{
                      width: "100%", maxWidth: "560px", borderRadius: "10px",
                      border: "1px solid #e2e8f0",
                      boxShadow: "0 2px 12px rgba(0,0,0,0.08)"
                    }}
                  />
                </div>
              )}

              {/* Agent badge */}
              {msg.agent_used && msg.role === "assistant" && (() => {
                const c = AGENT_COLORS[msg.agent_used] || AGENT_COLORS["General Chat"];
                return (
                  <div style={{
                    display: "inline-flex", alignItems: "center", gap: "5px",
                    marginTop: "10px", padding: "3px 9px", borderRadius: "20px",
                    background: c.bg, fontSize: "11px", fontWeight: 600, color: c.text
                  }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: c.dot, display: "inline-block" }} />
                    {msg.agent_used}
                  </div>
                );
              })()}
            </div>
          </div>
        ))}

        {/* Loading indicator — shows ReAct thinking animation */}
        {loading && (
          <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
            <div style={{
              width: "34px", height: "34px", borderRadius: "10px",
              background: "linear-gradient(135deg, #f1f5f9, #e2e8f0)",
              display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b"
            }}>
              <BotIcon />
            </div>
            <div style={{
              background: "white", padding: "14px 18px", borderRadius: "4px 18px 18px 18px",
              boxShadow: "0 2px 12px rgba(0,0,0,0.06)"
            }}>
              <div style={{ display: "flex", gap: "5px", alignItems: "center", marginBottom: "6px" }}>
                {[0, 1, 2].map(i => (
                <span key={i} style={{
                  width: "7px", height: "7px", borderRadius: "50%",
                  background: "#6366f1", display: "block",
                  animation: `pulse 1.2s ${i * 0.2}s infinite`
                }} />
              ))}
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Agent thinking… (Thought → Action → Observation)
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input bar */}
      <div style={{
        position: "fixed", bottom: 0, width: "100%",
        background: "rgba(255,255,255,0.95)",
        backdropFilter: "blur(12px)",
        borderTop: "1px solid rgba(0,0,0,0.06)",
        padding: "16px 24px",
        boxSizing: "border-box",
        display: "flex", justifyContent: "center"
      }}>
        <form onSubmit={sendMessage} style={{
          width: "100%", maxWidth: "800px",
          display: "flex", gap: "10px"
        }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask anything... (upload files first for RAG)"
            disabled={loading}
            style={{
              flex: 1, padding: "12px 18px",
              borderRadius: "12px",
              border: "1.5px solid #e2e8f0",
              fontSize: "14px",
              outline: "none",
              background: "white",
              color: "#1e293b",
              transition: "border-color 0.2s",
              fontFamily: "'DM Sans', sans-serif"
            }}
            onFocus={e => e.target.style.borderColor = "#6366f1"}
            onBlur={e => e.target.style.borderColor = "#e2e8f0"}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: "12px 20px",
              borderRadius: "12px",
              background: "linear-gradient(135deg, #6366f1, #7c3aed)",
              color: "white",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading || !input.trim() ? 0.6 : 1,
              display: "flex", alignItems: "center", gap: "6px",
              fontWeight: 600, fontSize: "14px",
              boxShadow: "0 4px 12px rgba(99,102,241,0.3)",
              transition: "all 0.2s"
            }}
          >
            <SendIcon /> Send
          </button>
        </form>
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        * { box-sizing: border-box; }
        body { margin: 0; }
        input:disabled { opacity: 0.7; }
      `}</style>
    </div>
  );
}