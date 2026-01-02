import React, { useState } from "react";
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
  const [beforeFile, setBeforeFile] = useState<File | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiffIndex, setActiveDiffIndex] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const onCompare = async () => {
  if (!beforeFile || !afterFile) return;
  setLoading(true);
  setError(null);
  setResult(null);
  setActiveDiffIndex(null);

  try {
    const form = new FormData();
    form.append("before_file", beforeFile);
    form.append("after_file", afterFile);

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
  if (!diffs) return;
  setChatLoading(true);
  setChatMessages((prev) => [...prev, { sender: "user", text: question }]);

  try {
    const form = new FormData();
    form.append("question", question);
    form.append("diffs", JSON.stringify(diffs));

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
              <h3>Detected Differences</h3>
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
          <h3>DocDiff Assistant 🤖</h3>
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
              onKeyDown={(e) => e.key === "Enter" && askQuestion(chatInput)}
            />
            <button onClick={() => askQuestion(chatInput)} disabled={!chatInput || chatLoading}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
