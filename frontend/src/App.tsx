import React, { useState, useEffect } from "react";
import axios from "axios";
import PdfViewer from "./components/PdfViewer";
import "./index.css";

type DiffMeta = {
  before?: string;
  after?: string;
  opcode?: [string, number, number, number, number];
  before_boxes?: number[][];
  after_boxes?: number[][];
  graphic_boxes?: number[][];
  page_w?: number;
  page_h?: number;
  [k: string]: any;
};

type DiffItem = {
  type: "text" | "graphic" | "layout" | string;
  page: number;
  severity: string;
  description: string;
  meta?: DiffMeta;
};

type CompareResponse = {
  pages_before: number;
  pages_after: number;
  diffs: DiffItem[];
  notes?: string;
};

type ChatMessage = { sender: "user" | "bot"; text: string };

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [beforeFile, setBeforeFile] = useState<File | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiffIndex, setActiveDiffIndex] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Session management
  useEffect(() => {
    const storedSessionId = localStorage.getItem('docdiff_session_id');
    if (storedSessionId) {
      loadSessionData(storedSessionId);
    } else {
      createNewSession();
    }
  }, []);

  const createNewSession = async () => {
    try {
      const response = await axios.post(`${API_BASE}/sessions`);
      const newSessionId = response.data.id;
      setSessionId(newSessionId);
      localStorage.setItem('docdiff_session_id', newSessionId);
    } catch (e: any) {
      console.error('Failed to create session:', e);
      setError('Failed to create session. Please refresh the page.');
    }
  };

  const loadSessionData = async (sessionId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}`);
      setSessionId(sessionId);

      // Restore comparison if exists
      if (response.data.comparison) {
        setResult(response.data.comparison.result_json);
      }

      // Restore chat history
      if (response.data.chat_messages && response.data.chat_messages.length > 0) {
        const messages = response.data.chat_messages.map((msg: any) => ({
          sender: msg.role === 'user' ? 'user' : 'bot',
          text: msg.content
        }));
        setChatMessages(messages);
      }
    } catch (e: any) {
      console.error('Failed to load session:', e);
      // Session not found or expired - create new one
      createNewSession();
    }
  };

  const clearSession = () => {
    localStorage.removeItem('docdiff_session_id');
    window.location.reload();
  };

  const clearComparison = () => {
    setResult(null);
    setActiveDiffIndex(null);
    setBeforeFile(null);
    setAfterFile(null);
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatInput("");
  };

  const onCompare = async () => {
  if (!beforeFile || !afterFile || !sessionId) return;
  setLoading(true);
  setError(null);
  setResult(null);
  setActiveDiffIndex(null);

  try {
    const form = new FormData();
    form.append("before_file", beforeFile);
    form.append("after_file", afterFile);
    form.append("session_id", sessionId);

    const { data } = await axios.post(`${API_BASE}/compare`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    setResult(data as CompareResponse);

    // 🧠 Don't auto-ask the summary — let the user start the chat manually
    console.log("✅ Comparison complete. DocDiff Assistant is ready for your questions.");
  } catch (e: any) {
    setError(
      e?.response?.data?.detail ||
        e?.message ||
        "Request failed while comparing the documents."
    );
  } finally {
    setLoading(false);
  }
};


  const askQuestion = async (question: string, diffs = result?.diffs) => {
  if (!diffs || !sessionId) return;
  setChatLoading(true);
  setChatMessages((prev) => [...prev, { sender: "user", text: question }]);

  try {
    const form = new FormData();
    form.append("question", question);
    form.append("diffs", JSON.stringify(diffs));
    form.append("session_id", sessionId);

    const response = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      body: form,
    });

    if (!response.ok || !response.body) throw new Error("Failed to stream response.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = "";

    setChatMessages((prev) => [...prev, { sender: "bot", text: "" }]);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      accumulated += chunk;

      setChatMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (updated[lastIndex].sender === "bot") {
          updated[lastIndex].text = accumulated;
        }
        return updated;
      });
    }
  } catch (e: any) {
    setChatMessages((prev) => [
      ...prev,
      { sender: "bot", text: e?.message || "Error fetching response." },
    ]);
  } finally {
    setChatLoading(false);
  }
};


  const activeDiff: DiffItem | null =
    activeDiffIndex != null && result ? result.diffs[activeDiffIndex] : null;

  const beforeBoxes = [
    ...(activeDiff?.meta?.before_boxes ?? []),
    ...(activeDiff?.meta?.graphic_boxes ?? []),
  ];
  const afterBoxes = [
    ...(activeDiff?.meta?.after_boxes ?? []),
    ...(activeDiff?.meta?.graphic_boxes ?? []),
  ];

  const pageW = activeDiff?.meta?.page_w;
  const pageH = activeDiff?.meta?.page_h;

  const colorMap = { text: "#22c55e", layout: "#3b82f6", graphic: "#f97316" } as Record<string, string>;

  return (
    <div className="app-container">
      <div className="topbar">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1>DocDiff AI</h1>
          <span style={{ opacity: 0.7 }}>Compare, Visualize & Chat</span>
        </div>
        <div className="file-inputs">
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setBeforeFile(e.target.files?.[0] ?? null)}
          />
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setAfterFile(e.target.files?.[0] ?? null)}
          />
          <button onClick={onCompare} disabled={!beforeFile || !afterFile || loading}>
            {loading ? "Analyzing…" : "Compare"}
          </button>
          <button
            onClick={clearSession}
            style={{ marginLeft: '8px', background: '#6b7280' }}
            title="Start a new session and clear history"
          >
            New Session
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="viewer-grid">
        <div className="viewer-panel">
          <h3>Before</h3>
          {beforeFile && (
            <PdfViewer file={beforeFile} highlightPage={activeDiff?.page ?? null} boxes={beforeBoxes} pageW={pageW} pageH={pageH} />
          )}
        </div>
        <div className="viewer-panel">
          <h3>After</h3>
          {afterFile && (
            <PdfViewer file={afterFile} highlightPage={activeDiff?.page ?? null} boxes={afterBoxes} pageW={pageW} pageH={pageH} />
          )}
        </div>
      </div>

      <div className="bottom-section">
        {/* Left: Diffs */}
        <div className="diff-section">
          {result && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0 }}>Detected Differences</h3>
                <button
                  onClick={clearComparison}
                  style={{ padding: '6px 12px', background: '#ef4444', fontSize: '14px' }}
                  title="Clear comparison results"
                >
                  Clear Diffs
                </button>
              </div>
              <div className="diff-list">
                {result.diffs.map((d, idx) => {
                  const isActive = idx === activeDiffIndex;
                  return (
                    <div
                      key={idx}
                      onClick={() => setActiveDiffIndex(idx)}
                      className={`diff-item ${isActive ? "active" : ""}`}
                      style={{ background: isActive ? `${colorMap[d.type]}22` : "transparent" }}
                    >
                      <strong style={{ color: colorMap[d.type] }}>
                        p.{d.page + 1} — {d.type.toUpperCase()}
                      </strong>
                      <div>{d.description}</div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Right: Chat Interface */}
        <div className="chat-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0 }}>DocDiff Assistant 🤖</h3>
            {chatMessages.length > 0 && (
              <button
                onClick={clearChat}
                style={{ padding: '6px 12px', background: '#ef4444', fontSize: '14px' }}
                title="Clear chat history"
              >
                Clear Chat
              </button>
            )}
          </div>
          <div className="chat-box">
            {chatMessages.map((m, i) => (
              <div key={i} className={`chat-message ${m.sender}`}>
                {m.text}
              </div>
            ))}
            {chatLoading && <div className="chat-message bot">Thinking…</div>}
          </div>
          <div className="chat-input-bar">
            <input
              type="text"
              placeholder="Ask about the differences..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && chatInput.trim()) {
                  askQuestion(chatInput);
                  setChatInput("");
                }
              }}
            />
            <button
              onClick={() => {
                if (chatInput.trim()) {
                  askQuestion(chatInput);
                  setChatInput("");
                }
              }}
              disabled={!chatInput || chatLoading}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
